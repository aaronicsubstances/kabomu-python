import random

import pytest

from trio.abc import ReceiveStream, SendStream

from kabomu.quasi_http_utils import _get_optional_attr

def create_byte_array_output_stream():
    buffer = bytearray()
    class ByteArrayOutputStream(SendStream):
        def __init__(self):
            super().__init__()
        
        def to_byte_array(self):
            return buffer
        
        async def send_all(self, data):
            buffer.extend(data)

        async def wait_send_all_might_not_block(self):
            pass

        async def aclose(self):
            pass
    return ByteArrayOutputStream()

def create_byte_array_input_stream(buffer):
    class ByteArrayInputStream(ReceiveStream):
        def __init__(self):
            super().__init__()
            self._offset = 0

        async def receive_some(self, max_bytes=None):
            if not max_bytes:
                max_bytes = len(buffer)
            max_bytes = min(len(buffer) - self._offset, max_bytes)
            next_chunk = buffer[self._offset:self._offset+max_bytes]
            self._offset += max_bytes
            return next_chunk

        async def aclose(self):
            pass

    return ByteArrayInputStream()

def create_randomized_read_input_stream(buffer):
    class RandomizedReadInputStream(ReceiveStream):
        def __init__(self):
            super().__init__()
            self._offset = 0

        async def receive_some(self, max_bytes=None):
            if not max_bytes:
                max_bytes = len(buffer)
            max_bytes = min(len(buffer) - self._offset, max_bytes)
            if max_bytes > 1:
                max_bytes = random.randint(1, max_bytes)
            next_chunk = buffer[self._offset:self._offset+max_bytes]
            self._offset += max_bytes
            return next_chunk

        async def aclose(self):
            pass

    return RandomizedReadInputStream()

async def read_as_string(stream: ReceiveStream):
    raw_data = await read_all_bytes(stream)
    return raw_data.decode()

async def read_all_bytes(stream: ReceiveStream):
    raw_data = bytearray()
    while True:
        next_chunk = await stream.receive_some()
        if not next_chunk:
            break
        raw_data.extend(next_chunk)
    return raw_data

def concat_buffers(*args):
    raw_data = bytearray()
    for next_chunk in args:
        raw_data.extend(next_chunk)
    return raw_data

async def assert_throws(proc, expected_cls=None):
    except_called = False
    err = None
    try:
        await proc()
    except BaseException as e:
        err = e
        if expected_cls:
            if not isinstance(err, expected_cls):
                raise
        except_called = True
    if not except_called:
        expected_cls = expected_cls if expected_cls else BaseException
        pytest.fail(f"DID NOT RAISE {expected_cls}")
    return err

async def compare_requests(
        actual, expected, expected_req_body_bytes):
    if not actual or not expected:
        assert actual is expected
        return
    
    assert _get_optional_attr(actual, "http_method") ==\
        _get_optional_attr(expected, "http_method")
    assert _get_optional_attr(actual, "http_version") ==\
        _get_optional_attr(expected, "http_version")
    assert _get_optional_attr(actual, "content_length") ==\
        _get_optional_attr(expected, "content_length")
    assert _get_optional_attr(actual, "target") ==\
        _get_optional_attr(expected, "target")
    assert _get_optional_attr(actual, "headers") ==\
        _get_optional_attr(expected, "headers")
    await _compare_bodies(_get_optional_attr(actual, "body"),
                          expected_req_body_bytes)


async def compare_responses(
        actual, expected, expected_res_body_bytes):
    if not actual or not expected:
        assert actual is expected
        return
    
    assert _get_optional_attr(actual, "status_code") ==\
        _get_optional_attr(expected, "status_code")
    assert _get_optional_attr(actual, "http_version") ==\
        _get_optional_attr(expected, "http_version")
    assert _get_optional_attr(actual, "content_length") ==\
        _get_optional_attr(expected, "content_length")
    assert _get_optional_attr(actual, "http_status_message") ==\
        _get_optional_attr(expected, "http_status_message")
    assert _get_optional_attr(actual, "headers") ==\
        _get_optional_attr(expected, "headers")
    await _compare_bodies(_get_optional_attr(actual, "body"),
                          expected_res_body_bytes)

async def _compare_bodies(actual, expected_body_bytes):
    if expected_body_bytes is None:
        assert not actual
        return
    
    assert actual
    actual_body_bytes = await read_all_bytes(actual)
    assert actual_body_bytes == expected_body_bytes
