"""
Contains the base class for collectors as well as the built-in UDP
collector.
"""

import logging
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory

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
            if len(line) == 0:
                continue

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


class TCPCollector(Collector):
    """
    This is a collector which listens for TCP connections,
    spawns a thread for each one, parses incoming metrics,
    and adds them to the aggregator.
    """

    def __init__(self, host="0.0.0.0", port=8125, **kwargs):
        super(TCPCollector, self).__init__(kwargs["aggregator"])
        self.host = host
        self.port = int(port)
        self.logger = logging.getLogger("statsite.tcpcollector")

    def start(self):
        # Start listening and run the reactor
        factory = TCPCollectorHandler.getFactory()
        factory.collector = self
        reactor.listenTCP(self.port, factory,
                backlog=128, interface=self.host)
        self.logger.debug("TCPCollector starting")
        reactor.run()

    def shutdown(self):
        # Stop the reactor
        self.logger.debug("TCPCollector shutting down")
        reactor.stop()


class TCPCollectorHandler(LineOnlyReceiver):
    "Simple Twisted Protocol handler to parse incoming commands"
    delimiter = "\n"  # Use a plain newline, instead of \r\n
    MAX_LENGTH = 4 * 1024  # Change the line length to 4K
    LOGGER = logging.getLogger("statsite.tcpcollector")

    @classmethod
    def getFactory(self):
        factory = ServerFactory()
        factory.protocol = TCPCollectorHandler
        return factory

    def lineReceived(self, line):
        # Add the parsed metrics to the aggregator
        try:
            metrics = self.factory.collector._parse_metrics(line)
            self.factory.collector._add_metrics(metrics)
        except Exception:
            self.LOGGER.exception("Exception during processing TCP connection")

