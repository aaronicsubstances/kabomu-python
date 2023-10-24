import trio

from kabomu.abstractions import IQuasiHttpServerTransport

from SocketConnection import SocketConnection

class LocalhostTcpServerTransport(IQuasiHttpServerTransport):
    
    def __init__(self,
                 default_processing_options,
                 quasi_http_server,
                 port):
        self.default_processing_options = default_processing_options
        self.quasi_http_server  = quasi_http_server
        self.port = port

    async def start(self):
        self.server_socket = await trio.open_tcp_listeners(
            self.port, "::1")
        # don't wait
        self.cancel_scope = trio.CancelScope()
        self.accept_connections()

    async def stop(self):
        self.cancel_scope.cancel()
        with trio.move_on_after(1):
            pass

    async def accept_connections(self):
        async def receiver(socket):
            await self.receive_connection(socket)
        with self.cancel_scope:
            trio.serve_listeners(receiver, self.server_socket)

    async def receive_connections(self, socket):
        try:
            connection = SocketConnection(socket, None, None,
                                          self.default_processing_options)
            await self.quasi_http_server.accept_connection(connection)
        except BaseException as ex:
            print(f"connection processing error: {ex}")
        
    async def release_connection(self, connection):
        await connection.release(None)

    def get_readable_stream(self, connection):
        return connection.socket
    
    def get_writable_stream(self, connection):
        return connection.socket