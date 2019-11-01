#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import ipaddress
import json
import os
import re
import shutil
import xml.etree.ElementTree as eTree
from distutils.dir_util import copy_tree
from pathlib import Path

import click
import urllib3
# from progress.bar import Bar
from PyInquirer import prompt, ValidationError, Validator
from pyfiglet import Figlet
from urllib3.exceptions import NewConnectionError, ConnectTimeoutError

# Constants
STANDARD_CHANNEL_STRUCTURE = [
    'manifest',
    'components/**',
    'source/**',
    'images/**'
]
CONFIG_FILE = 'rokuPiConfig.json'
STAGE_DIR = 'rokuPiTemp'


class IpAddressValidator(Validator):
    def validate(self, value):
        if len(value.text):
            try:
                if ipaddress.ip_address(value.text):
                    return True
                else:

                    raise ValidationError(
                        message="IP address needs to be in IPV4 format",
                        cursor_position=len(value.text))
            except ValueError:
                raise ValidationError(
                    message="IP address needs to be in IPV4 format",
                    cursor_position=len(value.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class EmptyValidator(Validator):
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class Roku:
    @staticmethod
    def scan_network():
        """
        Scans LAN for any available rokus.
        :return: List - an list of device dictionaries, removes any "Nones" before returning
        """
        network_ping_results = os.popen('arp -a').read()
        ip_list = [parse_ip_from_output(i) for i in network_ping_results.split('?')]
        device_list = [query_ip_address_for_device_info(ip) for ip in ip_list]

        return [device for device in device_list if device is not None]

    @staticmethod
    def write_device_data_to_config(device_data, config_path):
        config_data = json.load(open(str(config_path), 'r'))
        print(config_data)
        config_data["device"] = device_data
        with open(str(config_path), 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

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


def query_ip_address_for_device_info(ip_address):
    """
    Pings each ip address to see with roku query device,
    checks for response back then will parse device data xml
    :param ip_address - String - ip address IPV4 to ping with device query
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
                            return {
                                'name': f'{child.text} - {ip_address}',
                                'value': {
                                    'name': child.text,
                                    'username': 'rokudev',
                                    'ip_address': ip_address,
                                    'password': ''
                                }
                            }
        except NewConnectionError:
            click.echo(f'Unable to establish connection with {ip_address}')
            return None
        except ConnectTimeoutError:
            click.echo(f'Connection timed out connecting to {ip_address}')
            return None


def device_selection():
    available_devices = Roku.scan_network()
    device = {}
    write_to_config = False
    if len(available_devices) > 0:
        device_selection_questions = [
            {
                "type": 'checkbox',
                "message": 'Select Device',
                "name": 'device',
                "choices": available_devices,
                "validate": lambda answer: 'You must choose at least one device.'
                if len(answer) == 0 else True
            }, {
                'type': 'input',
                'name': 'password',
                'message': 'Enter device Password:',
                'validate': EmptyValidator,
            }, {
                'type': 'confirm',
                'name': 'save_device',
                'message': 'Do you want to save this device'
            }
        ]
        device_selection_answers = prompt(device_selection_questions)
        device_selection_answers["device"][0]["password"] = device_selection_answers["password"]
        device = device_selection_answers["device"][0]
        write_to_config = device_selection_answers["save_device"]
    else:
        click.echo('no devices found on network')
        add_roku_config = click.prompt('Would you like to define one manually y/n', type=str, default='y')
        if add_roku_config == 'y':
            device_questions = [
                {
                    "type": 'input',
                    "name": 'name',
                    "message": 'Device Name',
                    "default": 'My Roku',
                    "validate": EmptyValidator
                },
                {
                    "type": 'input',
                    "name": 'username',
                    "message": 'Username',
                    "default": 'rokudev',
                },
                {
                    "type": 'input',
                    "name": 'password',
                    "message": 'Password',
                    "validate": EmptyValidator
                },
                {
                    "type": 'input',
                    "name": 'ip_address',
                    "message": 'Ip Address',
                    "validate": IpAddressValidator
                }
            ]
            device = prompt(device_questions)
            write_to_config = True

    return {
        "device": device,
        "write_to_config": write_to_config
    }


class Channel:
    def __init__(self, path_to_channel):
        self.channel_path = Path(path_to_channel)
        self.channel_contents = os.listdir(self.channel_path)
        self.config_data = {}
        self.config_file = self.get_config_file()
        self.out_dir = self.get_out_dir()
        self.manifest_data = None

    def get_config_file(self):
        """
        Checks to see if config file is available in channel content
        :return: Object, None -
        """
        if CONFIG_FILE in self.channel_contents:
            return self.channel_path / CONFIG_FILE
        else:
            return None

    def set_config_file_data(self):
        self.config_file = self.channel_path / CONFIG_FILE
        with open(self.config_file) as config_file:
            self.config_data = json.load(config_file)

    def get_out_dir(self):
        out_path = os.path.join(self.channel_path, 'out')
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        return Path(out_path)

    def __str__(self):
        if {'title', 'major_version', 'minor_version', 'build_version'} <= set(self.manifest_data.keys()):
            return f'{self.manifest_data["title"]}_' \
                   f'{self.manifest_data["major_version"]}.' \
                   f'{self.manifest_data["minor_version"]}.' \
                   f'{self.manifest_data["build_version"]}'


def parse_manifest(manifest_path):
    """
    Parses channel manifest channel data
    :param manifest_path - Object -
    :return: Dictionary
    """
    manifest_data = {}
    with open(manifest_path) as manifest:
        for i, line in enumerate(manifest):
            if line != '\n':
                key_pair = line.split('=')
                key, value = key_pair[0], key_pair[1].replace('\n', '')
                manifest_data = {**manifest_data, **{key: value}}

    return manifest_data


def create_config_file(glob_list, destination_path):
    """
    Parses channel manifest channel data
    :param glob_list - List - list of file that need to be deployed for channel
    :param destination_path - String - path
    """
    config_data = {
        "files": glob_list
    }
    with open(os.path.join(destination_path, CONFIG_FILE), 'w') as config_file:
        json.dump(config_data, config_file, indent=4)


def empty_dir(dir_to_empty):
    for root, dirs, files in os.walk(dir_to_empty):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def stage_channel_contents(channel_path, glob_array):
    stage_dir_path = channel_path / STAGE_DIR

    if stage_dir_path.exists():
        empty_dir(stage_dir_path)
    else:
        os.mkdir(stage_dir_path)

    for content_path in glob_array:
        copy_content_to_staging_dir(channel_path, content_path)


def copy_content_to_staging_dir(channel_path, content_path):
    for from_path in glob.glob(os.path.join(channel_path, content_path)):
        from_path = Path(from_path)
        to_path = channel_path / STAGE_DIR / from_path.relative_to(channel_path)

        if from_path.is_file():
            if not to_path.parent.exists():
                os.mkdir(str(to_path.parent))

            try:
                shutil.copyfile(str(from_path), str(to_path))
            except FileNotFoundError:
                click.echo(f'failed to copy {str(from_path)} into staging')
        elif from_path.is_dir():
            copy_tree(str(from_path), str(to_path))
        else:
            click.echo(f'failed to copy {str(from_path)} into staging')


def archive_staged_content_to_out(staging_dir_path, out_dir_path):
    if not out_dir_path.parent.exists():
        os.mkdir(str(out_dir_path.parent))

    if out_dir_path.parent.exists():
        empty_dir(str(out_dir_path.parent))

    shutil.make_archive(out_dir_path, 'zip', staging_dir_path)


@click.command()
@click.option('-c',
              '--channel',
              'channel_path',
              help='path to channel root dir',
              required=True)
@click.option('-ip',
              '--roku-ip',
              'roku_ip',
              help='Ip address to roku',
              required=False)
def deploy(channel_path, roku_ip):
    f = Figlet(font='slant')
    click.echo(f.renderText('RokuPi'))
    current_channel = Channel(channel_path)

    # create config if non-existent
    if current_channel.config_file is None:
        create_config_response = click.prompt('Would like to create config file y/n ', type=str, default='y')

        if create_config_response.lower() == 'y':
            click.echo(f'Default structure \n{STANDARD_CHANNEL_STRUCTURE}\nThis can be updated later')
            use_default_channel_structure = click.prompt(
                'Would you like to use default channel structure y/n',
                type=str,
                default='y'
            )
            if use_default_channel_structure.lower() == 'y':
                create_config_file(STANDARD_CHANNEL_STRUCTURE, current_channel.channel_path)
            else:
                example = 'manifest, someDir/**, anotherDir/**'
                click.echo(f'please input you channel structure, '
                           f'use unix glob pattern in comma separated values {example}')
                custom_channel_structure = input("Please input your channel structure: ")

                if custom_channel_structure != '':
                    folders = custom_channel_structure.split(',')
                    create_config_file(folders, current_channel.channel_path)
                    current_channel.set_config_file_data()
                else:
                    click.echo(f'please use an array of files {example}')

    # Parse manifest for data
    current_channel.manifest_data = parse_manifest(current_channel.channel_path / 'manifest')
    current_channel.set_config_file_data()

    # Stage channel contents and create archive
    stage_channel_contents(current_channel.channel_path, current_channel.config_data["files"])
    stage_dir_path = current_channel.channel_path / STAGE_DIR
    out_dir = current_channel.channel_path / 'out' / current_channel.__str__()
    archive_staged_content_to_out(stage_dir_path, out_dir)

    # empty stage dir and remove
    empty_dir(str(stage_dir_path))
    stage_dir_path.rmdir()

    if roku_ip is None:
        device_selection_results = None
        # No device defined in config
        if "device" not in current_channel.config_data.keys() or not bool(current_channel.config_data["device"]):
            device_selection_results = device_selection()
            device = device_selection_results["device"]
        # using device defined in config
        else:
            current_channel.set_config_file_data()
            device = current_channel.config_data["device"]
            use_config_roku = click.prompt(f'Would you like to use {device["name"]} @ {device["ip_address"]} y/n',
                                           type=str,
                                           default='y')
            # not using device in config but there is one
            if use_config_roku.lower() != 'y':
                device_selection_results = device_selection()
                device = device_selection_results["device"]
        # scanning/manual input device saving
        if device_selection_results and device_selection_results["write_to_config"]:
            Roku.write_device_data_to_config(device, current_channel.config_file)
            current_channel.set_config_file_data()
    else:
        device = {
            "name": ' ',
            "username": 'rokudev',
            "password": '',
            "ip_address": roku_ip
        }
        try:
            if ipaddress.ip_address(device["ip_address"]):
                device_password = click.prompt('device password', type=str, hide_input=True)
                device["password"] = device_password
            else:
                click.echo("IP address needs to be in IPV4 format")
        except ValueError:
            click.echo("IP address needs to be in IPV4 format")

        data_from_device = query_ip_address_for_device_info(roku_ip)
        if data_from_device is None:
            click.echo("Unable to establish connection with device")
            return
        else:
            device["name"] = data_from_device["value"]["name"]
            save_device = click.prompt('Do you want to save this device y/n',  type=str, default='y')
            if save_device == 'y':
                Roku.write_device_data_to_config(device, current_channel.config_file)
                current_channel.set_config_file_data()




if __name__ == '__main__':
    deploy()
