import configparser
import logging

import trio

from kabomu.StandardQuasiHttpServer import StandardQuasiHttpServer
from kabomu.abstractions import QuasiHttpProcessingOptions

from shared import AppLogger
from shared.LocalhostTcpServerTransport import LocalhostTcpServerTransport
from shared.FileReceiver import FileReceiver

async def main():
    AppLogger.config()
    config = configparser.ConfigParser()
    config.read('example.ini')
    default_section = config["DEFAULT"]
    port = int(default_section.get('PORT', 5001))
    download_dir_path = default_section.get("SAVE_DIR", "logs/server")
    instance = StandardQuasiHttpServer(
        application=FileReceiver(port, download_dir_path)
    )
    transport = LocalhostTcpServerTransport(
        port=port,
        quasi_http_server=instance,
        default_processing_options=QuasiHttpProcessingOptions(
            timeout_millis=5_000
        )
    )
    instance.transport = transport

    try:
        logging.info(f"Starting Tcp.FileServer at {port}...")
        print("Press Ctrl-C to exit...")
        await transport.start()
    except KeyboardInterrupt:
        pass
    except:
        logging.error(f"Fatal error encountered", exc_info=1)
    finally:
        logging.info("Stopping Tcp.FileServer...")
        await transport.stop()

trio.run(main)