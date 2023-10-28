import trio

from kabomu.abstractions import IQuasiHttpConnection,\
    QuasiHttpProcessingOptions, DefaultTimeoutResult
from kabomu import quasi_http_utils

class SocketConnection(IQuasiHttpConnection):
    def __init__(self,
                 socket,
                 client_port_or_path,
                 processing_options,
                 fallback_processing_options):
        self.socket = socket
        self.client_port_or_path = client_port_or_path
        self._processing_options = quasi_http_utils.merge_processing_options(
            processing_options, fallback_processing_options)
        if self._processing_options is None:
            self._processing_options = QuasiHttpProcessingOptions()
        self.timeout_scope = None
        self.cancel_scope = None

    def environment(self):
        return None
    
    def processing_options(self):
        return self._processing_options
    
    async def schedule_timeout(self, proc):
        timeout_milis = self._processing_options.timeout_millis
        if not timeout_milis or timeout_milis <= 0:
            return
        self.cancel_scope = trio.CancelScope()
        self.timeout_scope = trio.move_on_after(timeout_milis / 1000.0)
        with self.timeout_scope:
            with self.cancel_scope:
                response = await proc()
                return DefaultTimeoutResult(response=response)
        if self.timeout_scope.cancelled_caught:
            return DefaultTimeoutResult(timeout=True)
    
    async def release(self, response):
        cancel_scope, timeout_scope = self.cancel_scope, self.timeout_scope
        if cancel_scope:
            cancel_scope.cancel()
        if timeout_scope:
            timeout_scope.cancel()
        if response and hasattr(response, 'body') and response.body:
            return
        await self.socket.aclose()
