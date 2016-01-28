import struct, time, json, logging, uuid, socket, threading
from Queue import Queue

DISCONNECT_TIME_SEC = 30

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

# Client,              server,          server client - set up with a socket, reads all client data from socket until disconnect
# send/recv blocking, recv non blocking, send/recv blocking
# TODO should use type object pattern
class Session(object):
    """ Base Session that gets given a socket"""
    def __init__(self, socket):
        logging.basicConfig(level=logging.INFO)
        self.unsentData = list()
        self.unreadData = Queue()
        self.socket = socket
        self.startThreads()
        print "Exiting session"

    def startThreads(self):
        self.processIncoming = True
        self.startThread(self.processIncomingMessages)
        self.processOutgoing = True
        self.startThread(self.sendOutgoingMessages)

    def startThread(self, processMethod):
        t = threading.Thread(target=processMethod)
        t.daemon = True
        t.start()

    def processIncomingMessages(self):
        incomingData = None
        while self.processIncoming and self.socket is not None:
            socketToRecvFrom = None
            try:
                socketToRecvFrom = self.getRecvSocket()
                msg = recv_msg(socketToRecvFrom)
                self.lastConnectTime = time.time()
                logging.info("Received msg %s", msg)
                incomingData = json.loads(msg) if msg is not None else None
            except socket.error:
                if socketToRecvFrom is not None:
                    socketToRecvFrom.close()
                if socketToRecvFrom is self.socket:
                    self.socket = self.initSocket()
            if incomingData is not None:
                for data in incomingData: # TODO if single JSON entry check this doesnt split into elements
                    self.addUnreadData(socketToRecvFrom, data)
            else:
                time.sleep(0.5)
        print logging.info("Shutting down listening")

    def sendOutgoingMessages(self):
        while self.processOutgoing and self.socket is not None:
            clientSocket = None
            try:
                for data in list(self.unsentData):
                    self.unsentData.remove(data)
                    toSend = json.dumps(data)
                    logging.debug("Sending data %s", toSend)
                    send_msg(clientSocket, toSend)
                    self.lastConnectTime = time.time()
                time.sleep(1)
            except socket.error:
                if clientSocket is not None:
                    clientSocket.close()
                if clientSocket is self.socket:
                    self.socket = self.initSocket()

    def initSocket(self):
        return None

    def getRecvSocket(self):
        return self.socket

    def getUnreadDataQueue(self):
        return self.unreadData

    def isTimedOut(self):
        cutoffTime = time.time() - DISCONNECT_TIME_SEC
        return self.lastConnectTime < cutoffTime

    def addDataToSend(self, **data):
        self.unsentData.append(data)

    def addUnreadData(self, socket, data):
        timestamp = data["timestamp"]
        del data["timestamp"]
        # TODO this hsould be common
        self.unreadData.put((timestamp, data))

class ClientSession(Session):
    """ A Session with a uid that creates a new socket which it connects to a server, it reads and writes to that """
    def __init__(self):
        super(ClientSession, self).__init__(self.initSocket())
        self.unsentData = list({id:str(uuid.uuid4())})

    def initSocket(self):
        soc = socket.socket()
        port = 12344 # TODO from config
        try:
            host = socket.gethostname() # TODO read server hostname from config, this only works while they share a socket
            soc.connect((host, port))
            logging.debug("Connected socket to %s %s", host, port)
        except Exception:
            host = '127.0.0.1'
            try:
                soc.connect((host, port))
                logging.debug("Connected socket to %s %s", host, port)
            except Exception:
                logging.error("%s could not connect to server.", host)
                self.running = False
                soc = None
        return soc

    def addDataToSend(self, **data):
        now = time.time()
        milliseconds = '%03d' % int((now - int(now)) * 1000)
        data["timestamp"] = time.strftime('%Y%m%d%H%M%S', time.localtime(now)) + milliseconds
        self.unsentData.append(data)

    def addUnreadData(self, socket, data):
        self.unreadData.put(data)

class ServerSession(Session):
    """ A Session that can accept multiple connections without blocking """
    def __init__(self):
        super(ServerSession, self).__init__(self.initSocket())

    def initSocket(self):
        soc = socket.socket()
        port = 12344
        try:
            host = socket.gethostname() # TODO read server hostname from config, this only works while they share a socket
            soc.bind((host, port))
            soc.listen(5) # TODO max num connections should be read from config
            logging.debug("Connected socket to %s %s", host, port)
        except Exception:
            logging.error("could not set up server.")
            self.running = False
            soc = None
        return soc

    def startThreads(self):
        self.processIncoming = True
        self.startThread(self.processIncomingMessages)

    def getRecvSocket(self):
        socketToRecvFrom, (addr, port) = self.socket.accept()
        return socketToRecvFrom

    def addUnreadData(self, socket, data):
        uid = data["id"]
        del data["id"]
        self.unreadData.put((socket, uid))