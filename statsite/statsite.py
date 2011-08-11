"""
Contains the main Statsite class which is what should be instantiated
for running a server.
"""
import logging
import pprint
import threading

from . import __version__
from aggregator import DefaultAggregator
from collector import UDPCollector
from metrics_store import GraphiteStore

BANNER = """
Statsite v%(version)s

[components]
  . collector: %(collector_cls)s
  . aggregator: %(aggregator_cls)s
  . store:      %(store_cls)s

[configuration]
%(configuration)s
"""

class Statsite(object):
    """
    Statsite is the main entrypoint class for instantiating, configuring,
    and running a Statsite server.
    """

    DEFAULT_SETTINGS = {
        "flush_interval": 10,
        "aggregator": {},
        "collector": {},
        "store": {}
    }

    def __init__(self, settings={}, collector_cls=UDPCollector, aggregator_cls=DefaultAggregator,
                 store_cls=GraphiteStore):
        """
        Initializes a new Statsite server instance. All configuration
        must be done during instantiate. If configuration changes in the
        future, a new statsite class must be created.
        """
        super(Statsite, self).__init__()

        # Store the classes and settings
        self.aggregator_cls = aggregator_cls
        self.settings = dict(self.DEFAULT_SETTINGS.items() + settings.items())

        # Setup the logger
        self.logger = logging.getLogger("statsite.statsite")
        self.logger.info(BANNER % {
                "version": __version__,
                "collector_cls": collector_cls,
                "aggregator_cls": aggregator_cls,
                "store_cls": store_cls,
                "configuration": pprint.pformat(self.settings, width=60, indent=2)
        })

        # Setup the store
        self.logger.debug("Initializing metrics store: %s" % store_cls)
        self.store = store_cls(**self.settings["store"])

        # Setup the aggregator, provide the store
        self.settings["aggregator"]["metrics_store"] = self.store
        self.logger.debug("Initializing aggregator: %s" % aggregator_cls)
        self.aggregator = self._create_aggregator()

        # Setup the collector, provide the aggregator
        self.settings["collector"]["aggregator"] = self.aggregator
        self.logger.debug("Initializing collector: %s" % collector_cls)
        self.collector =  collector_cls(**self.settings["collector"])

        # Setup the timer default
        self.timer = None

    def start(self):
        """
        This starts the actual statsite server. This will run in a
        separate thread and return immediately.
        """
        self.logger.info("Statsite starting")
        self._reset_timer()
        self.collector.start()

    def shutdown(self):
        """
        This shuts down the server by gracefully exiting the flusher,
        aggregator, and collector. Exact behavior of "gracefully" exit
        is up to the various components used, but by default this
        will throw away any data received during the current flush
        period, rather than immediately flushing it, since this can cause
        inaccurate statistics.
        """
        self.logger.info("Statsite shutting down")
        if self.timer:
            self.timer.cancel()

        self.collector.shutdown()

    def _on_timer(self):
        """
        This is the callback called every flush interval, and is responsible
        for initiating the aggregator flush.
        """
        self._reset_timer()
        self._flush_and_switch_aggregator()

    def _flush_and_switch_aggregator(self):
        """
        This is called periodically to flush the aggregator and switch
        the collector to a new aggregator.
        """
        self.logger.debug("Flushing and switching aggregator...")

        # Create a new aggregator and tell the collection to begin using
        # it immediately.
        old_aggregator = self.aggregator
        self.aggregator = self._create_aggregator()
        self.collector.set_aggregator(self.aggregator)

        # Flush the old aggregator in it's own thread
        thread = threading.Thread(target=old_aggregator.flush)
        thread.start()

    def _create_aggregator(self):
        """
        Returns a new aggregator with the settings given at initialization.
        """
        return self.aggregator_cls(**self.settings["aggregator"])

    def _reset_timer(self):
        """
        Resets the flush timer.
        """
        if self.timer:
            self.timer.cancel()

        self.timer = threading.Timer(int(self.settings["flush_interval"]), self._on_timer)
        self.timer.start()
