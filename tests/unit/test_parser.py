"""
Contains tests to test the parsing of messages sent to
Statsite.
"""

import pytest
import statsite.parser as p

class TestParser(object):
    def test_parse_line_basic(self):
        """Tests the basic line type of: k:v|type"""
        assert ("k", 27, "kv", None) == p.parse_line("k:27|kv")

    def test_parses_flag(self):
        """Tests that lines with flags (@ parameters) can be parsed
        properly."""
        assert ("k", 27, "ms", 123456) == p.parse_line("k:27|ms|@123456")

    def test_parses_negative_value(self):
        """Tests that lines can contain negative numbers as values."""
        assert ("k", -27, "ms", None) == p.parse_line("k:-27|ms")

    def test_parses_float_value(self):
        """Tests that float values can be parsed."""
        assert ("k", 3.14, "ms", None) == p.parse_line("k:3.14|ms")

    def test_parses_float_flag(self):
        """Tests that float flags can be parsed."""
        assert ("k", 3, "ms", 0.1) == p.parse_line("k:3|ms|@0.1")

    def test_fails_no_value(self):
        """Tests that parsing fails for lines with no
        value (or key, depending on how you look at it)"""
        with pytest.raises(ValueError):
            p.parse_line("k|kv")

    def test_fails_no_type(self):
        """Tests that parsing fails for lines with no
        metric type."""
        with pytest.raises(ValueError):
            p.parse_line("k:27")

    def test_fails_negative_flag(self):
        """Tests that negative flags can not be parsed."""
        with pytest.raises(ValueError):
            p.parse_line("k:27|ms|@-24")

    def test_parse_multiple_lines(self):
        """
        Tests that multiple lines of messages can be parsed into an
        array of tuples.
        """
        message  = "\n".join(["k:1|ms", "j:2|kv"])
        expected = [("k", 1, "ms", None),
                    ("j", 2, "kv", None)]

        assert expected == p.parse_message(message)
