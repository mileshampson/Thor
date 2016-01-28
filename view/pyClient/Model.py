# Models represent data that can be shared between controllers
from thor.view.ClientDataFormat import ConfigReader
from thor.view.pyClient.View import PieceView

class SelectionModel:
    def __init__(self):
        self.PrimarySelection = None
        self.extendedSelection = set()

    def setPrimarySelection(self, tilePosition):
        self.PrimarySelection = tilePosition

    def getPrimarySelection(self):
        return self.PrimarySelection

    def clearPrimarySelection(self):
        oldSelection = self.PrimarySelection
        self.PrimarySelection = None
        return oldSelection

    def isPrimarySelectionSet(self):
        return self.PrimarySelection is not None

    def extendSelection(self, tilePosition):
        if tilePosition != self.getPrimarySelection():
            self.extendedSelection.add(tilePosition)
            return True
        return False

    def getExtendedSelection(self):
        return self.extendedSelection

    def reduceSelection(self, tilePosition):
        if self.doesExtendedSelectionContain(tilePosition):
            self.extendedSelection.remove(tilePosition)
            return True
        return False

    def doesExtendedSelectionContain(self, tilePosition):
        return tilePosition in self.extendedSelection

    def clearExtendedSelection(self):
        oldSelection = self.extendedSelection
        self.extendedSelection = set()
        return oldSelection

    def clearAllSelections(self):
        selections = self.clearExtendedSelection()
        selections.add(self.clearPrimarySelection())
        return selections

class BoardTileModel:
    def __init__(self):
        self.idToTile = dict()

    def addTilePositionWithId(self, id, tilePosition):
        if self.idToTile.get(id) is None:
            self.idToTile[id] = tilePosition
            return tilePosition
        return None

    def removeTilePositionWithId(self, id):
        tilePosition = self.idToTile.get(id)
        if tilePosition is not None:
            del self.idToTile[id]
        return tilePosition

    def containsId(self, id):
        return id in self.idToTile.keys()

    def containsTile(self, id):
        return id in self.idToTile.values()

    def positionsOnBoardIn(self, tilePositions):
        return set(filter(lambda posn: self.containsTile(posn), tilePositions))

class BoardPiecesModel:
    def __init__(self):
        self.idToData = dict()

    def addPieceWithId(self, id, data):
        if self.idToData.get(id) is None:
            self.idToData[id] = data
            return data
        return None

    def isPieceAt(self, tilePosition):
        return len(self.getDataForPiecesAt(tilePosition)) > 0

    def containsId(self, id):
        return id in self.idToData.values()

    def getDataForPiecesAt(self, tilePosition):
        return [data for data in self.idToData.values() if data.location == tilePosition]

    def getIdForPiecesAt(self, tilePosition):
        return [id for id in self.idToData.keys() if self.idToData[id].location == tilePosition]

    def removePieceWithId(self, id):
        data = self.idToData.get(id)
        if data is not None:
            del self.idToData[id]
        return data

    def removeAllPieces(self):
        pieceValuesRemoved = list()
        for id in self.idToData.keys():
            pieceValuesRemoved.append(self.removePieceWithId(id))
        return pieceValuesRemoved

class PieceDataModel:
    def __init__(self, location, team):
        self.colour = ConfigReader.getColourForId(team)
        self.view = PieceView(self.colour, (location,))
        self.location = location
        self.moves = 2
        self.moveColour = ConfigReader.getColourForId(team+"Moving")
        self.team = team