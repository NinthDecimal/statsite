"""
Contains a fake Graphite stub which can be used to test what
Statsite is sending to Graphite.
"""

import SocketServer

class GraphiteServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    A fake Graphite server. This server stores all the messages received
    by Graphite in the `messages` list.
    """

    allow_reuse_address = True

    def __init__(self, address, *args, **kwargs):
        SocketServer.TCPServer.__init__(self, address, *args, **kwargs)

        # Store the host/port data and messages for users of the server
        self.host, self.port = address
        self.messages = []

class GraphiteHandler(SocketServer.StreamRequestHandler):
    """
    TCP handler for the fake graphite server. This receives messages
    and aggregates them on the server.
    """

    def handle(self):
        # Read all the lines from the input and append them to the
        # messages the server has seen. This is how we "fake" a
        # Graphite server. The tests are simply expected to test the
        # order and values of the messages themselves.
        while True:
            line = self.rfile.readline()
            if not line:
                break

            self.server.messages.append(line)
