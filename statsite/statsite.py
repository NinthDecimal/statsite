"""
Contains the main Statsite class which is what should be instantiated
for running a server.
"""
import logging
import pprint
import SocketServer
import threading

from . import __version__
from aggregator import DefaultAggregator
from aliveness import AlivenessHandler
from collector import UDPCollector
from metrics_store import GraphiteStore
from util import deep_merge, resolve_class_string

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
        "aggregator": {
            "class": "aggregator.DefaultAggregator"
        },
        "aliveness_check": {
            "enabled": False,
            "host": "0.0.0.0",
            "port": 8325
        },
        "collector": {
            "class": "collector.UDPCollector"
        },
        "store": {
            "class": "metrics_store.GraphiteStore"
        },
        "metrics": {}
    }

    def __init__(self, settings={}):
        """
        Initializes a new Statsite server instance. All configuration
        must be done during instantiate. If configuration changes in the
        future, a new statsite class must be created.
        """
        super(Statsite, self).__init__()

        # Deep merge the default settings with the given settings
        self.settings = deep_merge(self.DEFAULT_SETTINGS, settings)

        # Resolve the classes for each component
        for component in ["aggregator", "collector", "store"]:
            key   = "_%s_cls" % component
            value = resolve_class_string(self.settings[component]["class"])

            # Delete the class from the settings, since the settings are also
            # used for initialization, and components don't expect "class"
            # kwarg.
            del self.settings[component]["class"]

            # Set the attribute on ourself for use everywhere else
            setattr(self, key, value)

        # Setup the logger
        self.logger = logging.getLogger("statsite.statsite")
        self.logger.info(BANNER % {
                "version": __version__,
                "collector_cls": self._collector_cls,
                "aggregator_cls": self._aggregator_cls,
                "store_cls": self._store_cls,
                "configuration": pprint.pformat(self.settings, width=60, indent=2)
        })

        # Setup the store
        self.logger.debug("Initializing metrics store: %s" % self._store_cls)
        self.store = self._store_cls(**self.settings["store"])

        # Setup the aggregator, provide the store
        self.settings["aggregator"]["metrics_store"] = self.store
        self.logger.debug("Initializing aggregator: %s" % self._aggregator_cls)
        self.aggregator = self._create_aggregator()

        # Setup the collector, provide the aggregator
        self.settings["collector"]["aggregator"] = self.aggregator
        self.logger.debug("Initializing collector: %s" % self._collector_cls)
        self.collector = self._collector_cls(**self.settings["collector"])

        # Setup defaults
        self.aliveness_check = None
        self.timer = None

    def start(self):
        """
        This starts the actual statsite server. This will run in a
        separate thread and return immediately.
        """
        self.logger.info("Statsite starting")
        self._reset_timer()

        if self.settings["aliveness_check"]["enabled"]:
            self._enable_aliveness_check()

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

        self._disable_aliveness_check()
        self.collector.shutdown()

    def _enable_aliveness_check(self):
        """
        This enables the TCP aliveness check, which is useful for tools
        such as Monit, Nagios, etc. to verify that Statsite is still
        alive.
        """
        if self.aliveness_check:
            self.aliveness_check.shutdown()

        self.logger.debug("Aliveness check starting")

        # Settings
        host = self.settings["aliveness_check"]["host"]
        port = int(self.settings["aliveness_check"]["port"])

        # Create the server
        self.aliveness_check = SocketServer.TCPServer((host, port), AlivenessHandler)

        # Run the aliveness check in a thread
        thread = threading.Thread(target=self.aliveness_check.serve_forever)
        thread.daemon = True
        thread.start()

    def _disable_aliveness_check(self):
        """
        This shuts down the TCP aliveness check.
        """
        self.logger.debug("Aliveness check stopping")
        if self.aliveness_check:
            self.aliveness_check.shutdown()
            self.aliveness_check = None

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
        thread.daemon = True
        thread.start()

    def _create_aggregator(self):
        """
        Returns a new aggregator with the settings given at initialization.
        """
        return self._aggregator_cls(metrics_settings=self.settings["metrics"], **self.settings["aggregator"])

    def _reset_timer(self):
        """
        Resets the flush timer.
        """
        if self.timer:
            self.timer.cancel()

        self.timer = threading.Timer(int(self.settings["flush_interval"]), self._on_timer)
        self.timer.start()
