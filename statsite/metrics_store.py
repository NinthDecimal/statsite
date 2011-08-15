"""
Contains the base metrics store class and default metrics store class.
"""

import socket
import threading
import logging

class MetricsStore(object):
    """
    This is the base class for all metric stores. There is only one
    main method that metric stores must implement: :meth:`flush()`
    which is called from time to time to flush data out to the
    backing store.

    Metrics stores _must_ be threadsafe, since :meth:`flush()` could
    potentially be called by multiple flushing aggregators.
    """

    def flush(self, metrics):
        """
        This method is called by aggregators when flushing data.
        This must be thread-safe.
        """
        raise NotImplementedError("flush not implemented")

class GraphiteStore(MetricsStore):
    def __init__(self, host="localhost", port=2003, prefix="statsite", attempts=3):
        """
        Implements a metrics store interface that allows metrics to
        be persisted to Graphite. Raises a :class:`ValueError` on bad arguments.

        :Parameters:
            - `host` : The hostname of the graphite server.
            - `port` : The port of the graphite server
            - `prefix` (optional) : A prefix to add to the keys. Defaults to 'statsite'
            - `attempts` (optional) : The number of re-connect retries before failing.
        """
        # Convert the port to an int since its coming from a configuration file
        port = int(port)

        if port <= 0: raise ValueError, "Port must be positive!"
        if attempts <= 1: raise ValueError, "Must have at least 1 attempt!"

        self.host = host
        self.port = port
        self.prefix = prefix
        self.attempts = attempts
        self.sock_lock = threading.Lock()
        self.sock = self._create_socket()
        self.logger = logging.getLogger("statsite.graphitestore")

    def flush(self, metrics):
        """
        Flushes the metrics provided to Graphite.

       :Parameters:
        - `metrics` : A list of (key,value,timestamp) tuples.
        """
        # Construct the output
        data = "\n".join(["%s.%s %s %d" % (self.prefix,k,v,ts) for k,v,ts in metrics]) + "\n"

        # Serialize writes to the socket
        self.sock_lock.acquire()
        try:
            self._write_metric(data)
        except:
            self.logger.exception("Failed to write out the metrics!")
        finally:
            self.sock_lock.release()

    def close(self):
        """
        Closes the connection. The socket will be recreated on the next
        flush.
        """
        self.sock.close()

    def _create_socket(self):
        """Creates a socket and connects to the graphite server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host,self.port))
        return sock

    def _write_metric(self, metric):
        """Tries to write a string to the socket, reconnecting on any errors"""
        for attempt in xrange(self.attempts):
            try:
                self.sock.sendall(metric)
                return
            except socket.error:
                self.logger.exception("Error while flushing to graphite. Reattempting...")
                self.sock = self._create_socket()

        self.logger.critical("Failed to flush to Graphite! Gave up after %d attempts." % self.attempts)
