import socket
import logging
import time
import struct
import threading
import json

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
        self._send(obj)

    def _send(self, data):
        # try:
        #    serialized = json.dumps(data)
        # except (TypeError, ValueError), e:
        #    raise Exception('You can only send JSON-serializable data')
        # send the length of the serialized data first
        self.conn.send('%d\n' % len(data))
        # send the serialized data
        self.conn.sendall(data)

    def close(self):
        logger.debug("Client: Closing Connection Socket")
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
        logger.debug("Server: Closing Connection Socket")
        self.conn.close()  # Careful, might need to close socket separately


class WifiConnection(threading.Thread):
    def __init__(self, conn, other_address, process_callback):
        threading.Thread.__init__(self)
        self.conn = conn
        self.other_address = other_address
        self.active = False
        self.process_callback = process_callback

    def read_json(self):
        if not self.conn:
            raise Exception('You have to connect first before receiving data')
        data = self._recv()
        # self.close()
        return data

    def _recv(self):
        # read the length of the data, letter by letter until we reach EOL
        length_str = ''
        char = self.conn.recv(1)
        while char != '\n':
            length_str += char
            char = self.conn.recv(1)
        total = int(length_str)
        # use a memoryview to receive the data chunk by chunk efficiently
        view = memoryview(bytearray(total))
        next_offset = 0
        while total - next_offset > 0:
            recv_size = self.conn.recv_into(view[next_offset:], total - next_offset)
            next_offset += recv_size
        # try:
        #    deserialized = json.loads(view.tobytes())
        # except (TypeError, ValueError), e:
        #     raise Exception('Data received was not in JSON format')
        logger.debug("Finished receiving data")
        # return deserialized
        return view.tobytes()

    def close(self):
        logger.debug("Connection: Closing Connection Socket")
        self.conn.close()  # Careful, might need to close socket separately

    def run(self):
        while self.active:
            try:
                obj = self.read_json()
                logger.debug("Data: " + obj)
                logger.info("Read JSON")
                logger.debug("Other address: " + self.other_address[0])
                self.process_callback(self.other_address, obj)
                self.close()
                break
            except Exception as e:
                logger.exception(e)
                self.close()
                break

    def start(self):
        self.active = True
        super(WifiConnection, self).start()

    def stop(self):
        self.active = False
