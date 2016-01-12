import subprocess
import itertools
import socket

class BleScanner:
    def __init__(self, process_beacon, my_ip):
        self.process_beacon = process_beacon
        self.my_ip = my_ip

    def start_scan(self):

        # hcitool lescan --duplicates
        # hcidump --raw
        cmd_scan = "hcitool lescan --duplicates"
        proc = subprocess.Popen(cmd_scan, shell=True, stdout=subprocess.PIPE)

        cmd_dump = "hcidump --raw"
        proc = subprocess.Popen(cmd_dump, shell=True, stdout=subprocess.PIPE)

        proc = subprocess.Popen("ls -la", shell=True, stdout=subprocess.PIPE)

        while True:
            line = proc.stdout.readline()

            if line != '':
                print line.rstrip()
                tokens = line.split()
                if tokens[0] == '>' and tokens[6] == '00' and tokens[14] == '04':
                    mac_address = tokens[13]+":"+tokens[12]+":"+tokens[11]+":"+tokens[10]+":"+tokens[9]+":"+tokens[8]
                    ip_address = tokens[15]+"."+tokens[16]+"."+tokens[17]+"."+tokens[18]
                    rssi = tokens[19]
                    human_name = ''
                    name_line = proc.stdout.readline()
                    if name_line != '':
                        print line.rstrip()
                        name_tokens = name_line.split()
                        if name_tokens[0] == '>' and tokens[6] == '04':
                            list = []
                            for token in itertools.islice(name_tokens , 17, None):
                                list.append(token)
                            del list[-1]
                            for token in list:
                                human_name += token
                    self.process_beacon(mac_address, ip_address, rssi, human_name)

    @staticmethod
    def set_beacon(ip_address):
        # cmd = "hcitool -i hci0 cmd 0x08 0x0008 04 C0 A8 02 37"
        ip_tokens = ip_address.split(".")

        hex_ip_string = ''
        for token in ip_tokens:
            hex = "%0.2X" % int(token)
            hex_ip_string += " " + hex
            # print hex
        # print hexIpString

        cmd = "hcitool -i hci0 cmd 0x08 0x0008 04" + hex_ip_string
        print cmd
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        # hcitool -i hci0 cmd 0x08 0x0008 04 C0 A8 02 37

    @staticmethod
    def start_beacon():
        cmd = "hciconfig hci0 leadv"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    @staticmethod
    def stop_beacon():
        cmd = "hciconfig hci0 noleadv"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

print socket.gethostbyname(socket.gethostname())