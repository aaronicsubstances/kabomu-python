import sys

from kabomu.quasi_http_utils import _get_optional_attr
from kabomu import protocol_utils_internal
from kabomu.errors import MissingDependencyError,\
    QuasiHttpError,\
    QUASI_HTTP_ERROR_REASON_GENERAL

class StandardQuasiHttpClient:
    def __init__(self):
        self.transport = None

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
            response = None
            timeout_scheduler = _get_optional_attr(
                connection, "timeout_scheduler")
            if timeout_scheduler:
                async def proc():
                    return _process_send(
                        request, request_func,
                        transport, connection)
                response = await protocol_utils_internal.run_timeout_scheduler(
                    timeout_scheduler, True, proc)
            else:
                response_promise = _process_send(
                    request, request_func, transport, connection)
                timeout_task = _get_optional_attr(
                    connection, "timeout_task")
                if timeout_task:
                    pass
                response = await response_promise
            await _abort(transport, connection, False, response)
            return response
        except:
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
    request_serializer = _get_optional_attr(
        transport, "request_serializer")
    request_serialized = False
    if request_serializer:
        request_serialized = await request_serializer(
            connection, request)
    if not request_serialized:
        await protocol_utils_internal.write_entity_to_transport(
            False, request, transport.get_writable_stream(connection),
            connection)

    response = None
    response_deserializer = _get_optional_attr(
        transport, "response_deserializer")
    if response_deserializer:
        response = await response_deserializer(connection)
    if not response:
        response = await protocol_utils_internal.read_entity_from_transport(
            True, transport.get_readable_stream(connection),
            connection)
        async def release_func(_):
            await transport.release_connection(connection, None)
        response.release = release_func
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
