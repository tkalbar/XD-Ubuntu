import enum
import WifiStack
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)

# Send context

# Send data

id_dict = {}


class Medium(Enum):
    def __str__(self):
        return str(self.value)
    WIFI = 1
    BLE = 2


def receive_data(deviceId, obj):
    logger.debug("Dummy receive data")


def send_data(device_id, obj):
    if select_delivery_medium()==Medium.WIFI:
        logger.debug("Sending data over WIFI medium")
        if id_dict[device_id] != '':
            client = WifiStack.WifiClient(address=id_dict[device_id])
            client.send(obj)
    elif select_delivery_medium()==Medium.BLE:
        logger.debug("Sending data over BLE medium (oops)")


def send_context(device_id, byteSeq):
    if select_exchange_medium()==Medium.BLE:
        logger.debug("Sending context over BLE medium")

    elif select_exchange_medium()==Medium.BLE:
        logger.debug("Sending context over WIFI medium (oops)")


def select_delivery_medium():
    # For this port, only Wifi and Ble are available
    return Medium.WIFI


def select_exchange_medium():
    # For this port, only Wifi and Ble are available
    return Medium.BLE


def _receive_data(deviceId, obj):
        server = WifiStack.WifiServer(address=)
        receive_data(obj)


def _receive_context(deviceId, ip):
    id_dict[deviceId] = ip
