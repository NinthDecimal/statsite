"""
Contains the main Statsite class which is what should be instantiated
for running a server.
"""
import threading

from aggregator import DefaultAggregator
from collector import UDPCollector
from metrics_store import GraphiteStore

class Statsite(threading.Thread):
    """
    Statsite is the main entrypoint class for instantiating, configuring,
    and running a Statsite server.
    """

    def __init__(self, settings={}, collector=UDPCollector, aggregator=DefaultAggregator,
                 store=GraphiteStore):
        """
        Initializes a new Statsite server instance. All configuration
        must be done during instantiate. If configuration changes in the
        future, a new statsite class must be created.
        """
        super(Statsite, self).__init__()

        # Setup some basic defaults
        settings.setdefault("aggregator", {})
        settings.setdefault("collector", {})
        settings.setdefault("store", {})

        # Setup the store
        self.store = store(**settings["store"])

        # Setup the aggregator, provide the store
        settings["aggregator"]["metrics_store"] = self.store
        self.aggregator = aggregator(**settings["aggregator"])

        # Setup the collector, provide the aggregator
        settings["collector"]["aggregator"] = self.aggregator
        self.collector =  collector(**settings["collector"])

    def run(self):
        """
        This starts the actual statsite server. This will run in a
        separate thread and return immediately.
        """
        self.collector.serve_forever()

    def shutdown(self):
        """
        This shuts down the server by gracefully exiting the flusher,
        aggregator, and collector. Exact behavior of "gracefully" exit
        is up to the various components used, but by default this
        will throw away any data received during the current flush
        period, rather than immediately flushing it, since this can cause
        inaccurate statistics.
        """
        self.collector.shutdown()

