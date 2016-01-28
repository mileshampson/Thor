import logging, sys, uuid
from collections import defaultdict

from thor.view import HexCoordSys
from thor.view.HexCoordSys import TilePosition
from graeae.Session import ClientSession


class Board:
    def __init__(self, edgeLength):
        self.radius = edgeLength - 1
        self.diameter = 2 * self.radius
        self.numTilesHigh = self.diameter + 1
        self.numTilesWide = self.diameter + 1
        print "Creating board", self.numTilesWide, "tiles wide and", self.numTilesHigh, "tiles high"
        # Initialise the tiles with their position in the axial coordinate system used to define locations on the board
        self.tilePositions = HexCoordSys.getPositionsDefinedByHexWithEdge(edgeLength)
        self.numTiles = len(self.tilePositions)
        print "Created a board containing", self.numTiles, "tiles"
        self.borders = defaultdict(list)
        for tilePosition in self.tilePositions:
            for key in HexCoordSys.borders.keys():
                if HexCoordSys.borders[key](tilePosition, self.tilePositions):
                    self.borders[key].append(tilePosition)
        self.center = TilePosition(row=0, col=0)
        self.spokes = defaultdict(list)
        for key in HexCoordSys.edgeDirections.keys():
            curTile = self.center
            while self.isOnBoard(curTile):
                self.spokes[key].append(curTile)
                curTile = HexCoordSys.edgeDirections[key](curTile)

    def isOnBoard(self, tilePosition):
        return tilePosition in self.tilePositions

if __name__ == '__main__':
    if len(sys.argv) > 0:
        logging.basicConfig(level=logging.INFO)
        session = ClientSession()
        board = Board(int(sys.argv[1].strip()))
        for tilePosition in board.tilePositions:
            session.addDataToSend(({'type': 'Add', 'target': 'Tile', 'id': str(uuid.uuid4()),
                                    'tilePosition': (tilePosition.row, tilePosition.col)},))
# with open('server.config') as config_file:
#     forServer.queueNewDataForAll(json.load(config_file)["startCommands"])

# TODO configurable board to allow other settings i.e. 7 adjacent hexes

# t = threading.Thread(target=readUser, args = (server,int(sys.argv[1].strip())))
#         t.daemon = True
#         t.start()

# def readUser(fromServer, edgeLength):
#     while True:
#          #TODO use input() rather than raw_input to allow entry of types
#         line = raw_input('Enter a new command\n')
#         if (" "  in line):
#             pass



