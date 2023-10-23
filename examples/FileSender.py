import base64
import os
import random
import sys
import time

import trio

from kabomu.abstractions import DefaultQuasiHttpRequest,\
    QuasiHttpProcessingOptions
from kabomu import quasi_http_utils

from tests.shared import comparison_utils

async def start_transferring_files(
        instance, server_endpoint, upload_dir_path):
    count = 0
    bytes_transferred = 0
    start_time = time.perf_counter()

    for filename in os.listdir(upload_dir_path):
        f = os.path.join(upload_dir_path, filename)
        if not os.path.isfile(f):
            continue
        await transfer_file(instance, server_endpoint, f)
        bytes_transferred += os.path.getsize(f)
        count += 1

    time_taken = time.perf_counter() - start_time
    mega_bytes_transferred = bytes_transferred / (1024.0 * 1024.0)
    rate = round(mega_bytes_transferred / time_taken, 2)
    t = "Successfully transferred {0} bytes ({1} MB) worth of data in {2} files" +\
        " in {3} seconds = {4} MB/s"
    print(t.format(bytes_transferred, round(mega_bytes_transferred, 2),
                    count, round(time_taken, 2), rate))

async def transfer_file(instance, server_endpoint, f):
    request = DefaultQuasiHttpRequest()

    f_name = os.path.basename(f)
    f_name_encoded = base64.b64encode(f_name.encode()).decode()
    request.headers = {
        "f": [f_name_encoded]
    }
    echo_body_on = random.randint(0, 1)
    f_path_encoded = base64.b64encode(f.encode()).decode()
    if echo_body_on:
        request.headers["echo-body"] = [
            f_path_encoded   
        ]
    
    # add body
    with trio.open_file(f) as file_stream:
        request.body = file_stream
        request.content_length = -1
        if random.randint(0, 1):
            request.content_length = os.path.getsize(f)
        
        # determine options
        send_options = None
        if random.randint(0, 1):
            send_options = QuasiHttpProcessingOptions(
                max_response_body_size = -1
            )
        
        res = None
        try:
            if random.randbytes(0, 1):
                res = await instance.send(server_endpoint, request,
                                        send_options)
            else:
                async def request_generator():
                    return request
                res = await instance.send2(server_endpoint, request_generator,
                                        send_options)
                if res.status_code == quasi_http_utils.STATUS_CODE_OK:
                    if echo_body_on:
                        actual_res_body = await comparison_utils.read_as_bytes(
                            res.body
                        )
                        actual_res_body = base64.b64decode(
                            actual_res_body).decode()
                        if actual_res_body != f:
                            raise Exception("expected echo body to be " +
                                f"{f} but got {actual_res_body}")
                    print(f"File {f} sent successfully")
                else:
                    response_msg = ""
                    if res.body:
                        try:
                            response_msg = await comparison_utils.read_string_tobyes(res.body)
                        except:
                            pass # ignore.
                    raise Exception(f"status code indicates error: {res.status_code}\n{response_msg}")
        except:
            print(f"File {f} sent with error: {sys.exc_info()[1]}")
            raise
        finally:
            if res:
                await res.release()         

