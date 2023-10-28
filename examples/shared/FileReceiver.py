import base64
import logging
import os
import random
import re
import sys

import trio

from kabomu.abstractions import DefaultQuasiHttpResponse,\
    IQuasiHttpApplication
from kabomu import quasi_http_utils, io_utils_internal

from shared import io_utils_extra

class FileReceiver(IQuasiHttpApplication):
    def __init__(self, remote_endpoint, download_dir_path):
        self.remote_endpoint = remote_endpoint
        self.download_dir_path = download_dir_path

    async def process_request(self, request):
        file_name = request.headers["f"][0]
        file_name = base64.b64decode(file_name.encode()).decode()
        file_name = os.path.basename(file_name)

        transfer_error = None
        try:
            # ensure directory exists.
            # just in case remote endpoint contains invalid file path characters...
            path_for_remote_endpoint = re.sub(r'\W', "_", f"{self.remote_endpoint}")
            directory = os.path.join(self.download_dir_path,
                                     path_for_remote_endpoint)
            os.makedirs(directory,exist_ok=True)
            file_path = os.path.join(directory, file_name)

            async with await trio.open_file(file_path, 'wb', buffering=0) as file_stream:
                logging.debug(f"Starting receipt of file {file_name} from ${self.remote_endpoint}...")
                await io_utils_internal.copy(request.body, file_stream)
        except:
            transfer_error = sys.exc_info()[1]

        response = DefaultQuasiHttpResponse()
        response_body = None
        if not transfer_error:
            logging.info(f"File {file_name} received successfully")
            response.status_code = quasi_http_utils.STATUS_CODE_OK
            if "echo-body" in request.headers:
                echo_body = request.headers["echo-body"]
                response_body = ",".join(echo_body)
        else:
            logging.error(f"File {file_name} received with error:", exc_info=transfer_error)
            response.status_code = quasi_http_utils.STATUS_CODE_SERVER_ERROR
            response_body = str(transfer_error)
        if response_body:
            response_bytes = response_body.encode()
            response.body = io_utils_extra.create_byte_array_input_stream(
                response_bytes)
            response.content_length = -1
            if random.randint(0, 1):
                response.content_length = len(response_bytes)
        
        return response
