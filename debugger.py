import telnetlib


class Debugger:
    def __init__(self, device):
        print("device", device.device_data)
        self.device_ip = device.device_data["ip_address"]
        self.debug_server_port = 8080
        self.brs_console_port = 8085
        self.session = None
        print('debugger ip', self.device_ip)

    def start_session(self):
        try:
            self.session = telnetlib.Telnet(self.device_ip, self.brs_console_port)
            while True:
                text = self.session.read_until(b"\n")
                print(text)

        except Exception as e:
            print(e)

    def send_debug_command(self, command):
        if isinstance(command, str):
            try:
                self.session = telnetlib.Telnet(self.device_ip, self.debug_server_port)
                self.session.write(b"fps_display\n")
                self.session.write(b"exit\n")

            except Exception as e:
                print(e)
