import logging

import trio

from kabomu.abstractions import IQuasiHttpServerTransport

from shared.SocketConnection import SocketConnection

class LocalhostTcpServerTransport(IQuasiHttpServerTransport):
    
    def __init__(self,
                 default_processing_options,
                 quasi_http_server,
                 port):
        self.default_processing_options = default_processing_options
        self.quasi_http_server  = quasi_http_server
        self.port = port
        self.cancel_scope = None

    async def start(self):
        #async def receiver(socket):
        #    await self.receive_connection(socket)
        cancel_scope = trio.CancelScope()
        self.cancel_scope = cancel_scope
        with cancel_scope:
            await trio.serve_tcp(self.receive_connection,
                self.port, host="::1")

    async def stop(self):
        cancel_scope = self.cancel_scope
        if cancel_scope:
            cancel_scope.cancel()
        with trio.move_on_after(1):
            pass

    async def receive_connection(self, socket):
        try:
            connection = SocketConnection(socket, None, None,
                                          self.default_processing_options)
            await self.quasi_http_server.accept_connection(connection)
        except:
            logging.warning("connection processing error", exc_info=1)
        
    async def release_connection(self, connection):
        await connection.release(None)

    def get_readable_stream(self, connection):
        return connection.socket
    
    def get_writable_stream(self, connection):
        return connection.socket