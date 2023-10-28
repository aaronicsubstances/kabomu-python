import base64
import logging
import os
import random
import sys
import time

import trio

from kabomu.abstractions import DefaultQuasiHttpRequest,\
    QuasiHttpProcessingOptions
from kabomu import quasi_http_utils

from shared import io_utils_extra

async def start_transferring_files(
        instance, server_endpoint, upload_dir_path):
    count = 0
    bytes_transferred = 0
    start_time = time.perf_counter()

    with os.scandir(upload_dir_path) as dir_scanner:
        for entry in dir_scanner:
            if not entry.is_file():
                continue
            sz = entry.stat().st_size
            await transfer_file(instance, server_endpoint, entry.path,
                                sz)
            bytes_transferred += sz
            count += 1

    time_taken = time.perf_counter() - start_time
    mega_bytes_transferred = bytes_transferred / (1024.0 * 1024.0)
    rate = round(mega_bytes_transferred / time_taken, 2)
    t = "Successfully transferred {0} bytes ({1} MB) worth of data in {2} files" +\
        " in {3} seconds = {4} MB/s"
    logging.info(t.format(bytes_transferred, round(mega_bytes_transferred, 2),
                    count, round(time_taken, 2), rate))

async def transfer_file(instance, server_endpoint, f, f_size):
    request = DefaultQuasiHttpRequest()

    f_name = os.path.basename(f)
    f_name_encoded = base64.b64encode(f_name.encode()).decode()
    request.headers = {
        "f": [f_name_encoded]
    }
    echo_body_on = random.randint(0, 1)
    if echo_body_on:
        f_path_encoded = base64.b64encode(f.encode()).decode()
        request.headers["echo-body"] = [
            f_path_encoded
        ]
    
    # add body
    async with await trio.open_file(f, 'rb', buffering=0) as file_stream:
        request.body = file_stream
        request.content_length = -1
        if random.randint(0, 1):
            request.content_length = f_size
        
        # determine options
        send_options = None
        if random.randint(0, 1):
            send_options = QuasiHttpProcessingOptions(
                max_response_body_size = -1
            )
        
        res = None
        try:
            if random.randint(0, 1):
                res = await instance.send(server_endpoint, request,
                                        send_options)
            else:
                async def request_generator(ignored_env):
                    return request
                res = await instance.send2(server_endpoint, request_generator,
                                        send_options)
                if res.status_code == quasi_http_utils.STATUS_CODE_OK:
                    if echo_body_on:
                        actual_res_body = await io_utils_extra.read_all_bytes(
                            res.body
                        )
                        actual_res_body = base64.b64decode(
                            actual_res_body).decode()
                        if actual_res_body != f:
                            raise Exception("expected echo body to be " +
                                f"{f} but got {actual_res_body}")
                    logging.info(f"File {f} sent successfully")
                else:
                    response_msg = ""
                    if res.body:
                        try:
                            response_msg = await io_utils_extra.read_string_tobyes(res.body)
                        except:
                            pass # ignore.
                    raise Exception(f"status code indicates error: {res.status_code}\n{response_msg}")
        except:
            logging.warning(f"File {f} sent with error: {sys.exc_info()[1]}")
            raise
        finally:
            if res:
                await res.release()         

