#    bitmaps.py - Replaces contents of various arcade artwork ROMs with data from converted bitmaps
#    Copyright (C) 2016 Stephen Wylie

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published 
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.

#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

tileAddrScale = 16    # if you choose to divide the tile addresses in the tile file by a factor, put that factor here
tileHeightPx = 8      # height of a tile in pixels
tileWidthPx = 8       # width of a tile in pixels
tileAddresses = []
prevTileAddressCount = 0

# The tile file should contain comma-separated tile addresses, and
# must have as many tiles called out as (pixels/8) in each direction,
# e.g. 96*32 image will have 4 lines with 12 tile addresses each
#
# Note: It's OK to not put an address for a given 8x8 square.
# That just means that part of the BMP won't be put into the ROM.
# This is useful for when you have repeated blocks of color or
# other graphics hacks you intend to do there like mirrors/rotations.
with open('tilefile.txt') as fp:
    lineNum = 0
    for line in fp:
        lineNum += 1
        tileAddrsRow = line.strip().split(",")
        if (len(tileAddrsRow) == 0):
			# TODO NOTE: It's OK if you see the following error message if you made comments at the bottom of the file.
            print("Empty line read in tile file at line", lineNum)
            break
        if (len(tileAddrsRow) != prevTileAddressCount and prevTileAddressCount != 0):
			# TODO NOTE: It's OK if you see the following error message if you made comments at the bottom of the file.
            print("Error: Tile file does not have a consistent number of tile addresses per row.")
            print("Line", (lineNum - 1), "has", prevTileAddressCount, "tile addresses; line", lineNum, "has", len(tileAddrsRow), "tile addressses.")
            sys.exit()
        prevTileAddressCount = len(tileAddrsRow)
        tileAddresses.append(tileAddrsRow)

# Convert the file data into a 2D matrix of integers consisting of the tile addresses
for i in range(0, len(tileAddresses)):
    for j in range(0, len(tileAddresses[i])):
        if (tileAddresses[i][j] != ""):
            tileAddresses[i][j] = int(tileAddresses[i][j], 16)
print(tileAddresses)

# This is where you make reference to colors in an 8-bit BMP file.
# As the Bally MCR-3 embeds 16 colors in groups of 4, refer to
# the 0-255 color index, then the group index 0-3, then the
# color index 0-3, each comma-separated.
colors = {}
with open('colorfile.txt') as fp:
    for line in fp:
        row = line.strip().split(",")
        if (len(row) != 3):
            print("Error: Color file must have three values per row - the original pixel value, the palette, and the color index.")
            break
        colors[int(row[0], 16)] = (int(row[1]), int(row[2]))
print(colors)

# Open the bitmap and skip to the width & height section.
f = open("stevo.bmp", "rb")
f.seek(18)
width = 0
# Read in the bitmap width and height from the header.
for i in range(0, 4):
    wByte = ord(f.read(1))
    width += wByte * (16 ** i)
height = 0
for i in range(0, 4):
    hByte = ord(f.read(1))
    height += hByte * (16 ** i)
print("Width:", width, ", Height:", height)

if (len(tileAddresses) * tileHeightPx != height):
    print("WARNING: The number of rows in the tile file does not match the height of the provided bitmap.")
if (len(tileAddresses[0]) * tileWidthPx != width):
    print("WARNING: The number of columns in the tile file does not match the width of the provided bitmap.")

# Skip over the rest of the header.
f.seek(1078)
lines = []
for i in range(0, height):
    lines.extend(f.read(width))
f.close()

# Here's where the magic happens!
# Don't forget to substitute the path to your graphics ROMs down below near the end
paletteTiles = []
colorTiles = []
tileCount = int(width * height / (tileHeightPx * tileWidthPx))
rows = int(width / tileHeightPx)
for i in range(0, tileCount):
    paletteTile = []
    colorTile = []
    for rIdx in range(0, tileHeightPx):
        rowMultiplier = int(i / rows)
        row = height - 1 - (rIdx + (8 * rowMultiplier))
        newPaletteValue = 0
        newColorValue = 0
        for cIdx in range(0, tileWidthPx):
            col = cIdx + int(8 * (i % rows))
            pixel = (row * width) + col
            tempColorValue = 0
            tempPaletteValue = 0
            byteColor = lines[pixel]
            try:
                tempPaletteValue = colors[byteColor][0]
                tempColorValue = colors[byteColor][1]
            except KeyError:
                print("Unexpected color value:", byteColor)
            if (cIdx % 4 == 0):
                newPaletteValue = tempPaletteValue << 6
                newColorValue = tempColorValue << 6
            elif (cIdx % 4 == 3):
                #tile.append(format(newValue + tempValue, '02x'))  # plain-text output
                #paletteTile.append(chr(newPaletteValue + tempPaletteValue))  # char output
                #colorTile.append(chr(newColorValue + tempColorValue))  # char output
                paletteTile.append(newPaletteValue + tempPaletteValue)  # binary output
                colorTile.append(newColorValue + tempColorValue)  # binary output
            else:
                newPaletteValue += tempPaletteValue << ((3 - (cIdx % 4)) * 2)
                newColorValue += tempColorValue << ((3 - (cIdx % 4)) * 2)
    #tiles.append(tile)  # plain-text output
    #paletteTiles.append(("".join(paletteTile)))  # char output
    #colorTiles.append(("".join(colorTile)))  # char output
    paletteTiles.append(bytes(paletteTile))  # binary output
    colorTiles.append(bytes(colorTile))  # binary output

flatTileAddresses = [item for sublist in tileAddresses for item in sublist]
paletteTileFile = open("/path/to/bg0.bin", "rb+")
colorTileFile = open("/path/to/bg1.bin", "rb+")
for i in range(0, len(flatTileAddresses)):
    if (flatTileAddresses[i] != ""):
        paletteTileFile.seek(flatTileAddresses[i] * tileAddrScale)
        paletteTileFile.write(paletteTiles[i])
        colorTileFile.seek(flatTileAddresses[i] * tileAddrScale)
        colorTileFile.write(colorTiles[i])
paletteTileFile.close()
colorTileFile.close()