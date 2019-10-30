#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
from distutils.dir_util import copy_tree
import glob
import json
from pathlib import Path
from pyfiglet import Figlet
import os
import shutil

# Constants
STANDARD_CHANNEL_STRUCTURE = [
    'manifest',
    'components/**',
    'source/**',
    'images/**'
]
CONFIG_FILE = 'rokuPiConfig.json'
STAGE_DIR = 'rokuPiTemp'


def parse_manifest(manifest_path):
    manifest_data = {}
    with open(manifest_path) as manifest:
        for i, line in enumerate(manifest):
            if line != '\n':
                key_pair = line.split('=')
                key, value = key_pair[0], key_pair[1].replace('\n', '')
                manifest_data = {**manifest_data, **{key: value}}

    return manifest_data


def create_config_file(glob_array, destination_path):
    config_data = {
        "files": glob_array
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


class Channel:
    def __init__(self, path_to_channel):
        self.channel_path = Path(path_to_channel)
        self.channel_contents = os.listdir(self.channel_path)
        self.config_data = {}
        self.config_file = self.get_config_file()
        self.out_dir = self.get_out_dir()
        self.manifest_data = None

    def get_config_file(self):
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

@click.command()
@click.option('-p',
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
    # current_channel = Channel(channel_path)
    current_channel = Channel('/Users/christiancecilia/Work/Roku')

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
    current_channel.manifest_data = parse_manifest(os.path.join(current_channel.channel_path, 'manifest'))
    current_channel.set_config_file_data()

    # Stage channel contents and create archive
    stage_channel_contents(current_channel.channel_path, current_channel.config_data["files"])
    stage_dir_path = current_channel.channel_path / STAGE_DIR
    out_dir = current_channel.channel_path / 'out' / current_channel.__str__()
    archive_staged_content_to_out(stage_dir_path, out_dir)

    # empty stage dir and remove
    empty_dir(str(stage_dir_path))
    stage_dir_path.rmdir()


if __name__ == '__main__':
    deploy()
