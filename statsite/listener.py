import socket
import logging

class UDPListener(object):
    def __init__(self, port, callback=None, host="0.0.0.0", max_packet_size=32768):
        """
        This class implements a simple UDP socket listener. It wraps
        a UDP socket and accepts incoming messages. It invokes a simple
        callback to handle the messages, or sub-classes can define a custom
        :func:`new_message()` implementation to customize handling.

        Raises :class:`ValueError` if any of the parameters are invalid.

        :Parameters:
            - `port` : The port to listen on.
            - `callback` (optional) : A callable reference that must be able to take
              a message and address tuple as an argument. It can return a boolean value
              indicating if the UDPListener should shutdown.
            - `host` (optional) : A hostname to listen on. Defaults to all interfaces.
            - `max_packet_size` (optional) : The maximum packet size to read. Defaults to 32K.
        """
        # Sanity check the inputs
        if not isinstance(port, int): raise ValueError, "Port must be an integer!"
        if port <= 0 or port >= 65536: raise ValueError, "Port out of range! Must be between 0 and 65536"
        if callback is not None and not callable(callback): raise ValueError, "Callback must be callable!"
        if not isinstance(host, (str, unicode)): raise ValueError, "Host must be a string!"
        if not isinstance(max_packet_size, int): raise ValueError, "Maximum packet size must be an integer!"
        if max_packet_size <= 0: raise ValueError, "Cannot set maximum packet size to non-postive value!"

        # Store the callback if there is one
        self.callback = callback

        # Store the max packet size
        self.max_packet_size = max_packet_size

        # Setup our socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))
        self.socket.setblocking(True)

        # Setup our logger
        self.logger = logging.getLogger("statsite.UDPListener.%s.%s" % (host, port))

    def listen(self):
        """
        Starts the :class:`UDPLister`, begins accepting messages. This function will block
        until the :class:`UDPListener` is told to shutdown by the callback function.
        """
        while True:
            # Wait for a message
            self.logger.debug("Waiting for incoming packet.")
            mesg, addr = self.socket.recvfrom(self.max_packet_size)
            self.logger.debug("Received packet from %s. Packet size: %d bytes." % (addr, len(mesg)))

            # Invoke a handler
            try:
                should_break = self.new_message(mesg, addr)
            except:
                self.logger.exception("Encountered exception invoking message handler!")
                should_break = False

            # Check if we should break
            if should_break: break

    def new_message(self, msg, addr):
        """
        This function is invoked by :func:`listen()` when a new message is accepted.
        The default behavior is to invoke the callback handler that was provided during
        initialization.
        """
        # Invoke our callback, otherwise log an error
        if self.callback:
            return self.callback(msg, addr)
        else:
            self.logger.warning("No callback set to handle incoming message. Dropping message.")
            return False


