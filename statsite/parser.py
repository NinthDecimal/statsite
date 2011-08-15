"""
This module implements simple utility functions for
parsing incoming messages.
"""
import re

LINE_REGEX = re.compile("^([a-zA-Z0-9-_.]+):(-?[0-9.]+)\|([a-z]+)(?:\|@([0-9.]+))?$")
"""
Simple Regex used to match stats lines inside incoming messages.
"""

def parse_line(line):
    """
    Utility function to parse an incoming line in a message.

    Raises :exc:`ValueError` if the line is invalid or the
    message type if not valid.

    Returns a :class:`Metric` object of the proper subclass.
    """
    match = LINE_REGEX.match(line)
    if match is None:
        raise ValueError, "Invalid line: '%s'" % line

    key, value, metric_type, flag = match.groups()

    # Do type conversion to either float or int
    value = float(value) if "." in value else int(value)
    if flag is not None:
        flag = float(flag) if "." in flag else int(flag)

    # Return the metric object
    return (key, value, metric_type, flag)

