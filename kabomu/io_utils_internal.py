from kabomu.errors import KabomuIOError

DEFAULT_READ_BUFFER_SIZE = 8192

async def receive_some(stream, max_bytes=None):
    src_is_file = hasattr(stream, "read")
    if src_is_file:
        if not max_bytes or max_bytes < 1:
            max_bytes = DEFAULT_READ_BUFFER_SIZE
        next_chunk = await stream.read(max_bytes)
    else:
        next_chunk = await stream.receive_some(max_bytes)
    assert next_chunk is not None
    return next_chunk

async def send_all(stream, data):
    dest_is_file = hasattr(stream, "write")
    if dest_is_file:
        next_chunk_len = len(data)
        bytes_written = 0
        while bytes_written < next_chunk_len:
            # cause error if write returns None
            if bytes_written == 0:
                bytes_written += int(await stream.write(
                    data))
            else:
                bytes_written += int(await stream.write(
                    data[bytes_written:]))
    else:
        await stream.send_all(data)

async def read_bytes_fully(stream, count: int):
    raw_data = bytearray()
    bytes_left = int(count)
    while bytes_left:
        next_chunk = await receive_some(stream, bytes_left)
        next_chunk_len = len(next_chunk)
        if not next_chunk_len:
            raise KabomuIOError.create_end_of_read_error()
        raw_data.extend(next_chunk)
        bytes_left -= next_chunk_len
    return raw_data


async def copy(src, dest):
    while True:
        next_chunk = await receive_some(src)
        next_chunk_len = len(next_chunk)
        if not next_chunk_len:
            break
        await send_all(dest, next_chunk)
