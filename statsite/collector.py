"""
Contains the base class for collectors as well as the built-in UDP
collector.
"""

import logging
import SocketServer

import metrics
import parser

class Collector(object):
    """
    Collectors should inherit from this class, which provides the
    necessary interface and helpers for implementing a collector.
    """

    def __init__(self, aggregator):
        """
        Initializes a collector. Subclasses can override this with custom
        parameters if they want, but they _must_ call the superclass
        init method.
        """
        self.aggregator = aggregator

    def run(self):
        """
        This method must be implemented by collectors, and is called
        when the collector should be started. This method should block
        forever while the collector runs.
        """
        raise NotImplementedError("run must be implemented")

    def shutdown(self):
        """
        This method will be called by a second thread to notify the
        collector to shutdown, which it should immediately and gracefully.
        """
        raise NotImplementedError("shutdown must be implemented")

    def set_aggregator(self, aggregator):
        """
        This method may be periodically called to change the aggregator
        underneath the collector object.
        """
        self.aggregator = aggregator

    def parse_metrics(self, message, ignore_errors=False):
        """
        Given a raw message of metrics split by newline characters, this will
        parse the metrics and return an array of metric objects.

        This will raise a :exc:`ValueError` if any metrics are invalid, unless
        ``ignore_errors`` is set to True.
        """
        results = []
        for (key, value, metric_type, flag) in parser.parse_message(message):
            if metric_type in metrics.METRIC_TYPES:
                # Create and store the metric object
                metric = metrics.METRIC_TYPES[metric_type](key, value, flag)
                results.append(metric)
            else:
                # TODO: Log here?
                if not ignore_errors:
                    raise ValueError("Invalid metric received")

        return results

    def add_metrics(self, metrics):
        """
        Adds the given array of metrics to the aggregator.
        """
        self.aggregator.add_metrics(metrics)

class UDPCollector(Collector):
    """
    This is a collector which listens for UDP packets, parses them,
    and adds them to the aggregator.
    """

    def __init__(self, host, port, **kwargs):
        super(UDPCollector, self).__init__(**kwargs)

        self.server = UDPCollectorSocketServer((host, port), UDPCollectorSocketHandler)
        self.logger = logging.getLogger("statsite.udpcollector")

    def run(self):
        # Run the main server forever, blocking this thread
        self.server.serve_forever()

    def shutdown(self):
        # Tell the main server to stop
        self.server.shutdown()

class UDPCollectorSocketServer(SocketServer.UDPServer):
    """
    The SocketServer implementation for the UDP collector.
    """

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        self.collector = kwargs["collector"]
        del kwargs["collector"]

        SocketServer.UDPServer.__init__(self, *args, **kwargs)

class UDPCollectorSocketHandler(SocketServer.BaseRequestHandler):
    """
    Simple handler that receives UDP packets, parses them, and adds
    them to the aggregator.
    """

    def handle(self):
        # Get the message
        message, _ = self.request

        # Add the parsed metrics to the aggregator
        metrics = self.server.collector.parse_metrics(message, ignore_errors=True)
        self.server.collector.add_metrics(metrics)
