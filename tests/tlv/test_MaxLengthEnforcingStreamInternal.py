import pytest

from kabomu import io_utils_internal
from kabomu.tlv import tlv_utils

from kabomu.errors import KabomuIOError

from tests.shared import comparison_utils

@pytest.mark.parametrize("max_length, expected",  
    [
        (0, ""),  
        (0, "a"),
        (2, "a"),
        (2, "ab"),
        (3, "a"),
        (3, "abc"),
        (4, "abcd"),
        (5, "abcde"),
        (60, "abcdefghi")
    ])
async def test_reading(max_length, expected):
    # arrange
    stream = comparison_utils.create_randomized_read_input_stream(
        expected.encode())
    instance = tlv_utils.create_max_length_enforcing_stream(
        stream, max_length)

    # act
    actual = await comparison_utils.read_as_string(instance)

    # assert
    assert actual == expected


@pytest.mark.parametrize("max_length, src_data",  
    [  
        (1, "ab"),
        (2, "abc"),
        (3, "abcd"),
        (5, "abcdefxyz")
    ])

async def test_reading_for_errors(max_length, src_data):
    # arrange
    stream = comparison_utils.create_byte_array_input_stream(
        src_data.encode())
    instance = tlv_utils.create_max_length_enforcing_stream(
        stream, max_length)

    # act
    actual_ex = None
    try:
        await comparison_utils.read_all_bytes(instance)
    except KabomuIOError as ex:
        actual_ex = ex
    if not actual_ex:
        pytest.fail("expected KabomuIOError")
    assert f"exceeds limit of {max_length}" in str(actual_ex)

async def test_zero_byte_reads():
    instance = comparison_utils.create_byte_array_input_stream(
        bytes([0, 1, 2, 4]))
    instance = tlv_utils.create_max_length_enforcing_stream(
        instance)
    
    actual = await io_utils_internal.read_bytes_fully(instance, 0)
    assert actual == bytes()

    actual = await io_utils_internal.read_bytes_fully(instance, 3)
    assert actual == bytes([0, 1, 2])

    actual = await comparison_utils.read_all_bytes(instance)
    assert actual == bytes([4])

    actual = await io_utils_internal.read_bytes_fully(instance, 0)
    assert actual == bytes()
