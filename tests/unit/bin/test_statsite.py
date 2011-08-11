"""
Contains tests for the `statsite` binary program.
"""

from tests.base import TestBase
from statsite.bin.statsite import StatsiteCommand

class TestStatsiteBin(TestBase):
    def test_parse_settings_from_file(self, tempfile):
        """
        Tests that the statsite command can properly read settings
        from a configuration file.
        """
        tempfile.write("""
[collection]
key=value
""")
        tempfile.flush()

        command = StatsiteCommand(["-c", tempfile.name])
        assert "value" == command.settings["collection"]["key"]

    def test_parse_settings_from_options(self):
        """
        Tests that the statsite can read options from the command
        line.
        """
        command = StatsiteCommand(["-s", "collection.key=value"])
        assert "value" == command.settings["collection"]["key"]

    def test_parse_command_line_over_file(self, tempfile):
        """
        Tests that command line options override file options.
        """
        tempfile.write("""
[collection]
key=value
key2=value2
""")
        tempfile.flush()

        command = StatsiteCommand(["-c", tempfile.name, "-s", "collection.key2=bam"])
        assert "value" == command.settings["collection"]["key"]
        assert "bam" == command.settings["collection"]["key2"]

    def test_parse_dot_settings_from_file(self, tempfile):
        """
        Tests that settings separated by dots are properly stored
        from a file.
        """
        tempfile.write("""
[collection]
key.sub=value
""")
        tempfile.flush()

        command = StatsiteCommand(["-c", tempfile.name])
        assert "value" == command.settings["collection"]["key"]["sub"]

    def test_syntax_error_in_configuration_file(self, tempfile):
        """
        Tests that a syntax error in a configuration file raises a
        proper error.
        """
        tempfile.write("I'm invalid!")
        tempfile.flush()

        # TODO: This should raise a proper exception
        # StatsiteCommand(["-c", tempfile.name])
