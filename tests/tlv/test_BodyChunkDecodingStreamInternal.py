import pytest

from kabomu.tlv import tlv_utils

from kabomu.errors import KabomuIOError

from tests.shared import comparison_utils

@pytest.mark.parametrize("src_data, expected_tag, tag_to_ignore, expected",  
    [
        (bytes([0, 0, 0, 89,
                0, 0, 0, 0]), 89, 5, b""),  
        (bytes([0, 0, 0, 15,
                0, 0, 0, 2,
                2, 3,
                0, 0, 0, 8,
                0, 0, 0, 0]), 8, 15, b""),
        (bytes([
                0, 0, 0, 8,
                0, 0, 0, 2,
                2, 3,
                0, 0, 0, 8,
                0, 0, 0, 0]), 8, 15, bytes([2, 3])),
        (bytes([
                0, 0, 0, 8,
                0, 0, 0, 1,
                2,
                0, 0, 0, 8,
                0, 0, 0, 1,
                3,
                0, 0, 0, 8,
                0, 0, 0, 0]), 8, 15, bytes([2, 3])),
        (bytes([0, 0, 0x3d, 0x15,
                0, 0, 0, 0,
                0x30, 0xa3, 0xb5, 0x17,
                0, 0, 0, 1,
                2,
                0, 0, 0x3d, 0x15,
                0, 0, 0, 7,
                0, 0, 0, 0, 0, 0, 0,
                0x30, 0xa3, 0xb5, 0x17,
                0, 0, 0, 1,
                3,
                0, 0, 0x3d, 0x15,
                0, 0, 0, 0,
                0x30, 0xa3, 0xb5, 0x17,
                0, 0, 0, 4,
                2, 3, 45, 62,
                0, 0, 0x3d, 0x15,
                0, 0, 0, 1,
                1,
                0x30, 0xa3, 0xb5, 0x17,
                0, 0, 0, 8,
                91, 100, 2, 3, 45, 62, 70, 87,
                0x30, 0xa3, 0xb5, 0x17,
                0, 0, 0, 0]), 0x30a3b517, 0x3d15,
                bytes([2, 3, 2, 3, 45, 62,
                    91, 100, 2, 3, 45, 62, 70, 87]))
    ])
async def test_reading(src_data, expected_tag,
                       tag_to_ignore, expected):
    instance = comparison_utils.create_randomized_read_input_stream(
        src_data)
    instance = tlv_utils.create_tlv_decoding_readable_stream(
        instance, expected_tag, tag_to_ignore)

    # act
    actual = await comparison_utils.read_all_bytes(instance)

    # assert
    assert actual == expected

@pytest.mark.parametrize("src_data, expected_tag, tag_to_ignore, expected",  
    [
        (bytes([0, 0, 0x09, 0,
                0, 0, 0, 12]), 0x0900, 0, "unexpected end of read"),  
        (bytes([0, 0, 0x09, 0,
                0, 0, 0, 12]), 10, 30, "unexpected tag"),
        (bytes([
                0, 0, 0, 15,
                0, 0, 0, 2,
                2, 3,
                0, 0, 0, 15,
                0, 0, 0, 2,
                2, 3,
                0, 0, 0, 8,
                0, 0, 0, 0]), 8, 15, "unexpected tag"),
        (bytes([
                0, 0, 0, 0,
                0, 0xff, 0xff, 0xec,
                2, 3,
                0, 0, 0, 14,
                0, 0, 0, 0,
                2, 3,
                0, 0, 0, 8,
                0, 0, 0, 0]), 14, 8, "invalid tag: 0"),
        (bytes([0, 0, 0, 14,
                0xff, 0xff, 0xff, 0xec,
                2, 3,
                0, 0, 0, 14,
                0, 0, 0, 0,
                2, 3,
                0, 0, 0, 8,
                0, 0, 0, 0]), 14, 15,
                "invalid tag value length: -20")
    ])
async def test_decoding_for_errors(src_data, expected_tag,
                                   tag_to_ignore, expected):
    # arrange
    instance = comparison_utils.create_byte_array_input_stream(src_data)
    instance = tlv_utils.create_tlv_decoding_readable_stream(
        instance, expected_tag, tag_to_ignore)
    
    # act
    async def test_routine():
        await comparison_utils.read_all_bytes(instance)
    actual_ex = await comparison_utils.assert_throws(
        test_routine, KabomuIOError)
    assert expected in str(actual_ex)