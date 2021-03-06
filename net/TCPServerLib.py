"""TCPServerLib.py

This module implements a threaded tcp socket server and request handler for To-Do.
"""
import json
import os
import socketserver
import sys
import time

from core import core
from core.core import SyncOperations
from core.Logger import Logger
from crypto.AESCipher import AESCipher

logger = Logger(__name__)


class DataBaseServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded tcp server."""

    allow_reuse_address = True


class TCPRequestHandler(socketserver.StreamRequestHandler):
    """Socket server request handler."""

    def __init__(self, request, client_address, server):
        """Initialize request handler."""
        self.aes_cipher = AESCipher(core.options["key"])
        self.buf_size = 4096
        self.peer_name = None
        self.host = None
        self.data = None
        self.encrypted_header = None
        self.encrypted_data = None
        self.decrypted_data = None
        self.command = None
        self.encrypted_reply = None
        super().__init__(request, client_address, server)

    def process_request(self):
        """Process a request."""
        self.encrypted_data = self.request.recv(self.buf_size)
        self.decrypted_data = self.aes_cipher.decrypt(self.encrypted_data)
        self.command = self.decrypted_data.decode("utf-8")

        if self.command == SyncOperations["PULL_REQUEST"].name:
            self.pull()
        elif self.command == SyncOperations["PUSH_REQUEST"].name:
            self.push()
        else:
            pass

    def pull(self):
        """Pull to-do lists from remote host."""
        logger.log.info(f"received PULL_REQUEST from {self.peer_name}")
        if not core.options["pull"]:
            logger.log.info("PULL_REQUEST denied")
            self.encrypted_reply = self.aes_cipher.encrypt(
                SyncOperations["REJECT"].name
            )
            self.request.send(self.encrypted_reply)
            return

        if os.path.exists(core.lists_fn):
            self.data = ""
            with open(core.lists_fn, encoding="utf-8") as f:
                for line in f:
                    self.data += line

        if self.data is not None:
            logger.log.info("PULL_REQUEST ACCEPTED")
            self.encrypted_reply = self.aes_cipher.encrypt(
                SyncOperations["ACCEPT"].name
            )
            self.request.sendall(self.encrypted_reply)
            time.sleep(1)
            self.send_size_header()
        else:
            self.encrypted_reply = self.aes_cipher.encrypt(
                SyncOperations["NO_DATA"].name
            )
            self.request.send(self.encrypted_reply)

    def send_size_header(self):
        """Send the size of the to-do lists."""
        size = sys.getsizeof(self.data)
        self.encrypted_header = self.aes_cipher.encrypt(str(size))
        self.request.sendall(self.encrypted_header)
        time.sleep(1)
        self.send_data()

    def send_data(self):
        """Send to-do list data."""
        try:
            serialized = json.dumps(self.data)
        except OSError as e:
            logger.log.exception(e)
            return False, e
        self.encrypted_data = self.aes_cipher.encrypt(serialized)
        self.request.sendall(self.encrypted_data)

    def push(self):
        """Push to-do lists to remote hosts."""
        logger.log.info(f"PUSH_REQUEST from {self.peer_name}")
        if not core.options["push"]:
            logger.log.info("PUSH_REQUEST denied")
            self.encrypted_reply = self.aes_cipher.encrypt(
                SyncOperations["REJECT"].name
            )
            self.request.send(self.encrypted_reply)
            return
        logger.log.info("PUSH_REQUEST accepted")
        self.encrypted_reply = self.aes_cipher.encrypt(SyncOperations["ACCEPT"].name)
        self.request.send(self.encrypted_reply)
        self.host = (self.peer_name[0], core.options["port"])
        core.db.sync_pull(self.host)

    def handle(self):
        """Handle requests."""
        self.peer_name = self.request.getpeername()
        self.process_request()
