import socket
import threading
import logging

class GraphiteStore(object):
    def __init__(self,host,port,attempts=3):
        """
        Implements a metrics store interface that allows metrics to
        be persisted to Graphite. Raises a :class:`ValueError` on bad arguments.

        :Parameters:
            - `host` : The hostname of the graphite server.
            - `port` : The port of the graphite server
            - `attempts` (optional) : The number of re-connect retries before failing.
        """
        if not isinstance(host, (str,unicode)): raise ValueError, "Host must be a string!"
        if not isinstance(port, int): raise ValueError, "Port must be an integer!"
        if port <= 0: raise ValueError, "Port must be positive!"
        if attempts <= 1: raise ValueError, "Must have at least 1 attempt!"

        self.host = host
        self.port = port
        self.attempts = attempts
        self.sock_lock = threading.Lock()
        self.sock = self._create_socket()
        self.logger = logging.getLogger("statsite.graphite")

    def _create_socket(self):
        """Creates a socket and connects to the graphite server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host,self.port))
        return sock

    def _write_metric(self, metric):
        """Tries to write a string to the socket, reconnecting on any errors"""
        for attempt in xrange(self.attempts):
            try:
                self.sock.send(metric)
                break
            except socket.error:
                self.logger.exception("Failed to flush to Graphite!")
                self.sock = self._create_socket()

    def metrics_store(self, metrics):
        """
        Flushes the metrics provided to Graphite.

       :Parameters:
        - `metrics` : A list of (key,value,timestamp) tuples.
        """
        # Construct the output
        data = "\n".join(["%s %s %s" % metric for metric in metrics]) + "\n"

        # Serialize writes to the socket
        self.sock_lock.acquire()
        try:
            self._write_metric(data)
        except:
            self.logger.exception("Failed to write out the metrics!")
        finally:
            self.sock_lock.release()


