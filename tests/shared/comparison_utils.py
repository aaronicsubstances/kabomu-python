import random
from contextlib import AbstractAsyncContextManager

import pytest

from trio.abc import ReceiveStream, SendStream

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

def assert_throws(*args, **kwargs):
    class ContextManager(AbstractAsyncContextManager):
        def __init__(self):
            self.value = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            with pytest.raises(*args, **kwargs) as retExc:
                if exc:
                    raise exc
            self.value = retExc.value
            return True

    return ContextManager()
