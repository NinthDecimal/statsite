import SocketServer
import parser

class CollectorHandler(SocketServer.RequestHandler):
    """Simple handler that parses a UDP packet and adds the metrics to an aggregator"""
    def handle(self):
        mesg, socket = self.request
        metrics = parser.parse_message(mesg)
        self.server.aggregator.add_metrics(metrics)

class CollectorServer(SocketServer.UDPServer):
    """UDP listener that invokes the CollectorHandler for each packet"""
    allow_reuse_address = True

    def __init__(self,hostname,port,aggregator,handler=CollectorHandler):
        SocketServer.UDPServer.__init__(self,(hostname,port),handler)
        self.aggregator = aggregator

