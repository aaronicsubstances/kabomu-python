import trio

from kabomu import StandardQuasiHttpClient
from kabomu.abstractions import QuasiHttpProcessingOptions

from LocalhostTcpClientTransport import LocalhostTcpClientTransport
from FileSender import start_transferring_files

async def main():
    server_port = 5001
    upload_dir_path = "logs/client"
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