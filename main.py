import argparse
import os
from pathlib import Path
import ignition
import asyncio


def run_server():
    loop = asyncio.get_event_loop()
    server = ignition.Server(loop)
    loop.run_until_complete(server.run())


def run_service():
    loop = asyncio.get_event_loop()
    service = ignition.Service()
    loop.run_until_complete(service.run({
        "language": "python",
        "code": "print('hello world!')",
        "args": ""
    }))


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser()
    modes = {
        "service": run_service,
        "server": run_server,
    }
    mode_help = ", ".join(f"'{mode}'" for mode in modes.keys())
    parser.add_argument("mode", type=str, nargs="?", default="service",
                        help=mode_help)
    parser.add_argument("-p", type=str, nargs="?", default="6090:6096",
                        help="port range (from:to) for the application. 1 port = 1 concurrent container.")

    result = parser.parse_args()
    try:
        if result.mode in modes:
            modes[result.mode]()
    except KeyboardInterrupt:
        pass
