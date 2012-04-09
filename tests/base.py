"""
Contains the basic classes for test classes.
"""

import errno
import random
import socket
import tempfile
import time
import threading
import os
import os.path
import shutil
import subprocess

from graphite import GraphiteServer, GraphiteHandler
from helpers import DumbAggregator, DumbMetricsStore


class TestBase(object):
    """
    This is the base class for unit tests of statsite.
    """

    DEFAULT_INTERVAL = 1
    "The default flush interval for Statsite servers."

    def pytest_funcarg__aggregator(self, request):
        """
        This creates a fake aggregator instance and returns it.
        """
        return DumbAggregator(request.getfuncargvalue("metrics_store"), metrics_settings={})

    def pytest_funcarg__metrics_store(self, request):
        """
        This creates a fake metrics store instance and returns it.
        """
        return DumbMetricsStore()

    def pytest_funcarg__servers(self, request):
        """
        This creates a pytest funcarg for a client to a running Statsite
        server.
        """
        # Instantiate a graphite server
        graphite = request.getfuncargvalue("graphite")

        # Instantiate server
        # Instantiate server
        settings = {
            "flush_interval": self.DEFAULT_INTERVAL,
            "aliveness_check": {
                "enabled": 0,
            },
            "collector": {
                "host": "localhost",
                "port": graphite.port + 1
             },
            "store": {
                "host": "localhost",
                "port": graphite.port,
                "prefix": "foobar"
             }
        }

        # Take override settings if they exist
        if hasattr(request.function, "statsite_settings"):
            settings = dict(settings.items() + request.function.statsite_settings.items())

        # Flatten the settings
        flat_settings = {}
        for key, val in settings.iteritems():
            if isinstance(val, dict):
                for sub_key, sub_val in val.iteritems():
                    flat_settings[key + "." + sub_key] = sub_val
            else:
                flat_settings[key] = val

        config = """[statsite]
flush_interval = %(flush_interval)d

[aliveness_check]
enabled = %(aliveness_check.enabled)s

[collector]
host = %(collector.host)s
port = %(collector.port)d

[store]
host = %(store.host)s
port = %(store.port)d
prefix = %(store.prefix)s
""" % flat_settings

        # Write the configuration
        tmpdir = tempfile.mkdtemp()
        config_path = os.path.join(tmpdir, "config.cfg")
        open(config_path, "w").write(config)

        # Start the process
        proc = subprocess.Popen("statsite --config %s" % config_path, shell=True)
        proc.poll()
        assert proc.returncode is None

        # Define a cleanup handler
        def cleanup():
            try:
                proc.terminate()
                proc.wait()
                shutil.rmtree(tmpdir)
            except:
                pass
        request.addfinalizer(cleanup)

        # Take override settings if they exist
        if hasattr(request.function, "statsite_settings"):
            settings = dict(settings.items() + request.function.statsite_settings.items())

        # Create the TCP client connected to the statsite server
        time.sleep(0.1)
        start = time.time()
        client = None
        while time.time() - start < 5:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((settings["collector"]["host"], settings["collector"]["port"]))
                break
            except:
                # Retry
                client = None
                pass

        if client is None:
            raise Exception("Timed out trying to connect!")

        class Server(object):
            pass

        srv = Server()
        srv.settings = settings

        return (client, srv, graphite)

    def pytest_funcarg__servers_tcp(self, request):
        """
        This creates a pytest funcarg for a client to a running Statsite
        server. In this configuration, the server listens on TCP and the client
        is a TCP socket.
        """
        return self.pytest_funcarg__servers(request)

    def pytest_funcarg__graphite(self, request):
        """
        This creates a pytest funcarg for a fake Graphite server.
        """
        host = "localhost"

        # Instantiate the actual TCP server by trying random ports
        # to make sure they don't stomp on each other.
        while True:
            try:
                port = random.randint(2048, 32768)
                server = GraphiteServer((host, port), GraphiteHandler)
                break
            except socket.error, e:
                if e[0] != errno.EADDRINUSE:
                    raise e

        # Create the thread to run the server and start it up
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        # Add a finalizer to make sure our server is properly
        # shutdown after every test
        request.addfinalizer(lambda: server.shutdown())

        return server

    def pytest_funcarg__tempfile(self, request):
        return tempfile.NamedTemporaryFile()

    def after_flush_interval(self, callback, interval=None):
        """
        This waits the configured flush interval prior to calling
        the callback.
        """
        # Wait the given interval
        interval = self.DEFAULT_INTERVAL if interval is None else interval
        interval += 1
        time.sleep(interval)

        # Call the callback
        callback()
