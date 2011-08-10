import SocketServer
import parser
import metrics
import logging

class CollectorHandler(SocketServer.RequestHandler):
    """Simple handler that parses a UDP packet and adds the metrics to an aggregator"""
    def handle(self):
        # Get the raw metrics
        mesg, socket = self.request
        raw_metrics = parser.parse_message(mesg)

        # Convert to the metrics objects
        metric_lst = []
        for (key,value,metric_type,flag) in raw_metrics:
            if metric_type in metrics.METRIC_TYPES:
                # Create and store the metric object
                metric = metrics.METRIC_TYPE[metric_type](key,value,flag)
                metric_lst.append(metric)
            else:
                self.server.logger.error("Invalid metric type '%s' received! Dropping." % metric_type)

        # Add all the metrics to the aggregator
        self.server.aggregator.add_metrics(metrics)

class CollectorServer(SocketServer.UDPServer):
    """UDP listener that invokes the CollectorHandler for each packet"""
    allow_reuse_address = True

    def __init__(self,hostname,port,aggregator,handler=CollectorHandler):
        SocketServer.UDPServer.__init__(self,(hostname,port),handler)
        self.aggregator = aggregator
        self.logger = logging.getLogger("statsite.udpcollector")

