import socket
import logging
import time
import struct
import threading


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)


class WifiClient(object):
    def __init__(self, address="127.0.0.1", port=5419):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = self.socket
        self.address = address
        self.port = port

    def get_address(self):
        return self.address

    def get_port(self):
        return self.port

    def connect(self):
        for i in range(5):
            try:
                self.socket.connect( (self.address, self.port) )
            except socket.error as msg:
                logger.error("Socket Connection Error: %s" % msg)
                time.sleep(2)
                continue
            logger.info("Socket Connected")
            return True
        return False

    def send(self, obj):
        self.send_json(obj)

    def send_json(self, obj):
        # msg = json.dumps(obj)
        msg = obj
        if self.socket:
            frmt = "=%ds" % len(msg)
            packedMsg = struct.pack(frmt, msg)
            packedHdr = struct.pack('=I', len(packedMsg))

            self._send(packedHdr)
            self._send(packedMsg)

    def _send(self, msg):
        sent = 0
        while sent < len(msg):
            sent += self.conn.send(msg[sent:])

    def msg_length(self):
        d = self._read(4)
        s = struct.unpack('=I', d)
        return s[0]

    def _read(self, size):
        data = ''
        while len(data) < size:
            dataTmp = self.conn.recv(size-len(data))
            data += dataTmp
            if dataTmp == '':
                raise RuntimeError("Socket Connection Severed")
        return data

    def read_json(self):
        size = self.msg_length()
        data = self._read(size)
        frmt = "=%ds" % size
        msg = struct.unpack(frmt, data)
        # obj = json.loads(msg[0])
        obj = msg
        return obj

    def close(self):
        logger.debug("Closing Connection Socket")
        self.conn.close()  # Careful, might need to close socket separately


class WifiServer(threading.Thread):
    def __init__(self, port=5419):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = self.socket
        self.port = port
        self.active = False

    def _bind(self):
        self.socket.bind(('', self.port))

    def _listen(self):
        self.socket.listen(5)  # 5 connections are kept, waiting and the 6th is refused

    def _accept(self):
        return self.socket.accept()

    def accept_conn(self):
        self.conn, addr = self._accept()  # TODO: add timeout eventually

        logger.debug("connection accepted, conn socket (%s,%d)" % (addr[0], addr[1]))

    def run(self):
        while self.active:
            try:
                self.accept_conn()
                wifiConn = WifiConnection(self.conn)
            except Exception as e:
                logger.exception(e)
                continue

    def start(self):
        self.active = True
        super(WifiServer, self).start()

    def stop(self):
        self.active = False

    def close(self):
        logger.debug("Closing Connection Socket")
        self.conn.close()  # Careful, might need to close socket separately


class WifiConnection(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.active = False

    def process_message(self, obj):
        logger.debug("Dummy Process")
        logger.debug(obj)

    def msg_length(self):
        d = self._read(4)
        s = struct.unpack('=I', d)
        return s[0]

    def _read(self, size):
        data = ''
        while len(data) < size:
            dataTmp = self.conn.recv(size-len(data))
            data += dataTmp
            if dataTmp == '':
                raise RuntimeError("Socket Connection Severed")
        return data

    def read_json(self):
        size = self.msg_length()
        data = self._read(size)
        frmt = "=%ds" % size
        msg = struct.unpack(frmt, data)
        # obj = json.loads(msg[0])
        obj = msg
        return obj

    def close(self):
        logger.debug("Closing Connection Socket")
        self.conn.close()  # Careful, might need to close socket separately

    def run(self):
        while self.active:
                try:
                    obj = self.read_json
                    self.process_message(obj)
                except Exception as e:
                    logger.exception(e)
                    self.close()
                    break

    def start(self):
        self.active = True
        super(WifiConnection, self).start()

    def stop(self):
        self.active = False