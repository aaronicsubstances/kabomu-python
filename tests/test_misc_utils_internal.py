import pytest

from kabomu import misc_utils_internal

from tests.shared import comparison_utils

@pytest.mark.parametrize("v, expected",  
    [
        (2001, bytes([0, 0, 7, 0xd1])),
        (-10_999, bytes([0xff, 0xff, 0xd5, 9])),
        (1_000_000, bytes([0, 0xf, 0x42, 0x40])),
        (1_000_000_000, bytes([0x3b, 0x9a, 0xca, 0])),
        (-1_000_000_000, bytes([0xc4, 0x65, 0x36, 0]))
    ])
def test_serialize_int32_be(v, expected):
    actual = misc_utils_internal.serialize_int32_be(v)
    assert actual == expected

@pytest.mark.parametrize("raw_bytes, offset, expected",  
    [
        (bytes([0, 0, 7, 0xd1]), 0, 2001),
        (bytes([0xff, 0xff, 0xd5, 9]), 0, -10_999),
        (bytes([0, 0xf, 0x42, 0x40]), 0, 1_000_000, ),
        (bytes([0xc4, 0x65, 0x36, 0]), 0, -1_000_000_000),
        (bytes([8, 2, 0x88, 0xca, 0x6b, 0x9c, 1]), 2, -2_000_000_100)
    ])
def test_deserialize_int32_be(raw_bytes, offset, expected):
    actual = misc_utils_internal.deserialize_int32_be(raw_bytes, offset)
    assert actual == expected

def test_deserialize_int32_be_for_errors():
    with pytest.raises(Exception):
        misc_utils_internal.deserialize_int32_be(bytes([0, 0]), 0)
    with pytest.raises(Exception):
        misc_utils_internal.deserialize_int32_be(bytes([0, 0, 0, 0]), 1)
    with pytest.raises(Exception):
        misc_utils_internal.deserialize_int32_be(bytes([0] * 20), 17)

@pytest.mark.parametrize("input, expected",
    [
        ("0", 0),
        ("1", 1),
        ("2", 2),
        (" 20", 20),
        (" 200 ", 200),
        ("-1000", -1000),
        (1000000, 1_000_000),
        ("-1000000000", -1_000_000_000),
        ("4294967295", 4_294_967_295),
        ("-50000000000000", -50_000_000_000_000),
        ("100000000000000", 100_000_000_000_000),
        ("140737488355327", 140_737_488_355_327),
        ("-140737488355328", -140_737_488_355_328)
    ])
def test_parse_int48(input, expected):
    actual = misc_utils_internal.parse_int_48(input)
    assert actual == expected

@pytest.mark.parametrize("input",
    [
        "", " ", None, "false", "xyz", "1.23", "2.0",
        140737488355328, "-140737488355329",
        "72057594037927935"
    ])
def test_parse_int48_for_errors(input):
    with pytest.raises(Exception):
        misc_utils_internal.parse_int_48(input)

@pytest.mark.parametrize("input, expected",
    [
        ("0", 0),
        ("1", 1),
        ("2", 2),
        (" 20", 20),
        (" 200 ", 200),
        ("-1000", -1000),
        (1000000, 1_000_000),
        ("-1000000000", -1_000_000_000),
        ("2147483647", 2_147_483_647),
        ("-2147483648", -2_147_483_648),
        # remainder are verifications
        (2.0, 2.0),
        (2_147_483_647, 2_147_483_647),
        (-2_147_483_648, -2_147_483_648)
    ])
def test_parse_int32(input, expected):
    actual = misc_utils_internal.parse_int_32(input)
    assert actual == expected

@pytest.mark.parametrize("input",
    [
        "", " ", None, "false", "xyz", "1.23", "2.0",
        "2147483648", "-2147483649", "50000000000000",
        [], {}
    ])
def test_parse_int32_for_errors(input):
    with pytest.raises(Exception):
        misc_utils_internal.parse_int_32(input)

@pytest.mark.parametrize("data, offset, length, expected",
    [
        (None, 0, 0, False),
        (bytes(), 0, 0, True),
        (bytes(), 1, 0, False),
        (bytes(), 0, 1, False),
        (bytes([1]), 0, 1, True),
        (bytes([1]), -1, 0, True),
        (bytes([1]), 0, -1, False),
        (bytes([1]), 1, 1, False),
        (bytes([1, 2]), 1, 1, True),
        (bytes([1, 2]), 0, 2, True),
        (bytes([1, 2, 3]), 2, 2, False)
    ])
def test_is_valid_byte_buffer_slice(data, offset, length, expected):
    actual = misc_utils_internal.is_valid_byte_buffer_slice(data, offset, length)
    assert actual == expected

def test_string_to_bytes():
    expected = bytes()
    actual = misc_utils_internal.string_to_bytes("")
    assert actual == expected

    expected = bytes([97, 98, 99])
    actual = misc_utils_internal.string_to_bytes("abc")
    assert actual == expected

    actual = misc_utils_internal.string_to_bytes(
        "Foo \u00a9 bar \U0001d306 baz \u2603 qux")
    expected = bytes([
        0x46, 0x6f, 0x6f, 0x20, 0xc2, 0xa9, 0x20,
        0x62, 0x61, 0x72, 0x20,
        0xf0, 0x9d, 0x8c, 0x86, 0x20, 0x62, 0x61,
        0x7a, 0x20, 0xe2, 0x98, 0x83,
        0x20, 0x71, 0x75, 0x78
    ])
    assert actual == expected

def test_bytes_to_string():
    expected = ""
    actual = misc_utils_internal.bytes_to_string(b"")
    assert actual == expected

    expected = "abc"
    actual = misc_utils_internal.bytes_to_string(
        bytes([97, 98, 99]))
    assert actual == expected
    
    expected = "Foo \u00a9 bar \U0001d306 baz \u2603 qux"
    actual = misc_utils_internal.bytes_to_string(bytes([
        0x46, 0x6f, 0x6f, 0x20, 0xc2, 0xa9, 0x20,
        0x62, 0x61, 0x72, 0x20,
        0xf0, 0x9d, 0x8c, 0x86, 0x20, 0x62, 0x61,
        0x7a, 0x20, 0xe2, 0x98, 0x83,
        0x20, 0x71, 0x75, 0x78
    ]))
    assert actual == expected
