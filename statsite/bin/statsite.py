#!/usr/bin/env python
"""statsite

.. program:: statsite

"""

import logging
import logging.handlers
import signal
import sys
import threading
import ConfigParser
from optparse import OptionParser
from ..statsite import Statsite

class StatsiteCommandError(Exception):
    """
    This is the exception that will be raised if something goes wrong
    executing the Statsite command.
    """
    pass

class StatsiteCommand(object):
    TOPLEVEL_CONFIG_SECTION = "statsite"
    """
    This is the section to use in the configuration file if you wish to
    modify the top-level configuration.
    """

    def __init__(self, args=None):
        # Define and parse the command line options
        parser = OptionParser()
        parser.add_option("-c", "--config", action="append", dest="config_files",
                          default=[], help="path to a configuration file")
        parser.add_option("-l", "--log-level", action="store", dest="log_level",
                          default=None, help="log level")
        parser.add_option("-s", "--setting", action="append", dest="settings",
                          default=[], help="set a setting, e.g. collector.host=0.0.0.0")
        (self.options, _) = parser.parse_args(args)

        # Defaults
        self.statsite = None

        # Parse the settings from file, and then from the command line,
        # since the command line trumps any file-based settings
        self.settings = {}
        if len(self.options.config_files) > 0:
            self._parse_settings_from_file(self.options.config_files)

        self._parse_settings_from_options()

        # Setup the logger
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(lineno)s %(message)s"))

        logger = logging.getLogger("statsite")
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, self.settings["log_level"].upper()))

    def start(self):
        """
        Runs the statiste application.
        """
        signal.signal(signal.SIGINT, self._on_sigint)
        self.statsite = Statsite(self.settings)

        # Run Statsite in a separate thread so that signal handlers can
        # properly shut it down.
        thread = threading.Thread(target=self.statsite.start)
        thread.daemon = True
        thread.start()

        # Apparently `thread.join` blocks the main thread and makes it
        # _uninterruptable_, so we need to do this loop so that the main
        # thread can respond to signal handlers.
        while thread.isAlive():
            thread.join(0.2)

    def _on_sigint(self, signal, frame):
        """
        Called when a SIGINT is sent to cleanly shutdown the statsite server.
        """
        if self.statsite:
            self.statsite.shutdown()

    def _parse_settings_from_file(self, paths):
        """
        Parses settings from a configuration file.
        """
        config = ConfigParser.RawConfigParser()
        if config.read(paths) != paths:
            raise StatsiteCommandError, "Failed to parse configuration files."

        for section in config.sections():
            settings_section = section if section != self.TOPLEVEL_CONFIG_SECTION else None
            for (key, value) in config.items(section):
                self._add_setting(settings_section, key, value)

    def _parse_settings_from_options(self):
        """
        Parses settings from the command line options.
        """
        # Set the log level up
        self.settings.setdefault("log_level", "info")
        if self.options.log_level:
            self.settings["log_level"] = self.options.log_level

        # Set the generic options
        for setting in self.options.settings:
            key, value = setting.split("=", 2)
            section, key = key.split(".", 2)
            self._add_setting(section, key, value)

    def _add_setting(self, section, key, value):
        """
        Adds settings to a specific section.
        """
        if section is None:
            # If section is 'None' then we put the key/value
            # in the top-level settings
            current = self.settings
        else:
            # Otherwise we put it in the proper section...
            self.settings.setdefault(section, {})

            # Split the key by "." characters and make sure
            # that each character nests the dictionary further
            current = self.settings[section]
            parts = key.split(".")
            for part in parts[:-1]:
                current.setdefault(part, {})
                current = current[part]

            # The key is now the last of the dot-separated parts
            key = parts[-1]

        # Finally set the value onto the settings
        current[key] = value

def main():
    "The main entrypoint for the statsite command line program."
    try:
        command = StatsiteCommand()
        command.start()
    except StatsiteCommandError, e:
        sys.stderr.write("Error: %s\n" % e.message)
        sys.exit(1)

if __name__ == "__main__":
    main()
