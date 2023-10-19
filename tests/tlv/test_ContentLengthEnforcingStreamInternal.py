import pytest

from kabomu import io_utils_internal
from kabomu.tlv import tlv_utils

from kabomu.errors import KabomuIOError

from tests.shared import comparison_utils

@pytest.mark.parametrize("content_length, src_data, expected",  
    [
        (0, "", ""),  
        (0, "a", ""),
        (1, "ab", "a"),
        (2, "ab", "ab"),
        (2, "abc", "ab"),
        (3, "abc", "abc"),
        (4, "abcd", "abcd"),
        (5, "abcde", "abcde"),
        (6, "abcdefghi", "abcdef")
    ])
async def test_reading(content_length, src_data, expected):
    # arrange
    stream = comparison_utils.create_randomized_read_input_stream(
        src_data.encode())
    instance = tlv_utils.create_content_length_enforcing_stream(
        stream, content_length)

    # act
    actual = await comparison_utils.read_as_string(instance)

    # assert
    assert actual == expected

@pytest.mark.parametrize("content_length, src_data",  
    [  
        (2, ""),  
        (4, "abc"),
        (5, "abcd"),
        (15, "abcdef")
    ])
async def test_reading_for_errors(content_length, src_data):
    # arrange
    stream = comparison_utils.create_byte_array_input_stream(
        src_data.encode())
    instance = tlv_utils.create_content_length_enforcing_stream(
        stream, content_length)

    # act
    async def test_routine():
        await comparison_utils.read_all_bytes(instance)
    actual_ex = await comparison_utils.assert_throws(
        test_routine, KabomuIOError)
    assert "end of read" in str(actual_ex)

async def test_zero_byte_reads():
    stream = comparison_utils.create_byte_array_input_stream(
        bytes([0, 1, 2, 4]))
    instance = tlv_utils.create_content_length_enforcing_stream(
        stream, 3)
    
    actual = await io_utils_internal.read_bytes_fully(instance, 0)
    assert actual == bytes()

    actual = await io_utils_internal.read_bytes_fully(instance, 3)
    assert actual == bytes([0, 1, 2])

    actual = await io_utils_internal.read_bytes_fully(instance, 0)
    assert actual == bytes()

    # test aftermath reads
    actual = await comparison_utils.read_all_bytes(stream)
    assert actual == bytes([4])
