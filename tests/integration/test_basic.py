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
            assert [message] == graphite.messages

        client.send("%s:%s|kv|@%d" % (key, value, timestamp))
        self.after_flush_interval(check)

    def test_multiple_key_value(self, client, graphite):
        """
        Tests that multiple basic key/value pairs can be send to
        Statsite, and that they will all be flushed during the flush
        interval.
        """
        messages = [("answer", 42, int(time.time())),
                    ("another", 84, int(time.time()) - 5)]

        # The test method
        def check():
            raw_messages = ["%s %s %s" % message for message in messages]
            assert raw_messages == graphite.messages

        # Send all the messages
        for message in messages:
            client.send("%s:%s|kv|@%d" % message)

        # Verify they were properly received
        self.after_flush_interval(check)
