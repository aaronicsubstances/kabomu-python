import pytest

from types import SimpleNamespace

from kabomu.StandardQuasiHttpClient import StandardQuasiHttpClient
from kabomu.StandardQuasiHttpServer import StandardQuasiHttpServer
from kabomu.errors import KabomuIOError,\
    QuasiHttpError,\
    QUASI_HTTP_ERROR_REASON_GENERAL,\
    QUASI_HTTP_ERROR_REASON_TIMEOUT,\
    QUASI_HTTP_ERROR_REASON_PROTOCOL_VIOLATION

from kabomu.quasi_http_utils import _bind_method

from tests.shared.comparison_utils import create_byte_array_input_stream,\
    create_byte_array_output_stream,\
    concat_buffers,\
    create_randomized_read_input_stream,\
    assert_throws,\
    compare_requests

@pytest.mark.parametrize("""expected_req_body_bytes,
        req,
        expected_request,
        expected_serialized_req""",
    [
        (
            "tanner".encode(),
            SimpleNamespace(http_method="GET",
                            target="/",
                            http_version="HTTP/1.0",
                            content_length=6,
                            headers={
                                "Accept": ["text/plain", "text/csv"],
                                "Content-Type": "application/json,charset=UTF-8"
                            }),
            SimpleNamespace(http_method="GET",
                            target="/",
                            http_version="HTTP/1.0",
                            content_length=6,
                            headers={
                                "accept": ["text/plain", "text/csv"],
                                "content-type": ["application/json,charset=UTF-8"]
                            }),
            concat_buffers(bytes([ 0x68, 0x64, 0x72, 0x73,
                    0, 0, 0, 106 ]),
                '"GET","/","HTTP/1.0","6"\n'.encode(),
                '"Accept","text/plain","text/csv"\n'.encode(),
                '"Content-Type","application/json,charset=UTF-8"\n'.encode(),
                "tanner".encode())
        ),
        (
            None,
            SimpleNamespace(),
            SimpleNamespace(http_method="",
                            target="",
                            http_version="",
                            content_length=0,
                            headers={}),
            concat_buffers(bytes([ 0x68, 0x64, 0x72, 0x73,
                    0, 0, 0, 13 ]),
                '"","","","0"\n'.encode())
        ),
        (
            bytes([8, 7, 8, 9]),
            SimpleNamespace(content_length=-1),
            SimpleNamespace(http_method="",
                            target="",
                            http_version="",
                            content_length=-1,
                            headers={}),
            None
        )
    ])
async def test_request_serialization(
        expected_req_body_bytes,
        req,
        expected_request,
        expected_serialized_req):
    remote_endpoint = {}
    if expected_req_body_bytes is not None:
        req.body = create_byte_array_input_stream(
            expected_req_body_bytes)
    dummy_res = SimpleNamespace()
    dest_stream = create_byte_array_output_stream()
    send_options = SimpleNamespace()
    client_connection = SimpleNamespace(
        processing_options=send_options,
        writable_stream=dest_stream)
    client_transport = create_client_transport_impl(False)
    async def client_transport_allocate(self, end_pt, opts):
        assert end_pt is remote_endpoint
        assert opts is send_options
        return client_connection
    client_transport.allocate_connection = _bind_method(
        client_transport_allocate, client_transport)
    async def client_transport_establish(self, conn):
        assert conn is client_connection
    client_transport.establish_connection = _bind_method(
        client_transport_establish, client_transport)
    async def client_transport_response_deserializer(self, conn):
        assert conn is client_connection
        return dummy_res
    client_transport.response_deserializer = _bind_method(
        client_transport_response_deserializer, client_transport)
    client = StandardQuasiHttpClient()
    client.transport = client_transport
    actual_res = await client.send(remote_endpoint, req,
                                   send_options)
    assert actual_res is dummy_res
    if expected_serialized_req is not None:
        assert dest_stream.to_byte_array() == expected_serialized_req

    #  deserialize
    mem_input_stream = create_randomized_read_input_stream(
        dest_stream.to_byte_array())
    actual_request = None
    server_connection = SimpleNamespace(
        readable_stream=mem_input_stream,
        environment={})
    server_transport = create_server_transport_impl(False)
    async def server_transport_response_serializer(self, conn, res):
        assert conn == server_connection
        assert res == dummy_res
        return True
    server_transport.response_serializer = _bind_method(
        server_transport_response_serializer, server_transport)
    async def server_application(req):
        nonlocal actual_request
        actual_request = req
        return dummy_res
    server = StandardQuasiHttpServer()
    server.transport = server_transport
    server.application = server_application
    await server.accept_connection(server_connection)

    # assert
    await compare_requests(actual_request, expected_request,
                           expected_req_body_bytes)
    actual_environment = None
    if actual_request and hasattr(actual_request, "environment"):
        actual_environment = actual_request.environment
    assert server_connection.environment is actual_environment

@pytest.mark.parametrize("""req,
        send_options,
        expected_error_msg,
        expected_serialized_req""",
    [
        (
            SimpleNamespace(http_method="POST",
                            target="/Update",
                            content_length=8),
            SimpleNamespace(max_headers_size=24),
            None,
            concat_buffers(bytes([ 0x68, 0x64, 0x72, 0x73,
                    0, 0, 0, 24 ]),
                '"POST","/Update",\"\","8"\n'.encode())
        ),
        (
            SimpleNamespace(http_method="PUT",
                            target="/Updates",
                            content_length=0,
                            body=create_byte_array_input_stream(bytes([4]))),
            SimpleNamespace(max_headers_size=25),
            None,
            concat_buffers(bytes([ 0x68, 0x64, 0x72, 0x73,
                    0, 0, 0, 24 ]),
                '"PUT","/Updates",\"\","0"\n'.encode(),
                bytes([
                    0x62, 0x64, 0x74, 0x61,
                    0, 0, 0, 1, 4,
                    0x62, 0x64, 0x74, 0x61,
                    0, 0, 0, 0
                ]))
        ),
        (
            SimpleNamespace(content_length=10,
                            body=create_byte_array_input_stream(bytes([4,5,6]))),
            None,
            None,
            concat_buffers(bytes([ 0x68, 0x64, 0x72, 0x73,
                    0, 0, 0, 14 ]),
                '"","","","10"\n'.encode(),
                bytes([
                    4, 5, 6
                ]))
        ),
        (
            SimpleNamespace(),
            SimpleNamespace(max_headers_size=5),
            "quasi http headers exceed max size",
            None
        ),
        (
            SimpleNamespace(http_version="no-spaces-allowed",
                            headers={
                                "empty-prohibited": ["a: \nb"]
                            }),
            None,
            "quasi http header value contains newlines",
            None
        )
    ])
async def test_request_serialization_for_errors(
        req,
        send_options,
        expected_error_msg,
        expected_serialized_req):
    remote_endpoint = {}
    dummy_res = SimpleNamespace()
    dest_stream = create_byte_array_output_stream()
    client_connection = SimpleNamespace(
        processing_options=send_options,
        writable_stream=dest_stream)
    client_transport = create_client_transport_impl(False)
    async def client_transport_allocate(self, end_pt, opts):
        assert end_pt is remote_endpoint
        assert opts is send_options
        return client_connection
    client_transport.allocate_connection = _bind_method(
        client_transport_allocate, client_transport)
    async def client_transport_establish(self, conn):
        assert conn is client_connection
    client_transport.establish_connection = _bind_method(
        client_transport_establish, client_transport)
    async def client_transport_response_deserializer(self, conn):
        assert conn is client_connection
        return dummy_res
    client_transport.response_deserializer = _bind_method(
        client_transport_response_deserializer, client_transport)
    client = StandardQuasiHttpClient()
    client.transport = client_transport

    if expected_error_msg is None:
        actual_res = await client.send(remote_endpoint, req,
                                       send_options)
        assert actual_res is dummy_res
        if expected_serialized_req is not None:
            assert dest_stream.to_byte_array() == expected_serialized_req
    else:
        async def test_routine():
            await client.send(remote_endpoint, req, send_options)
        actual_ex = await assert_throws(test_routine)
        assert expected_error_msg in str(actual_ex)

def create_client_transport_impl(
        initialize_serializer_functions):
    if initialize_serializer_functions:
        class TransportImpl():
            def get_readable_stream(self, connection):
                return connection.readable_stream
            def get_writable_stream(self, connection):
                return connection.writable_stream
            async def release_connection(self, connection, response):
                pass
            async def request_serializer(self, connection, request):
                pass
            async def response_serializer(self, connection, response):
                pass
            async def request_deserializer(self, connection):
                pass
            async def response_deserializer(self, connection):
                pass

        return TransportImpl()
    else:
        def get_readable_stream(self, connection):
            return connection.readable_stream
        def get_writable_stream(self, connection):
            return connection.writable_stream
        async def release_connection(self, connection, response):
            pass
        instance = SimpleNamespace()
        instance.get_readable_stream = _bind_method(
            get_readable_stream, instance)
        instance.get_writable_stream = _bind_method(
            get_writable_stream, instance)
        instance.release_connection = _bind_method(
            release_connection, instance)
        return instance

def create_server_transport_impl(
        initialize_serializer_functions):
    if initialize_serializer_functions:
        class TransportImpl():
            def get_readable_stream(self, connection):
                return connection.readable_stream
            def get_writable_stream(self, connection):
                return connection.writable_stream
            async def release_connection(self, connection):
                pass
            async def request_serializer(self, connection, request):
                pass
            async def response_serializer(self, connection, response):
                pass
            async def request_deserializer(self, connection):
                pass
            async def response_deserializer(self, connection):
                pass

        return TransportImpl()
    else:
        def get_readable_stream(self, connection):
            return connection.readable_stream
        def get_writable_stream(self, connection):
            return connection.writable_stream
        async def release_connection(self, connection):
            pass
        instance = SimpleNamespace()
        instance.get_readable_stream = _bind_method(
            get_readable_stream, instance)
        instance.get_writable_stream = _bind_method(
            get_writable_stream, instance)
        instance.release_connection = _bind_method(
            release_connection, instance)
        return instance
