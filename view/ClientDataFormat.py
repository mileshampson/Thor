from thor.view import HexCoordSys

class TileEventProcessor(object):
    def __init__(self, targetType, session):
        self.targetType = targetType
        self.session = session
        self.incomingEventQueue = self.session.getUnreadDataQueue()

    """ Mixin allowing a class to receive an external event encoding as an add or remove method call """
    def processAnyNewData(self):
        # Not sure if python supports non-blocking queue iteration, so do this as a while
        event = self.incomingEventQueue.get(block=False)
        while (event is not None):
            data = event.get("data")
            id = event["id"]
            # TODO handle multiple moves
            if event["type"] == "Remove" or event["type"] == "Move":
                data = self.remove(id)
            if event["type"] == "Add" or event["type"] == "Move":
                tilePosition = HexCoordSys.getTilePosition(int(event["tilePosition"][0]), int(event["tilePosition"][1]))
                self.add(id, tilePosition, data)
            event = self.incomingEventQueue.get(block=False)

    def createRemoveEvent(self, id):
        self.session.addDataToSend(**{'type':'Remove', 'target':self.targetType, 'id':str(id)})

    def createMoveEvent(self, id, toPosition):
        self.session.addDataToSend(**{'type':'Move', 'target':self.targetType, 'id':str(id), 'tilePosition':toPosition})

    def createAddEvent(self, id, toPosition):
        self.session.addDataToSend(**{'type':'Add', 'target':self.targetType, 'id':str(id), 'tilePosition':toPosition})

import ConfigParser
class ConfigReader(object):
    configParser = ConfigParser.RawConfigParser()
    configParser.read('client.config')
    @classmethod
    def getColourForId(cls, colourid):
        colour = cls.configParser.get('colours', colourid)
        splitColour = colour.split(',')
        red, green, blue, alpha = [int(c) for c in splitColour]
        return (red, green, blue, alpha)