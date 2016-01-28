import sys, logging, socket, time, threading, json, uuid
from Session import Session, ServerSession

class Server:
    def __init__(self):
        self.session = ServerSession()
        self.clientSessions = dict()
        self.running = True

    def acceptConnectionLoop(self):
        while self.running:
            data = self.session.getUnreadDataQueue()
            newConnectionSocket, newConnectionUid = data.get() # Blocking call
            logging.info('Connection from new client %s', newConnectionUid)
            # Replace any existing session with this uid
            self.clientSessions[newConnectionUid] = Session(newConnectionSocket)
        logging.info("Stopping server listening")

    # TODO this would be better implemented as a coroutine
    def manageClientsLoop(self):
        while self.running:
            for uid, clientSession in self.clientSessions:
                # Not sure if python supports non-blocking queue iteration, so do this as a while
                unreadData = clientSession.unreadData.get(block=False)
                while (unreadData is not None):
                    logging.info("Received data %s", unreadData)
                    for otherUid in self.clientSessions.keys().remove(uid):
                        logging.info("Sending to %s", otherUid)
                        self.clientSessions[otherUid].addDataToSend(unreadData)
                    clientSession.unreadData.remove(unreadData)
                    unreadData = clientSession.unreadData.get(block=False)
            time.sleep(5)
        logging.info("Removing client management thread")
    # TODO state maagement, using timestamp
#     def updateAllData(self, newDataItems):
#         for newDataItem in newDataItems:
#             if newDataItem['type'] == 'Add' and (newDataItem['id'] not in self.allData.keys() or
#                                                  self.allData[newDataItem['id']]['created'] < newDataItem['created']):
#                 self.allData[newDataItem['id']] = newDataItem
#             elif newDataItem['type'] == 'Remove' and newDataItem['id'] in self.allData.keys() and \
#                                                    self.allData[newDataItem['id']]['created'] < newDataItem['modified']:
#                 del self.allData[newDataItem['id']]
#             elif newDataItem['type'] == 'Move' and newDataItem['id'] in self.allData.keys() and \
#                                                    self.allData[newDataItem['id']]['modified'] < newDataItem['modified']:
#                 self.allData[newDataItem['id']]['modified'] = newDataItem['modified']
#                 self.allData[newDataItem['id']]['tilePosition'] = newDataItem['tilePosition']
# TODO
# def closeConnections(fromServer):
#     while fromServer.running:
#         for session in list(fromServer.sessions.values()):
#             if session.isTimedOut():
#                 #TODO send disconnect message
#                 logging.info("Session %s timed out, removing", session.getUid())
#                 session.closeSocket()
#                 del fromServer.sessions[session.getUid()]
#         # yield for main connection loop to run
#         time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = Server()
    t = threading.Thread(target=server.manageClientsLoop)
    t.daemon = True
    t.start()
    server.acceptConnectionLoop()
    logging.info("Exiting server session")