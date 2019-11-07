import json
import os

from pathlib import Path
from constants import CONFIG_FILE


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

    def get_channel_archive(self):
        out_dir = self.get_out_dir()
        for child in out_dir.iterdir():
            if Path(child).is_file:
                return Path(child)

        return None

    def __str__(self):
        if {'title', 'major_version', 'minor_version', 'build_version'} <= set(self.manifest_data.keys()):
            return f'{self.manifest_data["title"]}_' \
                   f'{self.manifest_data["major_version"]}.' \
                   f'{self.manifest_data["minor_version"]}.' \
                   f'{self.manifest_data["build_version"]}'