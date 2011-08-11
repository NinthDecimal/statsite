#!/usr/bin/env python
"""statsite

.. program:: statsite

"""

import ConfigParser
from optparse import OptionParser

class StatsiteCommand(object):
    def __init__(self, args=None):
        # Define and parse the command line options
        parser = OptionParser()
        parser.add_option("-c", "--config", action="store", dest="config_file",
                          default=None, help="path to a configuration file")
        parser.add_option("-s", "--setting", action="append", dest="settings",
                          default=[], help="set a setting")
        (self.options, _) = parser.parse_args(args)

        # Parse the settings from file, and then from the command line,
        # since the command line trumps any file-based settings
        self.settings = {}
        if self.options.config_file:
            self._parse_settings_from_file(self.options.config_file)

        self._parse_settings_from_options()

    def start(self):
        pass

    def _parse_settings_from_file(self, path):
        """
        Parses settings from a configuration file.
        """
        config = ConfigParser.RawConfigParser()
        config.read(path)

        for section in config.sections():
            for (key, value) in config.items(section):
                self._add_setting(section, key, value)

    def _parse_settings_from_options(self):
        """
        Parses settings from the command line options.
        """
        for setting in self.options.settings:
            key, value = setting.split("=", 2)
            section, key = key.split(".", 2)
            self._add_setting(section, key, value)

    def _add_setting(self, section, key, value):
        """
        Adds settings to a specific section.
        """
        self.settings.setdefault(section, {})
        self.settings[section][key] = value

def main():
    "The main entrypoint for the statsite command line program."
    command = StatsiteCommand()
    command.start()

if __name__ == "__main__":
    main()
