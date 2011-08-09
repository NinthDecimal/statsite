"""
Contains the main Statsite class which is what should be instantiated
for running a server.
"""

class Statsite(object):
    """
    Statsite is the main entrypoint class for instantiating, configuring,
    and running a Statsite server.
    """

    def __init__(self, collector, aggregator, flusher, settings):
        """
        Initializes a new Statsite server instance. All configuration
        must be done during instantiate. If configuration changes in the
        future, a new statsite class must be created.
        """
        self.collector =  collector(settings["collector"])
        self.aggregator = aggregator(settings["aggregator"])
        self.flusher    = flusher(settings["flusher"])

    def start(self):
        """
        This starts the actual statsite server. This will run in a
        separate thread and return immediately.
        """
        # TODO: These need to go into separate threads
        self.flusher.start()
        self.aggregator.start(flusher=self.flusher)
        self.collector.start(aggregator=self.aggregator)

    def shutdown(self):
        """
        This shuts down the server by gracefully exiting the flusher,
        aggregator, and collector. Exact behavior of "gracefully" exit
        is up to the various components used, but by default this
        will throw away any data received during the current flush
        period, rather than immediately flushing it, since this can cause
        inaccurate statistics.
        """
        pass
