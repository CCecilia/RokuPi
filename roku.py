import click
import concurrent.futures
import ipaddress
import json
import os
import re
import urllib3
import xml.etree.ElementTree as eTree

from urllib3.exceptions import NewConnectionError, ConnectTimeoutError

device_pool = []


class Roku:
    def __init__(self, device_data):
        self.http = urllib3.PoolManager()
        self.device_plugin_url = f'http://{device_data["ip_address"]}/plugin_install'
        self.device_data = device_data

    @staticmethod
    def scan_network():
        """
        Scans LAN using address resolution protocol for any available devices then .
        :return: List - an list of device dictionaries, removes any "Nones" before returning
        """
        click.echo('Scanning netwrok for devices')
        network_ping_results = os.popen('arp -a').read()
        ip_list = [parse_ip_from_output(i) for i in network_ping_results.split('?')]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            {executor.submit(query_ip_address_for_device_info, ip, True): ip for ip in ip_list}

        return [device for device in device_pool if device is not None]

    @staticmethod
    def write_device_data_to_config(device_data, config_path):
        config_data = json.load(open(str(config_path), 'r'))
        config_data["device"] = device_data
        with open(str(config_path), 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

    def delete_channel(self):
        click.echo('removing channel from  device')
        delete_cmd = f'curl --user {self.device_data["username"]}:{self.device_data["password"]} --digest -s -S ' \
                     f'-F "mysubmit=Delete" ' \
                     f'{self.device_plugin_url}'
        os.popen(delete_cmd).read()

    def deploy_channel(self, channel):
        archive_path = channel.get_channel_archive()
        click.echo(f'deploying {channel.__str__()} channel from  device')
        deploy_cmd = f'curl --user {self.device_data["username"]}:{self.device_data["password"]} --digest -s -S ' \
                     f'-F "mysubmit=Install" ' \
                     f'-F "archive=@{archive_path}" ' \
                     f'{self.device_plugin_url}'
        os.popen(deploy_cmd).read()

    def send_key_press(self, key_press):
        if isinstance(key_press, str):
            if key_press.count(key_press[0]) == len(key_press):
                key_press = f'Lit_{key_press}'

            # requests.post(f'http://{self.device_data["ip_address"]}:8060/keypress/{key_press}')
            http = urllib3.PoolManager()
            url = f'http://{self.device_data["ip_address"]}:8060/keypress/{key_press}'
            http.request('POST', url, retries=False)
        else:
            raise ValueError('key_press must be a non empty string')

    def __str__(self):
        return 'Roku'


def parse_ip_from_output(output_string):
    """
    Parses ip address out from arp output
    :param output_string - String -
    :return: String, None - either none if device didn't respond or timed out
    """
    if output_string != '':
        ip_address = re.split(' ', output_string.lstrip(), 2)[0][1:-1]

        try:
            if ipaddress.ip_address(ip_address):
                return ip_address
        except ValueError:
            click.echo(f'got {ip_address} instead of ip')


def query_ip_address_for_device_info(ip_address, use_device_pool=False):
    """
    Pings each ip address to see with roku query device,
    checks for response back then will parse device data xml
    :param use_device_pool:
    :param ip_address: String - ip address IPV4 to ping with device query
    :return: Dictionary - dict is formatted for PyInquirer's choices, and contains available device info
    """
    timeout = urllib3.Timeout(connect=2.0, read=7.0)
    http = urllib3.PoolManager(timeout=timeout)
    if isinstance(ip_address, str):
        url = f'http://{ip_address}:8060/query/device-info'
        try:
            response = http.request('GET', url, retries=False)
            if response.status == 200:
                data = response.data
                if isinstance(data, bytes):
                    tree = eTree.fromstring(data)
                    for child in tree:
                        if child.tag == 'friendly-model-name':
                            device = {
                                'name': f'{child.text} - {ip_address}',
                                'value': {
                                    'name': child.text,
                                    'username': 'rokudev',
                                    'ip_address': ip_address,
                                    'password': ''
                                }
                            }

                            if not use_device_pool:
                                return device
                            else:
                                device_pool.append(device)
        except NewConnectionError:
            click.echo(f'Unable to establish connection with {ip_address}')
            return None
        except ConnectTimeoutError:
            click.echo(f'Connection timed out connecting to {ip_address}')
            return None
