from trio.abc import HalfCloseableStream, ReceiveStream, SendStream

from kabomu import io_utils_internal, misc_utils_internal
from kabomu.errors import KabomuIOError, IllegalArgumentError

TAG_FOR_QUASI_HTTP_HEADERS = 0x68647273

TAG_FOR_QUASI_HTTP_BODY_CHUNK = 0x62647461

TAG_FOR_QUASI_HTTP_BODY_CHUNK_EXT = 0x62657874

DEFAULT_MAX_LENGTH  = 134_217_728 # 128 MB

def encode_tag_and_length(tag: int, length: int):
    if tag <= 0:
        raise KabomuIOError(f"invalid tag: {tag}")
    if length < 0:
        raise KabomuIOError(f"invalid length: {length}")
    encoded_tag = misc_utils_internal.serialize_int32_be(tag)
    return encoded_tag + misc_utils_internal.serialize_int32_be(length)

def decode_tag(data, offset):
    tag = misc_utils_internal.deserialize_int32_be(data, offset)
    if tag <= 0:
        raise IllegalArgumentError(f"invalid tag: {tag}")
    return tag

def decode_length(data, offset):
    decoded_length = misc_utils_internal.deserialize_int32_be(data, offset)
    if decoded_length < 0:
        raise IllegalArgumentError(f"invalid length: {decode_length}")
    return decoded_length

def create_content_length_enforcing_stream(backing_stream: ReceiveStream,
                                           content_length: int):
    class ContentLengthEnforcingStream(ReceiveStream):
        def __init__(self):
            super().__init__()
            self._bytes_left_to_read = int(content_length)

        async def receive_some(self, max_bytes=None):
            if not max_bytes:
                max_bytes = 8_192
            bytes_to_read = min(self._bytes_left_to_read, int(max_bytes))
            next_chunk = b""
            if bytes_to_read:
                next_chunk = await backing_stream.receive_some(bytes_to_read)
            self._bytes_left_to_read -= len(next_chunk)
            end_of_read = not next_chunk
            if end_of_read and self._bytes_left_to_read > 0:
                raise KabomuIOError.create_end_of_read_error()
            return next_chunk

        async def aclose(self):
            pass
        
    return ContentLengthEnforcingStream()

def create_max_length_enforcing_stream(backing_stream: ReceiveStream,
                                       max_length=None):
    class MaxLengthEnforcingStream(ReceiveStream):
        def __init__(self):
            super().__init__()
            nonlocal max_length
            if not max_length:
                max_length = DEFAULT_MAX_LENGTH
            self._bytes_left_to_read = int(max_length) + 1 # check for excess read.

        async def receive_some(self, max_bytes=None):
            if not max_bytes:
                max_bytes = 8_192
            bytes_to_read = min(self._bytes_left_to_read, int(max_bytes))
            next_chunk = b""
            if bytes_to_read:
                next_chunk = await backing_stream.receive_some(bytes_to_read)
            self._bytes_left_to_read -= len(next_chunk)
            if not self._bytes_left_to_read:
                raise KabomuIOError(f"stream size exceeds limit of {max_length} bytes")
            return next_chunk

        async def aclose(self):
            pass

    return MaxLengthEnforcingStream()

def create_tlv_encoding_writable_stream(backing_stream: SendStream,
                                        tag_to_use: int):
    #class BodyChunkEncodingStream(SendStream, HalfCloseableStream):
    class BodyChunkEncodingStream:
        def __init__(self):
            pass
        
        async def send_eof(self):
            await backing_stream.send_all(
                encode_tag_and_length(tag_to_use, 0))
        
        async def send_all(self, data):
            if data:
                await backing_stream.send_all(
                    encode_tag_and_length(tag_to_use, len(data)))
                await backing_stream.send_all(data)

        def wait_send_all_might_not_block(self):
            return backing_stream.wait_send_all_might_not_block()

        async def aclose(self):
            pass

    return BodyChunkEncodingStream()

def create_tlv_decoding_readable_stream(
        backing_stream: ReceiveStream,
        expected_tag: int, tag_to_ignore: int):
    class BodyChunkDecodingStream(ReceiveStream):
        def __init__(self) -> None:
            super().__init__()
            self._last_chunk_seen = False
            self._chunk_data_len_rem = 0

        async def receive_some(self, max_bytes=None):
            if not max_bytes:
                max_bytes = 8_192
            # once empty data chunk is seen,
            # return empty for all subsequent reads.
            if self._last_chunk_seen:
                return b""
            
            if not self._chunk_data_len_rem:
                self._chunk_data_len_rem = await self._fetch_next_tag_and_length()
                if not self._chunk_data_len_rem:
                    self._last_chunk_seen = True
                    return b""
                
            max_bytes = min(self._chunk_data_len_rem, int(max_bytes))
            next_chunk = await backing_stream.receive_some(max_bytes)
            if not next_chunk:
                raise KabomuIOError.create_end_of_read_error()
            self._chunk_data_len_rem -= len(next_chunk)
            return next_chunk
        
        async def _fetch_next_tag_and_length(self):
            tag = await self._read_tag_only()
            if tag == tag_to_ignore:
                await self._read_away_tag_value()
                tag = await self._read_tag_only()
            
            if tag != expected_tag:
                raise KabomuIOError(
                    f"unexpected tag: expected {expected_tag} but found {tag}")
            return await self._read_length_only()
        
        async def _read_away_tag_value(self):
            length = await self._read_length_only()
            src = create_content_length_enforcing_stream(
                backing_stream, length)
            async for _ in src:
                pass

        async def _read_tag_only(self):
            encoded_tag = await io_utils_internal.read_bytes_fully(
                backing_stream, 4)
            tag = int.from_bytes(encoded_tag, signed=True)
            if tag <= 0:
                raise KabomuIOError(f"invalid tag: {tag}")
            return tag

        async def _read_length_only(self):
            encoded_length = await io_utils_internal.read_bytes_fully(
                backing_stream, 4)
            length = int.from_bytes(encoded_length, signed=True)
            if length < 0:
                raise KabomuIOError(f"invalid tag value length: {length}")
            return length

        async def aclose(self):
            pass

    return BodyChunkDecodingStream()
