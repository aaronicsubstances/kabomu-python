import pytest

from kabomu import io_utils_internal
from kabomu.tlv import tlv_utils

from tests.shared import comparison_utils

@pytest.mark.parametrize("tag, length, expected",  
    [
        (0x15c0, 2, bytes([0, 0, 0x15, 0xc0,
                    0, 0, 0, 2])),  
        (0x12342143, 0, bytes([0x12, 0x34, 0x21, 0x43,
                    0, 0, 0, 0])),
        (1, 0x78cdef01, bytes([0, 0, 0, 1,
                    0x78, 0xcd, 0xef, 0x01]))
    ])
def test_encode_tag_and_length(tag: int, length: int, expected):
    actual = tlv_utils.encode_tag_and_length(tag, length)
    assert actual == expected

@pytest.mark.parametrize("tag, length",  
    [
        (0, 1),  
        (-1, 1),
        (2, -1)
    ])
def test_encode_tag_and_length_for_errors(tag: int, length: int):
    with pytest.raises(Exception):
        tlv_utils.encode_tag_and_length(tag, length)

@pytest.mark.parametrize("data, offset, expected",  
    [
        (bytes([0, 0, 0, 1]), 0, 1),
        (bytes([0x03, 0x40, 0x89, 0x11]), 0, 0x03408911),
        (bytes([1, 0x56, 0x10, 0x01, 0x20, 2]), 1, 0x56100120),
    ])
def test_decode_tag(data, offset: int, expected):
    actual = tlv_utils.decode_tag(data, offset)
    assert actual == expected

@pytest.mark.parametrize("data, offset",  
    [
        (bytes([1, 1, 1]), 0),
        (bytes([0, 0, 0, 0]), 0),
        (bytes([5, 1, 200, 3, 0, 3 ]), 2),
    ])
def test_decode_tag_for_errors(data, offset):
    with pytest.raises(Exception):
        tlv_utils.decode_tag(data, offset)

@pytest.mark.parametrize("data, offset, expected",  
    [
        (bytes([0, 0, 0, 0]), 0, 0),
        (bytes([1, 2, 0, 0, 0, 1]), 2, 1),
        (bytes([0x03, 0x40, 0x89, 0x11]), 0, 0x03408911),
    ])
def test_decode_length(data, offset: int, expected):
    actual = tlv_utils.decode_length(data, offset)
    assert actual == expected

@pytest.mark.parametrize("data, offset",  
    [
        (bytes([1, 1, 1]), 0),
        (bytes([5, 1, 200, 3, 0, 3 ]), 2),
    ])
def test_decode_length_for_errors(data, offset):
    with pytest.raises(Exception):
        tlv_utils.decode_length(data, offset)

async def test_create_tlv_encoding_readable_stream():
    # arrange
    src_byte = 45
    tag_to_use = 16
    expected = bytes([
        0, 0, 0, 16,
        0, 0, 0, 1,
        src_byte,
        0, 0, 0, 16,
        0, 0, 0, 0
    ])
    dest_stream = comparison_utils.create_byte_array_output_stream()
    instance = tlv_utils.create_tlv_encoding_writable_stream(
        dest_stream, tag_to_use)
    
    # act
    await instance.send_all(bytes([src_byte]))
    await instance.send_all(b"")
    # write end of stream
    await instance.send_eof()

    # assert
    actual = dest_stream.to_byte_array()
    assert actual == expected

@pytest.mark.parametrize("expected, tag_to_use",
    [
        ("", 1),
        ("a", 4),
        ("ab", 45),
        ("abc", 60),
        ("abcd", 120_000_000),
        ("abcde", 34_000_000),
        ("abcdefghi", 0x3245671d)
    ])
async def test_body_chunk_codec_streams(expected, tag_to_use):
    src_stream = comparison_utils.create_randomized_read_input_stream(
        expected.encode())
    dest_stream = comparison_utils.create_byte_array_output_stream()
    encoding_stream = tlv_utils.create_tlv_encoding_writable_stream(
        dest_stream, tag_to_use)

    # act
    await io_utils_internal.copy(src_stream, encoding_stream)
    # write end of stream
    await encoding_stream.send_eof()
    mem_input_stream = comparison_utils.create_byte_array_input_stream(
        dest_stream.to_byte_array()) # reset for reading.
    decoding_stream = tlv_utils.create_tlv_decoding_readable_stream(
        mem_input_stream, tag_to_use, 0)
    actual = await comparison_utils.read_as_string(decoding_stream)

    # assert
    assert actual == expected
