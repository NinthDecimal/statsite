"""
Contains the basic classes for test classes.
"""

import socket
import time
import threading
from graphite import GraphiteServer, GraphiteHandler

class IntegrationBase(object):
    """
    This is the base class for integration tests of Statsite.
    """

    DEFAULT_INTERVAL = 1
    "The default flush interval for Statsite servers."

    current_statsite_port = 16000
    current_graphite_port = 12000
    """The current statsite/graphite ports to use when instantiating
    servers. These will be incremented."""

    def pytest_funcarg__client(self, request):
        """
        This creates a pytest funcarg for a client to a running Statsite
        server.
        """
        host = "localhost"
        port = IntegrationBase.current_statsite_port
        IntegrationBase.current_statsite_port += 1

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
        port = IntegrationBase.current_graphite_port
        IntegrationBase.current_graphite_port += 1

        # Instantiate the actual TCP server
        server = GraphiteServer(("localhost", port), GraphiteHandler)
        server.allow_reuse_address = True

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
