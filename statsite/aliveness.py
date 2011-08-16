"""
Contains classes which handle the TCP aliveness check.
"""

import logging
import SocketServer

LOGGER = logging.getLogger("statsite.aliveness")

class AlivenessHandler(SocketServer.BaseRequestHandler):
    """
    This is the TCP handler which responds to any aliveness checks
    to Statsite. This handler simply responds to every packet received
    with the contents of "YES" (all caps). This is so that in the future
    if smarter checks are done, "NO" could possibly respond as well.
    """

    def handle(self):
        LOGGER.debug("Aliveness check from: %s" % self.client_address[0])
        self.request.send("YES")
