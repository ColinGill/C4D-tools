"""
Name-US:BO4 Import .mtl c4d...
Description-US:Run this script after importing an .obj file. It will parse the .mtl files and build the materials.


ImportMTL_C4d_CoD 1.1.1
===============
2018 by Colin


Description
-----------
This script reads a folder containing MTL files and builds / updates the materials with textures and basic(!) material
parameters as described in the Wikipedia article "Wavefront .obj file". Most of the work was done by www.c4d-jack.de.


Disclaimer
----------
This script is provided as is, no guarantee or warranty whatsoever. Use on your own risk.


Known bugs / problems
---------------------
Some of the information in the Wiki article is contradictory. E.g. it is stated that "d" and "Tr" both stand for "Transparency".
Some OBJ files, however, contain both keys with different values.

The "illumination models" as mentioned in the Wiki article are ignored. Maybe I didn't get it, but they seemed not to
make a lot of sense.


Updates from original script by www.c4d-jack.de.
---------
1/ Modified to accept .txt files as mtls for use with greyhound format
2/ interates through a folder of material files instead of previous singular file execution
3/ Updates normals, diffuse (occulsion), gloss, emissive ,and specular textures..

"""

import os
import c4d
from c4d import gui
from c4d import storage


ENABLE_DEBUG = False


MTL_KEYWORD_NEWMATERIAL = 'semantic,image_name'
MTL_KEYWORD_MAP = 'map_'


# Map possible MTL keywords to C4D constants
# Texture maps
MTL_KEYWORDS_MAP = {
                     'map_Ka' : c4d.MATERIAL_LUMINANCE_SHADER,
                     'colorMap' : c4d.MATERIAL_COLOR_SHADER,
                     'specColorMap' : c4d.MATERIAL_SPECULAR_SHADER,
                     'map_bump' : c4d.MATERIAL_BUMP_SHADER,
                     'normalMap' : c4d.MATERIAL_NORMAL_SHADER,
                     'aoMap' : c4d.MATERIAL_DIFFUSION_SHADER,
                     'emissiveMap' : c4d.MATERIAL_LUMINANCE_SHADER,
                     'glossMap' : c4d.MATERIAL_REFLECTION_SHADER,
                     'map_d' : c4d.MATERIAL_ALPHA_SHADER,

                   }

# Vectors
MTL_KEYWORDS_COLOR = {
                       'Ka' : c4d.MATERIAL_LUMINANCE_COLOR,
                       'Kd' : c4d.MATERIAL_COLOR_COLOR,
                       'Ks' : c4d.MATERIAL_SPECULAR_COLOR
                     }

# Floats
MTL_KEYWORDS_PROP = {
                       'Ns' : c4d.MATERIAL_SPECULAR_WIDTH,
                       'd' : c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS,
                       'Tr' : c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS
                     }

# Map C4D constants to strings
MTL_KEYWORDS_NAMES = {
                       c4d.MATERIAL_LUMINANCE_SHADER : 'luminance map',
                       c4d.MATERIAL_COLOR_SHADER : 'diffuse map',
                       c4d.MATERIAL_NORMAL_SHADER : 'normal map',
                       c4d.MATERIAL_ALPHA_SHADER : 'mask',
                       c4d.MATERIAL_BUMP_SHADER : 'bump map',
                       c4d.MATERIAL_SPECULAR_SHADER : 'specular map',
                       c4d.MATERIAL_DIFFUSION_SHADER : 'ambient map',
                       c4d.MATERIAL_REFLECTION_SHADER : 'reflection map',

                       c4d.MATERIAL_LUMINANCE_COLOR : 'ambient color',
                       c4d.MATERIAL_COLOR_COLOR : 'diffuse color',
                       c4d.MATERIAL_SPECULAR_COLOR : 'specular color',

                       c4d.MATERIAL_SPECULAR_WIDTH : 'specular coefficient',
                       c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS : 'transparency'
                     }

# Map C4D constants to multipliers
MTL_KEYWORDS_MUL = {
                     c4d.MATERIAL_LUMINANCE_COLOR : 1.0,
                     c4d.MATERIAL_COLOR_COLOR : 1.0,
                     c4d.MATERIAL_SPECULAR_COLOR : 1.0,

                     c4d.MATERIAL_SPECULAR_WIDTH : 0.01,
                     c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS : 1.0
                   }

# Map C4D constants to 'use channel' IDs
MTL_KEYWORDS_USE = {
                      c4d.MATERIAL_SPECULAR_SHADER :  c4d.MATERIAL_USE_SPECULARCOLOR,
                      c4d.MATERIAL_LUMINANCE_SHADER : c4d.MATERIAL_USE_LUMINANCE,
                      c4d.MATERIAL_COLOR_SHADER : c4d.MATERIAL_USE_COLOR,
                      c4d.MATERIAL_NORMAL_SHADER : c4d.MATERIAL_USE_NORMAL,
                      c4d.MATERIAL_ALPHA_SHADER : c4d.MATERIAL_USE_ALPHA,
                      c4d.MATERIAL_BUMP_SHADER : c4d.MATERIAL_USE_BUMP,
                      c4d.MATERIAL_DIFFUSION_SHADER : c4d.MATERIAL_USE_DIFFUSION,
                      c4d.MATERIAL_REFLECTION_SHADER : c4d.MATERIAL_USE_REFLECTION,

                      c4d.MATERIAL_LUMINANCE_COLOR : c4d.MATERIAL_USE_LUMINANCE,
                      c4d.MATERIAL_COLOR_COLOR : c4d.MATERIAL_USE_COLOR,
                      c4d.MATERIAL_SPECULAR_COLOR : c4d.MATERIAL_USE_SPECULAR,

                      c4d.MATERIAL_SPECULAR_WIDTH : c4d.MATERIAL_USE_SPECULAR,
                      c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS : c4d.MATERIAL_USE_TRANSPARENCY
                   }



# Print a string, if debug mode is enabled
def DebugPrint(s):
    if ENABLE_DEBUG:
        print s


# Get the path component from a path
def GetPath(path):
    head, tail = os.path.split(path)
    return head


# Set a material property
def SetMatProperty(matName, value, targetId, targetDoc):
    DebugPrint('  -> Inserting "' + str(value) + '" as "' + MTL_KEYWORDS_NAMES[targetId] + '" of material "' + matName + '".')
    mat = targetDoc.SearchMaterial(matName)

    # If material not found, create it
    if mat == None:
        mat = c4d.BaseMaterial(c4d.Mmaterial)
        mat.SetName(matName)
        targetDoc.InsertMaterial(mat)

    # Cancel if material could not be found or created
    if mat == None:
        DebugPrint('     ERROR: COULD NEITHER FIND NOR ALLOCATE TARGET MATERIAL!')
        return

    # Add undo
    targetDoc.AddUndo(c4d.UNDOTYPE_CHANGE, mat)

    # Set property
    mat[targetId] = value * MTL_KEYWORDS_MUL[targetId]

    # Activate channel
    mat[MTL_KEYWORDS_USE[targetId]] = True
    if targetId == c4d.MATERIAL_SPECULAR_WIDTH:
        if value == 0.0:
            mat[MTL_KEYWORDS_USE[targetId]] = False
            DebugPrint('Turning Spec off cuz 0 width')

    # Update material
    mat.Update(True, True)


# Insert a texture into a channel of a material in a document. Create material, if necessary.
def InsertTexture(fBase, fName, matName, targetId, targetDoc , flipNormalY):
    DebugPrint('  -> Inserting "' + fName + '" into channel "' + MTL_KEYWORDS_NAMES[targetId] + '" of material "' + matName + '".')
    mat = targetDoc.SearchMaterial(matName)
   
    # If material not found, create it
    if mat == None:
        mat = c4d.BaseMaterial(c4d.Mmaterial)
        mat.SetName(matName)
        targetDoc.AddUndo(c4d.UNDOTYPE_NEW, mat)
        targetDoc.InsertMaterial(mat)

    # Cancel if material could not be found or created
    if mat == None:
        DebugPrint('     ERROR: COULD NEITHER FIND NOR ALLOCATE TARGET MATERIAL!')
        return

    # Create a new bitmap shader, insert texture
    tShader = c4d.BaseShader(c4d.Xbitmap)
    if tShader == None:
        DebugPrint('     ERROR: COULD NOT ALLOCATE BITMAP SHADER!')
        return

    fSlash = '/'
    fPath = str(fBase) + str(fSlash) + str(fName)

    tShader[c4d.BITMAPSHADER_FILENAME] = fPath #

    # Add undo
    targetDoc.AddUndo(c4d.UNDOTYPE_CHANGE, mat)

    # Activate channel
    mat[MTL_KEYWORDS_USE[targetId]] = True

    # Insert texture into channel
    mat[targetId] = tShader

    # Insert shader into node tree
    mat.InsertShader(tShader)

    # Special cases
    if targetId == c4d.MATERIAL_ALPHA_SHADER:
        # If we set an alpha map and the format is PNG of TIFF, it's likely to have an alpha channel, so we switch off "Image Alpha"
        if fName.endswith(('.tif','.tiff','.png','.tga')):
            mat[c4d.MATERIAL_ALPHA_IMAGEALPHA] = False

    #flip normals if needed
    if flipNormalY == 1:
        mat[c4d.MATERIAL_NORMAL_REVERSEY] = True
       

    # Update material
    mat.Update(True, True)


# Iterate lines of .mtl file, extract data, insert data into document
def ParseFile(fName, targetDoc):
    print 'Parsing ' + fName + '...'

    # Veriables
    #basePath = GetPath(fName)
    basePath = os.path.abspath(fName)
    basePath = basePath + "\..\\_images"
    print 'PATH ' + basePath
    matName = ''
    matCount = 0
    mapCount = 0
    lineNr = 0

    fl = open(fName)

    targetDoc.StartUndo()

    # Iterate lines
    for ln in fl:
        lineNr += 1
        line = ln.strip()
        words = line.split(',')
        normalFlipY = 0

        # Empty line -> End of current material
        if line == '':
            matName = ''
            DebugPrint(' ')
            continue

        # Comment line
        if line.startswith('#'):
            continue

        # Check if line is the beginning of a new material
        elif line.startswith(MTL_KEYWORD_NEWMATERIAL):
            matName = fName[:-11]
            matCount += 1
            print '*****Line ' + str(lineNr) + ': Found new mat: ****** ' + matName
            continue

        # Check for maps
        elif words[0] in MTL_KEYWORDS_MAP:
            if matName == '':
                print ' PARSER ERROR (line ' + str(lineNr) + '): MAP ' + words[0] + ' OUTSIDE OF MATERIAL!'
                continue
            else:
                targetChannel = MTL_KEYWORDS_MAP[words[0]]
                mapName = words[1]
                mapCount += 1
                DebugPrint('  Found map ' + MTL_KEYWORDS_NAMES[MTL_KEYWORDS_MAP[words[0]]] + ': ' + words[1])
                if words[0] ==  'normalMap':
                    normalFlipY = 1
                    
                InsertTexture(basePath, mapName+'.png', matName , targetChannel, targetDoc , normalFlipY)

        # Check for colors
        elif words[0] in MTL_KEYWORDS_COLOR:
            color = c4d.Vector()
            if matName == '':
                print '  PARSER ERROR (line ' + str(lineNr) + '): COLOR OUTSIDE OF MATERIAL!'
                continue
            else:
                try:
                    targetId = MTL_KEYWORDS_COLOR[words[0]]
                    color = c4d.Vector(float(words[1]), float(words[2]), float(words[3]))
                    print'  Found ' + MTL_KEYWORDS_NAMES[targetId] + ': ' + str(color)
                    SetMatProperty(matName, color, targetId, targetDoc)
                except ValueError:
                    print '  PARSER ERROR (line ' + str(lineNr) + '): COLOR ' + words[0] + ' COULD NOT BE PARSED!'

        # Check for float values
        elif words[0] in MTL_KEYWORDS_PROP:
            if matName == '':
                print '  PARSER ERROR (line ' + str(lineNr) + '): PROPERTY ' + words[0] + ' OUTSIDE OF MATERIAL!'
                continue
            else:
                try:
                    targetId = MTL_KEYWORDS_PROP[words[0]]
                    value = float(words[-1])
                    print'  Found ' + MTL_KEYWORDS_NAMES[targetId] + ': ' + str(value)
                    SetMatProperty(matName, value, targetId, targetDoc)
                except ValueError:
                    print '  PARSER ERROR (line ' + str(lineNr) + '): PROPERTY COULD NOT BE PARSED!'

    targetDoc.EndUndo()
    print ' \nDone. Parsed ' + str(lineNr) + ' and found ' + str(matCount) + ' materials with ' + str(mapCount) + ' texture maps'
    fl.close()
    c4d.EventAdd()


def main():

    fn = ''
    fn = storage.LoadDialog(c4d.FILESELECTTYPE_ANYTHING, 'Open .mtl file', c4d.FILESELECT_LOAD, 'mtl')
    directory = fn + "/.."
    print 'fn = ' + fn
    dirList = os.listdir(directory)

    for file in dirList:
        if file != None and file != ''and file.endswith(".txt"):

             ParseFile(file.decode("utf8"), doc)
             #ParseFile(fn.decode("utf8"), doc)
            #DebugPrint(' ')


if __name__=='__main__':
     main()