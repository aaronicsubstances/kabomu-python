import pytest

from kabomu import io_utils_internal

from kabomu.errors import KabomuIOError

from tests.shared import comparison_utils

async def test_read_bytes_fully():
    # arrange
    reader = comparison_utils.create_randomized_read_input_stream(
        bytes([0, 1, 2, 3, 4, 5, 6, 7]))

    # act
    read_buffer = await io_utils_internal.read_bytes_fully(reader, 3)

    # assert
    assert read_buffer == bytes([0, 1, 2])
    
    # assert that zero length reading doesn't cause problems.
    read_buffer = await io_utils_internal.read_bytes_fully(reader, 0)
    assert read_buffer == b""

    # act again
    read_buffer = await io_utils_internal.read_bytes_fully(reader, 3)
    
    # assert
    assert read_buffer == bytes([3, 4, 5])
    
    # act again
    read_buffer = await io_utils_internal.read_bytes_fully(reader, 2)
    
    # assert
    assert read_buffer == bytes([6, 7])

    # test zero byte reads.
    read_buffer = await io_utils_internal.read_bytes_fully(reader, 0)
    assert read_buffer == bytes()

async def test_read_bytes_fully_for_errors():
    # arrange
    reader = comparison_utils.create_byte_array_input_stream(
        bytes([0, 1, 2, 3, 4, 5, 6, 7]))

    # act
    read_buffer = await io_utils_internal.read_bytes_fully(reader, "5")
    
    # assert
    assert read_buffer == bytes([0, 1, 2, 3, 4])

    actual_ex = None
    try:
        await io_utils_internal.read_bytes_fully(reader, 5)
    except KabomuIOError as ex:
        actual_ex = ex
    if not actual_ex:
        pytest.fail("expected KabomuIOError")
    assert "end of read" in str(actual_ex)

@pytest.mark.parametrize("src_data",  
    [  
        "", "ab", "xyz", "abcdefghi"
    ])
async def test_copy(src_data: str):
    # arrange
    expected = src_data.encode()
    reader_stream = comparison_utils.create_randomized_read_input_stream(expected)
    writer_stream = comparison_utils.create_byte_array_output_stream()

    # act
    await io_utils_internal.copy(reader_stream, writer_stream)

    # assert
    assert writer_stream.to_byte_array() == expected
