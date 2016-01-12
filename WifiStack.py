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
        self.my_ip = ''
        self.connect()

    def get_my_ip(self):
        return self.my_ip

    def get_address(self):
        return self.address

    def get_port(self):
        return self.port

    def connect(self):
        for i in range(5):
            try:
                self.socket.connect((self.address, self.port))
            except socket.error as msg:
                logger.error("Socket Connection Error: %s" % msg)
                time.sleep(2)
                continue
            self.my_ip = self.socket.getsockname()[0]
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
            packed_msg = struct.pack(frmt, msg)
            packed_hdr = struct.pack('=I', len(packed_msg))

            self._send(packed_hdr)
            logger.info("Sent HDR")
            self._send(packed_msg)
            logger.info("Sent MSG")

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
            data_tmp = self.conn.recv(size-len(data))
            data += data_tmp
            if data_tmp == '':
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
    def __init__(self, process_callback, port=5419):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = self.socket
        self.port = port
        self.active = False
        self.process_callback = process_callback
        self.other_address = ''
        self._bind()

    def _bind(self):
        self.socket.bind(('', self.port))

    def _listen(self):
        self.socket.listen(5)  # 5 connections are kept, waiting and the 6th is refused

    def _accept(self):
        return self.socket.accept()

    def accept_conn(self):
        self._listen()

        self.conn, self.other_address = self._accept()  # TODO: add timeout eventually

        logger.debug("connection accepted, conn socket (%s,%d)" % (self.other_address[0], self.other_address[1]))

    def run(self):
        while self.active:
            try:
                self.accept_conn()
                wifi_conn = WifiConnection(self.conn, self.other_address, self.process_callback)
                wifi_conn.start()
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
    def __init__(self, conn, other_address, process_callback):
        threading.Thread.__init__(self)
        self.conn = conn
        self.other_address = other_address
        self.active = False
        self.process_callback = process_callback

    def msg_length(self):
        d = self._read(4)
        s = struct.unpack('=I', d)
        return s[0]

    def _read(self, size):
        data = ''
        while len(data) < size:
            data_tmp = self.conn.recv(size-len(data))
            data += data_tmp
            if data_tmp == '':
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
                obj = self.read_json()
                logger.info("Read JSON")
                self.process_callback(self.other_address, obj)
            except Exception as e:
                logger.exception(e)
                self.close()
                break

    def start(self):
        self.active = True
        super(WifiConnection, self).start()

    def stop(self):
        self.active = False
