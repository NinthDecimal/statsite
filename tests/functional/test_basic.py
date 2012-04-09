"""
Contains integration tests to test the basic functionality of
Statsite: simply collecting key/value pairs.
"""

import time
from tests.base import TestBase

class TestBasic(TestBase):
    def test_single_key_value(self, servers):
        """
        Tests that basic key/value pairs are successfully flushed
        to Graphite.
        """
        client, server, graphite = servers

        key = "answer"
        value = 42
        timestamp = int(time.time())

        def check():
            message = "%s.kv.%s %s %s" % (server.settings["store"]["prefix"], key, value, timestamp)
            assert [message] == graphite.messages

        client.send("%s:%s|kv|@%d\n" % (key, value, timestamp))
        self.after_flush_interval(check)

    def test_multiple_key_value(self, servers):
        """
        Tests that multiple basic key/value pairs can be send to
        Statsite, and that they will all be flushed during the flush
        interval.
        """
        client, server, graphite = servers
        prefix = server.settings["store"]["prefix"]

        messages = [("answer", 42, int(time.time())),
                    ("another", 84, int(time.time()) - 5)]

        # The test method
        def check():
            raw_messages = ["%s.kv.%s %s %s" % (prefix,k,v,ts) for k,v,ts in messages]
            assert raw_messages == graphite.messages

        # Send all the messages
        for message in messages:
            client.send("%s:%s|kv|@%d\n" % message)

        # Verify they were properly received
        self.after_flush_interval(check)

    def test_clears_after_flush_interval(self, servers):
        """
        Tests that after the flush interval, the data is cleared and
        only new data is sent to the graphite server.
        """
        client, server, graphite = servers
        prefix = server.settings["store"]["prefix"]

        messages = [("k", 1, int(time.time())), ("j", 2, int(time.time()))]

        # Send the first message and wait the flush interval
        client.send("%s:%s|kv|@%d\n" % messages[0])
        self.after_flush_interval(lambda: None)

        # Send the second message
        client.send("%s:%s|kv|@%d\n" % messages[1])

        # Check the results after the flush interval
        def check():
            raw_messages = ["%s.kv.%s %s %s" % (prefix,k,v,ts) for k,v,ts in messages]
            assert raw_messages == graphite.messages

        self.after_flush_interval(check)

    def test_no_data_before_flush_interval(self, servers):
        """
        Tests that the data is flushed on the flush interval.
        """
        statsite_init_time = time.time()
        client, server, graphite = servers

        # Send some data to graphite and wait the flush interval
        client.send("k:1|kv\n")
        self.after_flush_interval(lambda: None)

        # Verify that the data was received at least after the
        # flush interval
        duration = graphite.last_receive - statsite_init_time
        epsilon  = 0.1
        assert abs(int(self.DEFAULT_INTERVAL) - duration) <= epsilon


class TestBasicTCP(TestBase):
    def test_single_key_value(self, servers_tcp):
        """
        Tests that basic key/value pairs are successfully flushed
        to Graphite.
        """
        client, server, graphite = servers_tcp

        key = "answer"
        value = 42
        timestamp = int(time.time())

        def check():
            message = "%s.kv.%s %s %s" % (server.settings["store"]["prefix"], key, value, timestamp)
            assert [message] == graphite.messages

        client.sendall("%s:%s|kv|@%d\n" % (key, value, timestamp))
        self.after_flush_interval(check)

    def test_multiple_key_value(self, servers_tcp):
        """
        Tests that multiple basic key/value pairs can be send to
        Statsite, and that they will all be flushed during the flush
        interval.
        """
        client, server, graphite = servers_tcp
        prefix = server.settings["store"]["prefix"]

        messages = [("answer", 42, int(time.time())),
                    ("another", 84, int(time.time()) - 5)]

        # The test method
        def check():
            raw_messages = ["%s.kv.%s %s %s" % (prefix,k,v,ts) for k,v,ts in messages]
            assert raw_messages == graphite.messages

        # Send all the messages
        for message in messages:
            client.sendall("%s:%s|kv|@%d\n" % message)

        # Verify they were properly received
        self.after_flush_interval(check)

    def test_clears_after_flush_interval(self, servers_tcp):
        """
        Tests that after the flush interval, the data is cleared and
        only new data is sent to the graphite server.
        """
        client, server, graphite = servers_tcp
        prefix = server.settings["store"]["prefix"]

        messages = [("k", 1, int(time.time())), ("j", 2, int(time.time()))]

        # Send the first message and wait the flush interval
        client.sendall("%s:%s|kv|@%d\n" % messages[0])
        self.after_flush_interval(lambda: None)

        # Send the second message
        client.sendall("%s:%s|kv|@%d\n" % messages[1])

        # Check the results after the flush interval
        def check():
            raw_messages = ["%s.kv.%s %s %s" % (prefix,k,v,ts) for k,v,ts in messages]
            assert raw_messages == graphite.messages

        self.after_flush_interval(check)

    def test_no_data_before_flush_interval(self, servers_tcp):
        """
        Tests that the data is flushed on the flush interval.
        """
        statsite_init_time = time.time()
        client, server, graphite = servers_tcp

        # Send some data to graphite and wait the flush interval
        client.sendall("k:1|kv\n")
        self.after_flush_interval(lambda: None)

        # Verify that the data was received at least after the
        # flush interval
        duration = graphite.last_receive - statsite_init_time
        epsilon  = 0.1
        assert abs(int(self.DEFAULT_INTERVAL) - duration) <= epsilon

