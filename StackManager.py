import WifiStack
import BleStack
import logging
import commands
import time
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)


class XdInstance(object):
    def __init__(self, receive_data, receive_context):
        self.receive_data = receive_data
        self.receive_context = receive_context
        self.id_dict = {}
        self._init_stacks()

    def _receive_data(self, device_ip_address, obj):
        for dev_id, ip in self.id_dict.iteritems():
            if ip == device_ip_address:
                self.receive_data(dev_id, obj)

    def _receive_context(self, device_id, device_ip_address, rssi, human_name):
        self.id_dict[device_id] = device_ip_address
        self.receive_context(device_id, device_ip_address, rssi, human_name)

    def _init_stacks(self):
        self.server = WifiStack.WifiServer(self._receive_data)
        self.server.daemon = True
        self.server.start()

        BleStack.set_beacon(self.get_my_ip())
        BleStack.start_beacon()
        self.scanner = BleStack.BleScanner(self._receive_context)
        self.scanner.daemon = True
        self.scanner.start()

    @staticmethod
    def get_my_ip():
        return commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:]

    def send_data(self, device_id, obj):
        if self.select_delivery_medium() == "WIFI":
            logger.debug("Sending data over WIFI medium")
            if self.id_dict[device_id] != '':
                client = WifiStack.WifiClient(address=self.id_dict[device_id])
                client.send(obj)
        elif self.select_delivery_medium() == "BLE":
            logger.debug("Sending data over BLE medium (oops)")

    # def send_context(self, device_id, byteSeq):
    #    if self.select_exchange_medium() == "BLE":
    #        logger.debug("Sending context over BLE medium")
    #
    #    elif self.select_exchange_medium() == "WIFI":
    #        logger.debug("Sending context over WIFI medium (oops)")

    @staticmethod
    def select_delivery_medium():
        # For this port, only Wifi and Ble are available
        return "WIFI"

    @staticmethod
    def select_exchange_medium():
        # For this port, only Wifi and Ble are available
        return "BLE"


def data(dev_id, obj):
    print "dev_id: " + dev_id
    print "obj: " + obj


def context(device_id, device_ip_address, rssi, human_name):
    print "device_id: " + device_id
    print "device_ip_address: " + device_ip_address
    print "rssi: " + str(rssi)
    print "human_name: " + human_name

xd = XdInstance(data, context)
my_ip = xd.get_my_ip()
payload = {"c": 0, "b": 0, "a": 0}
time.sleep(7)
print "my_ip: " + my_ip
while True:
    if my_ip == "192.168.2.192":
        print "in 192"
        for dev_id in xd.id_dict:
            print "dict in 192: " + xd.id_dict[dev_id]
            if xd.id_dict[dev_id] == "192.168.2.55":
                xd.send_data(dev_id, json.dumps(payload))

    if my_ip == "192.168.2.55":
        print "in 55"
        for dev_id in xd.id_dict:
            print "dict in 55: " + xd.id_dict[dev_id]
            if xd.id_dict[dev_id] == "192.168.2.192":
                xd.send_data(dev_id, json.dumps(payload))

    time.sleep(2)

