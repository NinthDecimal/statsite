"""
Contains tests to test the aliveness check of Statsite.
"""

import socket
import time
from tests.base import TestBase
from tests.helpers import statsite_settings

class TestBasic(TestBase):
    @statsite_settings({
        "aliveness_check": {
            "enabled": True
        }
    })
    def test_default_aliveness(self, servers):
        """
        Tests that the default aliveness check works.
        """
        socket = self._socket()
        socket.sendall("hello?")
        data = socket.recv(1024)
        socket.close()

        assert "YES" == data

    def _socket(self, host="localhost", port=8325):
        """
        Returns a TCP socket to talk to the aliveness check.
        """
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set a timeout so that a proper exception is raised if things
        # take too long
        sock.settimeout(1.0)

        # Connect to server and send data
        sock.connect((host, port))

        return sock
