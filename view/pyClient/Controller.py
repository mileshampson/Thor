import logging
from collections import defaultdict

import pygame
from pygame import QUIT, KEYDOWN, K_ESCAPE, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP

from thor.view import HexCoordSys

from thor.view.pyClient.Model import SelectionModel, BoardTileModel, BoardPiecesModel, PieceDataModel
from thor.view.pyClient.View import ScreenView, TileView, OverlayView, PieceView
from thor.view.ClientDataFormat import ConfigReader, TileEventProcessor
from graeae.Session import ClientSession

class ScreenController:
    """ Manages a ScreenView and controllers for other views on the screen """
    def __init__(self):
        self.screenView = ScreenView()
        self.controllers = list()
        self.running = True
        self.mouseDragButton = None
        self.lastTileOverPosition = HexCoordSys.getTilePosition(0, 0)
        self.session = ClientSession()
        self.controllers.append(TileController("Tile", self.session))
        self.controllers.append(PieceController("Piece", self.session, self.controllers["Tile"].tilePositionModel))
        self.mainLoop()

    def mainLoop(self):
        logging.info("Starting main client loop")
        clock = pygame.time.Clock()
        while self.running:
            # Limit to 10 loops a second. The rendering code is quick so this avoids excess CPU utilization.
            clock.tick(10)
            for ctrl in self.controllers:
                ctrl.processAnyNewData()
            for event in pygame.event.get():
                self.processUpdate(event)
            # Clear screen and redraw everything every loop to avoid logic for passing display.update dirty rects
            self.screenView.clearSurface()
            for controller in self.controllers:
                controller.draw(self.screenView.getSurface())
            self.screenView.draw()

    def processUpdate(self, event):
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            self.running = False
        elif event.type == MOUSEMOTION:
            self.screenView.cursor.setPosition(event.pos[0],event.pos[1])
            oldTilePosition = self.lastTileOverPosition
            self.lastTileOverPosition = self.screenView.cursor.getTilePosition()
            # Drag Right/Info click to a new tile
            if self.mouseDragButton is 3 and oldTilePosition != self.lastTileOverPosition:
                self.controllers["Piece"].trialMoveSelectedEvent(self.lastTileOverPosition)
        elif event.type == MOUSEBUTTONDOWN:
            self.mouseDragButton = event.button
            if event.button == 1: # Left/action click
                self.controllers["Piece"].selectEvent(self.lastTileOverPosition)
        elif event.type == MOUSEBUTTONUP:
            if self.mouseDragButton is 3: # Release Right/Info click
                self.controllers["Piece"].moveSelectedEvent(self.lastTileOverPosition)
                self.controllers["Piece"].selectEvent(self.lastTileOverPosition)
                self.mouseDragButton = None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ScreenController()
    print "Exiting client session"

class TileController(TileEventProcessor):
    """ Manages the display of board tiles for the ScreenController """
    def __init__(self, eventId, session):
        super(TileController, self).__init__(eventId, session)
        self.tileViews = []
        self.tilePositionModel = BoardTileModel()

    def remove(self, id):
        tilePositionRemoved = self.tilePositionModel.removeTilePositionWithId(id)
        if tilePositionRemoved is not None:
            self.tileViews.remove(TileView(tilePositionRemoved))

    def add(self, id, tilePosition, data):
        if self.tilePositionModel.addTilePositionWithId(id, tilePosition) is not None:
            self.tileViews.append(TileView(tilePosition))

    def draw(self, drawOnto):
        for tileView in self.tileViews:
            tileView.draw(drawOnto)

class SelectionController:
    """ Manages the display of user selections for the ScreenController """
    def __init__(self):
        self.selectionViews = defaultdict(dict)

    def setSelectedTile(self, tilePosition, selectionKey=None, colour=None):
        logging.debug("Changing primary selection for model %s from %s to %s", selectionKey,
                      selectionKey.getPrimarySelection if selectionKey is not None else "None", tilePosition)
        if selectionKey is None:
            selectionKey = SelectionModel()
        selectionKey.setPrimarySelection(tilePosition)
        if colour is not None:
            self.selectionViews[selectionKey][tilePosition] = (OverlayView((tilePosition,), colour))
        return selectionKey

    def setInfoTiles(self, newSelections, selectionKey, colour, viewTypeToUse):
        logging.debug("Changing info selection for model %s from %s to %s", selectionKey,
                      selectionKey.getExtendedSelection(), newSelections)
        # Go through each of the current extended selections and remove any not in the new selection
        for noLongerSelected in selectionKey.getExtendedSelection() - newSelections:
            if selectionKey.reduceSelection(noLongerSelected):
                del self.selectionViews[selectionKey][noLongerSelected]
        # For each position that is on the board and not already selected, select it
        for newSelection in newSelections - selectionKey.getExtendedSelection():
            if selectionKey.extendSelection(newSelection):
                self.selectionViews[selectionKey][newSelection] = viewTypeToUse((newSelection,), colour)

    def clearAllSelection(self, selectionKey):
        if selectionKey is not None:
            tilePosition = selectionKey.clearPrimarySelection()
            if tilePosition in self.selectionViews[selectionKey]:
                logging.debug("Clearing primary selection %s for model %s", tilePosition, selectionKey)
                del self.selectionViews[selectionKey][tilePosition]
            for selectedPos in selectionKey.clearExtendedSelection():
                if selectedPos in self.selectionViews[selectionKey]:
                    del self.selectionViews[selectionKey][selectedPos]
            del self.selectionViews[selectionKey]

    def draw(self, drawOnto):
        for selectModels in self.selectionViews.values():
            for selectedView in selectModels.values():
                selectedView.draw(drawOnto)

class PieceController(TileEventProcessor):
    """ Manages the display of pieces on the board for the ScreenController """
    def __init__(self, eventId, session, tilePositionModel):
        super(PieceController, self).__init__(eventId, session)
        self.pieceViews = []
        self.selectionController = SelectionController()
        self.moveSelectionsModel = None
        self.pathSelectionModel = None
        self.piecesModel = BoardPiecesModel()
        self.tilePositionModel = tilePositionModel

    def remove(self, id):
        data = self.piecesModel.removePieceWithId(id)
        self.pieceViews.remove(data.view)
        if self.moveSelectionsModel is not None and \
                       data.location == self.moveSelectionsModel.getPrimarySelection():
            self.clearSelectEvent()
        return data.team

    def add(self, id, tilePosition, team):
        if not self.piecesModel.containsId(id):
            dm = PieceDataModel(tilePosition, team)
            self.piecesModel.addPieceWithId(id, dm)
            self.pieceViews.append(dm.view)

    def draw(self, drawSurface):
        for pieceView in self.pieceViews:
            pieceView.draw(drawSurface)
        self.selectionController.draw(drawSurface)

    def selectEvent(self, tilePosition):
        self.clearSelectEvent()
        if self.piecesModel.isPieceAt(tilePosition):
            logging.debug("Select event for %s", tilePosition)
            pieceData = self.piecesModel.getDataForPiecesAt(tilePosition)[0]
            self.moveSelectionsModel = self.selectionController.setSelectedTile(tilePosition, colour=ConfigReader.getColourForId('SelectedTile'))
            self.selectionController.setInfoTiles(self.tilePositionModel.positionsOnBoardIn(
                HexCoordSys.getTilesWithin(pieceData.moves, tilePosition)),
                self.moveSelectionsModel, ConfigReader.getColourForId('Info1Tile'), type(OverlayView((),())))
            self.pathSelectionModel = self.selectionController.setSelectedTile(tilePosition)

    def clearSelectEvent(self):
        logging.debug("Clear select event")
        self.selectionController.clearAllSelection(self.moveSelectionsModel)
        self.moveSelectionsModel = None
        self.selectionController.clearAllSelection(self.pathSelectionModel)
        self.pathSelectionModel = None

    def trialMoveSelectedEvent(self, tilePosition):
        # If a tile has been selected for the start of the path, and the specified path tile is on the board
        if self.pathSelectionModel is not None and self.tilePositionModel.contains(tilePosition) and not \
                self.pathSelectionModel.doesExtendedSelectionContain(tilePosition):
            logging.debug("Trial move to %s", tilePosition)
            pieceData = self.piecesModel.getDataForPiecesAt(self.pathSelectionModel.getPrimarySelection())[0]
            self.selectionController.setInfoTiles(self.tilePositionModel.positionsOnBoardIn(
                HexCoordSys.getShortestTilePathBetween(self.pathSelectionModel.getPrimarySelection(), tilePosition)),
                self.pathSelectionModel, pieceData.movingColour, type(PieceView((),())))

    def moveSelectedEvent(self, tilePosition):
        if self.moveSelectionsModel is not None and self.tilePositionModel.containsTile(tilePosition):
            logging.debug("Move event to %s", tilePosition)
            team = None
            id = None
            for id in self.piecesModel.getIdForPiecesAt(self.moveSelectionsModel.getPrimarySelection()):
                team = self.remove(id)
                id = id
            self.add(id, tilePosition, team)
            self.createMoveEvent(id, tilePosition)