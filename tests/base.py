"""
Contains the basic classes for test classes.
"""

import errno
import random
import socket
import tempfile
import time
import threading

from statsite.statsite import Statsite

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
        return DumbAggregator(request.getfuncargvalue("metrics_store"), metrics_settings={})

    def pytest_funcarg__metrics_store(self, request):
        """
        This creates a fake metrics store instance and returns it.
        """
        return DumbMetricsStore()

    def pytest_funcarg__servers(self, request):
        """
        This creates a pytest funcarg for a client to a running Statsite
        server.
        """
        # Instantiate a graphite server
        graphite = request.getfuncargvalue("graphite")

        # Instantiate server
        settings = {
            "flush_interval": self.DEFAULT_INTERVAL,
            "collector": {
                "host": "localhost",
                "port": graphite.port + 1
             },
            "store": {
                "host": "localhost",
                "port": graphite.port,
                "prefix": "foobar"
             }
        }

        # Take override settings if they exist
        if hasattr(request.function, "statsite_settings"):
            settings = dict(settings.items() + request.function.statsite_settings.items())

        server = Statsite(settings)
        thread = threading.Thread(target=server.start)
        thread.start()

        # Add a finalizer to make sure the server is properly shutdown
        request.addfinalizer(lambda: server.shutdown())

        # Create the UDP client connected to the statsite server
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.connect((settings["collector"]["host"], settings["collector"]["port"]))

        return (client, server, graphite)

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

    def pytest_funcarg__tempfile(self, request):
        return tempfile.NamedTemporaryFile()

    def after_flush_interval(self, callback, interval=None):
        """
        This waits the configured flush interval prior to calling
        the callback.
        """
        # Wait the given interval
        interval = self.DEFAULT_INTERVAL if interval is None else interval
        interval += 0.5
        time.sleep(interval)

        # Call the callback
        callback()
