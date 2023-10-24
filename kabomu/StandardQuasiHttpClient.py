import sys

from kabomu.quasi_http_utils import _get_optional_attr, _bind_method
from kabomu import protocol_utils_internal
from kabomu.errors import MissingDependencyError,\
    QuasiHttpError,\
    QUASI_HTTP_ERROR_REASON_GENERAL

class StandardQuasiHttpClient:
    def __init__(self, transport=None):
        self.transport = transport

    async def send(self, remote_endpoint, request, options=None):
        if not request:
            raise ValueError("request argument is null")
        return await self._send_internal(
            remote_endpoint, request, None, options)

    async def send2(self, remote_endpoint, request_func, options=None):
        if not request_func:
            raise ValueError("request_func argument is null")
        return await self._send_internal(
            remote_endpoint, None, request_func, options)

    async def _send_internal(self,
            remote_endpoint, request, request_func,
            send_options):
        # access fields for use per request call, in order to cooperate with
        # any implementation of field accessors which supports
        # concurrent modifications.
        transport = self.transport

        if not transport:
            raise MissingDependencyError("client transport")

        connection = None
        try:
            connection = await transport.allocate_connection(
                remote_endpoint, send_options)
            if not connection:
                raise QuasiHttpError("no connection")

            async def proc():
                return await _process_send(
                    request, request_func,
                    transport, connection)
            response = await protocol_utils_internal.run_timeout_scheduler(
                connection, True, proc)
            if not response:
                response = await _process_send(
                    request, request_func, transport, connection)
            await _abort(transport, connection, False, response)
            return response
        except:
            #raise
            if connection:
                await _abort(transport, connection, True)
            ex = sys.exc_info()[1]
            if isinstance(ex, QuasiHttpError):
                raise
            abort_error = QuasiHttpError(
                QUASI_HTTP_ERROR_REASON_GENERAL,
                "encountered error during send request processing")
            abort_error.__cause__ = ex
            raise abort_error

async def _process_send(request, request_func, transport, connection):
    # wait for connection to be completely established.
    await transport.establish_connection(connection)

    if not request:
        request = await request_func(
            _get_optional_attr(connection, "environment"))
        if not request:
            raise QuasiHttpError("no request")

    # send entire request first before
    # receiving of response.
    request_serialized = False
    if hasattr(transport, "request_serializer"):
        request_serialized = await transport.request_serializer(
            connection, request)
    if not request_serialized:
        await protocol_utils_internal.write_entity_to_transport(
            False, request, transport.get_writable_stream(connection),
            connection)

    response = None
    if hasattr(transport, "response_deserializer"):
        response = await transport.response_deserializer(connection)
    if not response:
        response = await protocol_utils_internal.read_entity_from_transport(
            True, transport.get_readable_stream(connection),
            connection)
        async def release_func(self):
            await transport.release_connection(connection, None)
        response.release = _bind_method(
            release_func, response)
    return response

async def _abort(transport, connection, error_occured, response=None):
    if error_occured:
        try:
            # don't wait
            await transport.release_connection(
                connection, None) # swallow errors
        except:
            pass # ignore
    else:
        await transport.release_connection(
                connection, response)
