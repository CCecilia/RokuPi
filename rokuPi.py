#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import os

STANDARD_CHANNEL_STRUCTURE = [
    'manifest',
    'components/**/*.*',
    'source/**/*.*',
    'images/**/*.*'
]


class Channel:
    def __init__(self, path_to_channel):
        self.channel_path = path_to_channel
        self.channel_contents = os.listdir(self.path)
        self.config_file = self.get_config()

    def get_config(self):
        file_query = [item for item in self.channel_contents if item == 'rokuPiConfig.json']
        if len(file_query) == 0:
            return None
        else:
            return file_query[0]



@click.group()
def channel():
    pass

@channel.command()
@click.option('--channel-path', help='path to channel root dir')
def deploy(channel_path):
    print(channel_path)
    current_channel = Channel(channel_path)
    print(current_channel)
    if current_channel.config_file == None:
    #   config creation route
        create_config = click.prompt('Would like to create config file y/n ', type=str, default='y')
        if create_config:
        #
        else:
            # use default channel Structure for channel class
            pass
    else:
#         update chanel class from config
        pass




if __name__ == '__main__':
    deploy()
