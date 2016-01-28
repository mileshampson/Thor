import math
import pygame
import pygame.gfxdraw
from pygame.locals import *
from thor.view.ClientDataFormat import ConfigReader
from thor.view import HexCoordSys

# TODO should be in config or from pygame.display.Info().current_w current_h
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
CENTER = HexCoordSys.ScreenCoordinate(x=WINDOW_WIDTH/2, y=WINDOW_HEIGHT/2)
# TODO could be scaled from window width/heigh div num tiles
TILE_EDGE_LENGTH = 20
TILE_HEIGHT = TILE_EDGE_LENGTH * 2
TILE_WIDTH = math.sqrt(3)/2 * TILE_HEIGHT

class CommonIdentity(object):
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash(self.__dict__)

class ScreenView():
    def __init__(self):
        pygame.init()
        # Create the display surface
        print pygame.display.Info()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 1)
        pygame.display.set_caption('Title')
        self.drawOn = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), 1)
        self.cursor = CursorView()

    def getSurface(self):
        return self.drawOn

    def clearSurface(self):
        self.drawOn.fill(ConfigReader.getColourForId('LIGHT_GREY'))

    def draw(self):
        # Put the current display surface onto the screen object
        self.screen.blit(self.drawOn, (0, 0))
        # Draw the cursor to the screen object
        self.cursor.draw(self.screen)
        # Push the screen to the display buffer
        pygame.display.flip()

class TileView(CommonIdentity):
    def __init__(self, tilePosition):
        self.surface = pygame.image.load("./hextile.png").convert()
        self.surface.set_colorkey(ConfigReader.getColourForId('TRANSPARENT_COLOR_KEY'), RLEACCEL)
        self.boundingBox = self.surface.get_rect()
        self.boundingBox.center = HexCoordSys.hexToPixel(tilePosition, TILE_EDGE_LENGTH, CENTER)
        self.views = []
        self.addView(TextView("%d,%d" % (tilePosition.row, tilePosition.col)))
        self.tilePosition = tilePosition

    def addView(self, view):
        view.setPosition(self.boundingBox.topleft[0], self.boundingBox.topleft[1])
        self.views.append(view)

    def getTilePosition(self):
        return self.tilePosition

    def draw(self, drawOnto):
        drawOnto.blit(self.surface, self.boundingBox.topleft)
        for view in self.views:
            view.draw(drawOnto)

class TextView:
    def __init__(self, text):
        self.surface = pygame.font.Font(pygame.font.get_default_font(),12).render(text, 0, ConfigReader.getColourForId('WHITE'))
        self.boundingBox = self.surface.get_rect()
        self.setPosition(0,0)

    def setPosition(self, screenX, screenY):
        """ Takes a position at the top left of a tile and moves this bounding box to it"""
        self.boundingBox.center = (screenX + (TILE_WIDTH/2), screenY + (TILE_HEIGHT/2))

    def draw(self, drawOnto):
        drawOnto.blit(self.surface, self.boundingBox.topleft)

class CursorView(object):
    def __init__(self):
        self.surface = pygame.image.load("./hexcursor.png").convert()
        self.surface.set_colorkey(ConfigReader.getColourForId('TRANSPARENT_COLOR_KEY'), RLEACCEL)
        self.boundingBox = self.surface.get_rect()
        self.tilePosUnderCursor = None
        self.setPosition(0,0)

    def setPosition(self, screenX, screenY):
        """ Translates position into position at top left of nearest tile. Does not work if position is already at top left """
        self.tilePosUnderCursor = HexCoordSys.pixelToHex(HexCoordSys.ScreenCoordinate(screenX, screenY), TILE_EDGE_LENGTH, CENTER)
        self.boundingBox.center = HexCoordSys.hexToPixel(self.tilePosUnderCursor, TILE_EDGE_LENGTH, CENTER)

    def getTilePosition(self):
        """ Note that this may not correspond to a tile on the board"""
        return self.tilePosUnderCursor

    def draw(self, drawOnto):
        drawOnto.blit(self.surface, self.boundingBox.topleft)

class OverlayView(object):
    def __init__(self, tilePositions, colour):
        self.colour = colour
        for tilePosition in tilePositions:
            center = HexCoordSys.hexToPixel(tilePosition, TILE_EDGE_LENGTH, CENTER)
            self.vertices = list()
            for i in range(0,6):
                angle = (2 * math.pi / 6) * (i + 0.5)
                x_i = center.x + TILE_EDGE_LENGTH * math.cos(angle)
                y_i = center.y + TILE_EDGE_LENGTH * math.sin(angle)
                self.vertices.append((x_i, y_i))

    def draw(self, drawOnto):
        pygame.gfxdraw.filled_polygon(drawOnto, self.vertices, self.colour)

class PieceView(CommonIdentity):
    def __init__(self, colour, tilePositions):
        self.positions = set()
        for tilePosition in tilePositions:
            self.positions.add(HexCoordSys.hexToPixel(tilePosition, TILE_EDGE_LENGTH, CENTER))
        self.colour = colour
        self.radius = int(TILE_EDGE_LENGTH / 2.0)

    def draw(self, drawOnto):
        for position in self.positions:
            pygame.gfxdraw.filled_circle(drawOnto, position.x, position.y, self.radius, self.colour)