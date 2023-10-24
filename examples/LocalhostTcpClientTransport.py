import trio

from kabomu.abstractions import IQuasiHttpClientTransport

from SocketConnection import SocketConnection

class LocalhostTcpClientTransport(IQuasiHttpClientTransport):
    def __init__(self, default_send_options):
        self.default_send_options = default_send_options

    async def allocate_connection(self, remote_endpoint, send_options):
        port = remote_endpoint
        socket = await trio.open_tcp_stream("::1", port)
        connection = SocketConnection(socket, port, send_options,
                                      self.default_send_options)
        return connection
    
    async def establish_connection(self, connection):
        pass

    async def release_connection(self, connection, response):
        await connection.release(response)

    def get_readable_stream(self, connection):
        return connection.socket
    
    def get_writable_stream(self, connection):
        return connection.socket
