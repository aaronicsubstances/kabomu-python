from trio.abc import ReceiveStream, SendStream

from kabomu.errors import KabomuIOError

async def read_bytes_fully(stream: ReceiveStream, count: int):
    raw_data = bytearray()
    bytes_left = int(count)
    while bytes_left:
        next_chunk = await stream.receive_some(bytes_left)
        if not next_chunk:
            raise KabomuIOError.create_end_of_read_error()
        raw_data.extend(next_chunk)
        bytes_left -= len(next_chunk)
    return raw_data

async def copy(src: ReceiveStream, dest: SendStream):
    while True:
        next_chunk = await src.receive_some()
        if not next_chunk:
            break
        await dest.send_all(next_chunk)
