"""
Contains the base class for collectors as well as the built-in UDP
collector.
"""

import logging
import socket
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
        self.logger = logging.getLogger("statsite.collector")
        self.aggregator = aggregator

    def start(self):
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

    def _parse_metrics(self, message):
        """
        Given a raw message of metrics split by newline characters, this will
        parse the metrics and return an array of metric objects.

        This will raise a :exc:`ValueError` if any metrics are invalid, unless
        ``ignore_errors`` is set to True.
        """
        results = []
        for line in message.split("\n"):
            # If the line is blank, we ignore it
            if len(line) == 0: continue

            # Parse the line, and skip it if its invalid
            try:
                (key, value, metric_type, flag) = parser.parse_line(line)
            except ValueError:
                self.logger.error("Invalid line syntax: %s" % line)
                continue

            # Create the metric and store it in our results
            if metric_type in metrics.METRIC_TYPES:
                # Create and store the metric object
                metric = metrics.METRIC_TYPES[metric_type](key, value, flag)
                results.append(metric)
            else:
                # Ignore the bad invalid metric, but log it
                self.logger.error("Invalid metric '%s' in line: %s" % (metric_type, line))

        return results

    def _add_metrics(self, metrics):
        """
        Adds the given array of metrics to the aggregator.
        """
        self.aggregator.add_metrics(metrics)

class UDPCollector(Collector):
    """
    This is a collector which listens for UDP packets, parses them,
    and adds them to the aggregator.
    """

    def __init__(self, host="0.0.0.0", port=8125, **kwargs):
        super(UDPCollector, self).__init__(**kwargs)

        self.server = UDPCollectorSocketServer((host, int(port)),
                                               UDPCollectorSocketHandler,
                                               collector=self)
        self.logger = logging.getLogger("statsite.udpcollector")

    def start(self):
        # Run the main server forever, blocking this thread
        self.logger.debug("UDPCollector starting")
        self.server.serve_forever()

    def shutdown(self):
        # Tell the main server to stop
        self.logger.debug("UDPCollector shutting down")
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
        self._setup_socket_buffers()

    def _setup_socket_buffers(self):
        "Increases the receive buffer sizes"
        # Try to set the buffer size to 4M, 2M, 1M, and 512K
        for buff_size in (4*1024**2,2*1024**2,1024**2,512*1024):
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buff_size)
                return
            except:
                pass

class UDPCollectorSocketHandler(SocketServer.BaseRequestHandler):
    """
    Simple handler that receives UDP packets, parses them, and adds
    them to the aggregator.
    """

    def handle(self):
        try:
            # Get the message
            message, _ = self.request

            # Add the parsed metrics to the aggregator
            metrics = self.server.collector._parse_metrics(message)
            self.server.collector._add_metrics(metrics)
        except Exception, e:
            self.server.collector.logger.exception("Exception during processing UDP packet")
