"""
Contains the basic classes for test classes.
"""

import errno
import random
import socket
import time
import threading
from graphite import GraphiteServer, GraphiteHandler
from helpers import DumbAggregator, DumbMetricsStore

class TestBase(object):
    """
    This is the base class for unit tests of statsite.
    """

    DEFAULT_INTERVAL = 1
    "The default flush interval for Statsite servers."

    def pytest_funcarg__aggregator(self, request):
        """
        This creates a fake aggregator instance and returns it.
        """
        return DumbAggregator()

    def pytest_funcarg__metrics_store(self, request):
        """
        This creates a fake metrics store instance and returns it.
        """
        return DumbMetricsStore()

    def pytest_funcarg__client(self, request):
        """
        This creates a pytest funcarg for a client to a running Statsite
        server.
        """
        host = "localhost"
        port = 12000

        # TODO: Instantiate server

        # Create the UDP client connected to the statsite server
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.connect((host, port))

        return client

    def pytest_funcarg__graphite(self, request):
        """
        This creates a pytest funcarg for a fake Graphite server.
        """
        host = "localhost"

        # Instantiate the actual TCP server by trying random ports
        # to make sure they don't stomp on each other.
        while True:
            try:
                port = random.randint(2048, 32768)
                server = GraphiteServer((host, port), GraphiteHandler)
                break
            except socket.error, e:
                if e[0] != errno.EADDRINUSE:
                    raise e

        # Create the thread to run the server and start it up
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        # Add a finalizer to make sure our server is properly
        # shutdown after every test
        request.addfinalizer(lambda: server.shutdown())

        return server

    def after_flush_interval(self, callback, interval=None):
        """
        This waits the configured flush interval prior to calling
        the callback.
        """
        # Wait the given interval
        interval = self.DEFAULT_INTERVAL if interval is None else interval
        time.sleep(interval)

        # Call the callback
        callback()
