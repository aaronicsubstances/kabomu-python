import configparser

import trio

from kabomu.StandardQuasiHttpClient import StandardQuasiHttpClient
from kabomu.abstractions import QuasiHttpProcessingOptions

from shared import AppLogger
from shared.LocalhostTcpClientTransport import LocalhostTcpClientTransport
from shared.FileSender import start_transferring_files

async def main():
    AppLogger.config()
    config = configparser.ConfigParser()
    config.read('example.ini')
    default_section = config["DEFAULT"]
    server_port = int(default_section.get('SERVER_PORT', 5001))
    upload_dir_path = default_section.get("UPLOAD_DIR", "logs/client")
    transport = LocalhostTcpClientTransport(
        default_send_options=QuasiHttpProcessingOptions(
            timeout_millis=5_000
        )
    )
    instance = StandardQuasiHttpClient(transport=transport)

    try:
        print(f"Connecting Tcp.FileClient to {server_port}...")

        await start_transferring_files(instance, server_port,
                                       upload_dir_path)
    except BaseException as ex:
        print(f"Fatal error encountered: {ex}")
        raise

trio.run(main)