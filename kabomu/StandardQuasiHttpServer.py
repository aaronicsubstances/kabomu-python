import sys

from kabomu.quasi_http_utils import _get_optional_attr
from kabomu import protocol_utils_internal
from kabomu.errors import MissingDependencyError,\
    QuasiHttpError,\
    QUASI_HTTP_ERROR_REASON_GENERAL

class StandardQuasiHttpServer:
    def __init__(self):
        self.transport = None
        self.application = None

    async def accept_connection(self, connection):
        if not connection:
            raise ValueError("connection argument is null")

        # access fields for use per processing call, in order to cooperate with
        # any implementation of field accessors which supports
        # concurrent modifications.
        transport = self.transport
        application = self.application
        if not transport:
            raise MissingDependencyError("server transport")
        if not application:
            raise MissingDependencyError("server application")

        try:
            timeout_scheduler = _get_optional_attr(
                connection, "timeout_scheduler")
            if timeout_scheduler:
                async def proc():
                    await _process_accept(application, transport,
                                          connection)
                await protocol_utils_internal.run_timeout_scheduler(
                    timeout_scheduler, False, proc)
            else:
                await _process_accept(application, transport,
                                      connection)
            await transport.release_connection(connection)
        except:
            #raise
            await _abort(transport, connection, True)
            ex = sys.exc_info()[1]
            if isinstance(ex, QuasiHttpError):
                raise
            abort_error = QuasiHttpError(
                QUASI_HTTP_ERROR_REASON_GENERAL,
                "encountered error during receive request processing")
            abort_error.__cause__ = ex
            raise abort_error

async def _process_accept(application, transport, connection):
    request = None
    if hasattr(transport, "request_deserializer"):
        request = await transport.request_deserializer(connection)
    if not request:
        request = await protocol_utils_internal.read_entity_from_transport(
            False, transport.get_readable_stream(connection),
            connection)

    response = await application.process_request(request)
    if not response:
        raise QuasiHttpError("no response")

    try:
        response_serialized = False
        if hasattr(transport, "response_serializer"):
            response_serialized = await transport.response_serializer(
                connection, response)
        if not response_serialized:
            await protocol_utils_internal.write_entity_to_transport(
                True, response, transport.get_writable_stream(connection),
                connection)
    finally:
        if hasattr(response, "release"):
            await response.release()

async def _abort(transport, connection, error_occured):
    if error_occured:
        try:
            # don't wait
            await transport.release_connection(
                connection) # swallow errors
        except:
            pass # ignore
    else:
        await transport.release_connection(
                connection)
