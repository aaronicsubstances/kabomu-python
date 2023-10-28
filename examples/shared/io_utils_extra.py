from trio.abc import ReceiveStream, SendStream

from kabomu import io_utils_internal

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

async def read_as_string(stream: ReceiveStream):
    raw_data = await read_all_bytes(stream)
    return raw_data.decode()

async def read_all_bytes(stream: ReceiveStream):
    raw_data = bytearray()
    while True:
        next_chunk = await io_utils_internal.receive_some(stream)
        if not next_chunk:
            break
        raw_data.extend(next_chunk)
    return raw_data
