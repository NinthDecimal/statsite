"""
Contains a fake Graphite stub which can be used to test what
Statsite is sending to Graphite.
"""

import SocketServer

class GraphiteServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, *args, **kwargs):
        SocketServer.TCPServer.__init__(self, *args, **kwargs)

        self.values = []

class GraphiteHandler(SocketServer.StreamRequestHandler):
    """
    TCP handler for the fake graphite server. This receives messages
    and aggregates them on the server.
    """

    def handle(self):
        pass
