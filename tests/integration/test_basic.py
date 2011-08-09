"""
Contains integration tests to test the basic functionality of
Statsite: simply collecting key/value pairs.
"""

import time
from tests.base import IntegrationBase

class TestBasic(IntegrationBase):
    def test_single_key_value(self, client, graphite):
        """
        Tests that basic key/value pairs are successfully flushed
        to Graphite.
        """
        key = "answer"
        value = 42
        timestamp = int(time.time())

        def check():
            message = "%s %s %s" % (key, value, timestamp)
            assert [message] == graphite.values

        client.send("%s:%s|kv|@%d" % (key, value, timestamp))
        self.after_flush_interval(check)
