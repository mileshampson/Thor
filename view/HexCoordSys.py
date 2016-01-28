import math, logging
from collections import namedtuple

TileCubePosition = namedtuple("TileCubePosition", "x y z")
def getCubePosOf(tilePosition):
    return TileCubePosition(x=tilePosition.col, y=-tilePosition.col-tilePosition.row, z=tilePosition.row)
# This TilePosition is a two coordinate representation of TileCubePosition which is easier to work with
# Each TileCubePosition has a canonical position in this system as we map row=z, col=x, and for every
# position with one of those varying the y value must also vary and can be obtained from the relation 0 = x + y + z
class TilePosition(namedtuple("TilePosition", "row col")):
    __slots__ = ()
    def __add__(self, other):
        return TilePosition(row=self.row + other.row, col=self.col + other.col)
    def __sub__(self, other):
        return TilePosition(row=self.row - other.row, col=self.col - other.col)
    def __mul__(self, other):
        # Multiplication is only defined for scalar values
        if type(other) is TilePosition:
            return self
        return TilePosition(row=self.row * other, col=self.col * other).roundPosn()
    __rmul__ = __mul__
    def roundPosn(self):
        """ Round each component of the tile position to the nearest int that is a valid tile on the board """
        x, y, z = getCubePosOf(self)
        rx = round(x)
        ry = round(y)
        rz = round(z)
        x_diff = abs(rx - x)
        y_diff = abs(ry - y)
        z_diff = abs(rz - z)
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry-rz
        elif y_diff <= z_diff:
            rz = -rx-ry
        # Add 0 to remove negative zero for display purposes. rx and rz are now integers
        return TilePosition(col=int(rx + 0), row=int(rz + 0))

# The internal definition of a tile pos
def getTilePosition(row, col):
    return TilePosition(row=row, col=col)
# Define a frame of reference for movements between tiles, mapping compass directions to a function that
# transforms a tile position into the neighbouring tile position in that direction.
edgeDirections={"NE": (lambda tilePos: TilePosition(row=tilePos.row - 1, col=tilePos.col + 1)),
                "E": (lambda tilePos: TilePosition(row=tilePos.row, col=tilePos.col + 1)),
                "SE": (lambda tilePos: TilePosition(row=tilePos.row + 1, col=tilePos.col)),
                "SW": (lambda tilePos: TilePosition(row=tilePos.row + 1, col=tilePos.col - 1)),
                "W": (lambda tilePos: TilePosition(row=tilePos.row, col=tilePos.col - 1)),
                "NW": (lambda tilePos: TilePosition(row=tilePos.row - 1, col=tilePos.col))}
diagonalDirections={"N": (lambda tilePos: TilePosition(row=tilePos.row - 2, col=tilePos.col + 1)),
                    "ENE": (lambda tilePos: TilePosition(row=tilePos.row - 1, col=tilePos.col + 2)),
                    "ESE": (lambda tilePos: TilePosition(row=tilePos.row + 1, col=tilePos.col + 1)),
                    "S": (lambda tilePos: TilePosition(row=tilePos.row + 2, col=tilePos.col - 1)),
                    "WSW": (lambda tilePos: TilePosition(row=tilePos.row + 1, col=tilePos.col - 2)),
                    "WNW": (lambda tilePos: TilePosition(row=tilePos.row - 1, col=tilePos.col - 1))}
allDirections = dict(edgeDirections.items() + diagonalDirections.items())
borders={"NE": (lambda tilePos, posns: edgeDirections["NE"](tilePos) not in posns
                                   and edgeDirections["E"](tilePos) not in posns),
         "SE": (lambda tilePos, posns: edgeDirections["E"](tilePos) not in posns
                                   and edgeDirections["SE"](tilePos) not in posns),
         "S": (lambda tilePos, posns: edgeDirections["SE"](tilePos) not in posns
                                  and edgeDirections["SW"](tilePos) not in posns),
         "SW": (lambda tilePos, posns: edgeDirections["SW"](tilePos) not in posns
                                   and edgeDirections["W"](tilePos) not in posns),
         "NW": (lambda tilePos, posns: edgeDirections["W"](tilePos) not in posns
                                   and edgeDirections["NW"](tilePos) not in posns),
         "N": (lambda tilePos, posns: edgeDirections["NW"](tilePos) not in posns
                                   and edgeDirections["NE"](tilePos) not in posns)}

# --------------------------- TilePosition comparison functions --------------------------------------------
def distanceBetween(tilePos1, tilePos2):
    """ The rectilinear distance between the two points, which is always an integer value in our coordinate system """
    return int(round((math.fabs(tilePos1.col - tilePos2.col) + math.fabs(tilePos1.row - tilePos2.row) +
                      math.fabs(tilePos1.col + tilePos1.row - tilePos2.col - tilePos2.row)) / 2.0))

def getShortestTilePathBetween(tilePos1, tilePos2):
#     N = hex_distance(A, B)
# for each 0 lte i lte N:
#     draw hex at hex_round(A * (1 - i/N) + B * i/N)

# rewriting A * (1 - i/N) + B * i/N as A + (B - A) * i/N, then precalculating (B - A) and 1.0/N.
    lengthF = float(distanceBetween(tilePos1, tilePos2))
    if lengthF < 2:
        return [tilePos1, tilePos2]
    posns = []
    ratioFactor = 1.0/lengthF
    diffFactor = tilePos2 - tilePos1
    for i in range(int(lengthF + 1)):
        # * and +/- are defined in the TilePosition class
        posns.append(tilePos1 + (diffFactor * i) * ratioFactor)
    logging.debug("Shortest path between %s and %s is %s", tilePos1, tilePos2, posns)
    return posns

# --------------------------- TilePosition grouping functions --------------------------------------------
def getPositionsDefinedByHexWithEdge(edgeLength):
    radius = edgeLength - 1
    return getPositionsDefinedByHexWithRowRange(-radius, radius)

def getPositionsDefinedByHexWithRowRange(lowestRow, highestRow):
    # Add 1 to the end indices to include highestRow and the generated highest col, as range function excludes end point
    return set(TilePosition(row=r, col=q) for r in range(lowestRow, highestRow + 1)
                                          for q in range(lowestRow - min(0,r), highestRow - max(0, r) + 1))
    # Alt use a 2d array, but then would need to shift the negative values
    #return [[TilePosition(row=r, col=q) for q in range(lowestRow - min(0,r), highestRow - max(0, r))]
    #                                    for r in range(lowestRow, highestRow)]
def getTilesWithin(distance, ofTilePosition):
    matchingTiles = set()
    for deltaX in range(-distance, distance + 1):
        startX = max(-distance, -deltaX - distance)
        endX = min(distance, -deltaX + distance)
        for deltaY in range(startX, endX + 1):
            deltaZ = -deltaX - deltaY
            matchingTiles.add(ofTilePosition + TilePosition(row=deltaX, col=deltaZ))
    logging.debug("Tiles within %s of %s are %s", distance, ofTilePosition, matchingTiles)
    return matchingTiles

# ------------------------ Pixel conversion functions -----------------------------------------------------
ScreenCoordinate = namedtuple("ScreenCoordinate", "x y")
#TODO pixel functions would be clearer and more efficient if written as matrix operations and run in numpy
def hexToPixel(tilePosition, hexEdgeLength, centerPixel):
    x = round(hexEdgeLength * math.sqrt(3) * (tilePosition.col + tilePosition.row/2.0))
    y = round(hexEdgeLength * 3/2.0 * tilePosition.row)
    # This will be centered around 0,0, need to shift it to center around the specified center
    return ScreenCoordinate(x=int(centerPixel.x + x), y=int(centerPixel.y + y))

def pixelToHex(screenCoordinate, hexEdgeLength, centerPixel):
    # This will be centered around centerPixel, need to shift it to center around 0,0
    x = screenCoordinate.x - centerPixel.x
    y = screenCoordinate.y - centerPixel.y
    # Need to use roundPosition() to translate this to a valid hex
    return TilePosition(row=2/3.0 * y / float(hexEdgeLength),
                        col=(1/3.0 * math.sqrt(3) * x - 1/3.0 * y) / float(hexEdgeLength)).roundPosn()