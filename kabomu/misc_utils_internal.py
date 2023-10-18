from kabomu.errors import IllegalArgumentError

def serialize_int32_be(v: int):
    return v.to_bytes(4, signed=True)

def deserialize_int32_be(src, offset: int):
    if not is_valid_byte_buffer_slice(src, offset, 4):
        raise IllegalArgumentError("invalid byte buffer slice")
    return int.from_bytes(src[offset:offset+4], signed=True)

def parse_int_48(input):
    n = int(input)
    if n < -140_737_488_355_328 or n > 140_737_488_355_327:
        raise IllegalArgumentError(f"invalid 48-bit integer: {n}")
    return n

def parse_int_32(input):
    n = int(input)
    if n < -2_147_483_648 or n > 2_147_483_647:
        raise IllegalArgumentError(f"invalid 32-bit integer: {n}")
    return n

def is_valid_byte_buffer_slice(data, offset: int, length: int):
    if data == None:
        return False
    if type(offset) != int:
        return False
    if type(length) != int:
        return False
    if offset < 0:
        offset += len(data)
    if offset < 0:
        return False
    if length < 0:
        return False
    if offset + length > len(data):
        return False
    return True

def string_to_bytes(s):
    return s.encode()

def bytes_to_string(raw_bytes):
    return raw_bytes.decode()