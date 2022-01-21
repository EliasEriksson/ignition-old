import argparse
import os
from pathlib import Path
import ignition
import asyncio
import subprocess


def process(stdin: str) -> str:
    p = subprocess.run(stdin.split())
    return (
        (p.stdout.decode("utf-8") if p.stdout else "")
        if p.returncode == 0 else
        (p.stderr.decode("utf-8") if p.stderr else "")
    )


def start_client():
    loop = asyncio.get_event_loop()
    print("----------------------------------------------")
    ignition.Client(loop)


def start_server():
    loop = asyncio.get_event_loop()
    ignition.Server(loop=loop)
    loop.run_forever()


def test():
    loop = asyncio.get_event_loop()
    service = ignition.Server(loop=loop)
    status, request = loop.run_until_complete(service.test({
        "language": "python",
        "code": "print('hello world!')",
        "args": ""
    }))
    print(status, request)


def build_docker_image():
    process("sudo docker build --tag ignition .")


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser()
    modes = {
        "server": start_server,
        "client": start_client,
        "test": test,
        "build-docker-image": build_docker_image
    }
    mode_help = ", ".join(f"'{mode}'" for mode in modes.keys())
    parser.add_argument("mode", type=str, nargs="?", default="server",
                        help=mode_help)
    parser.add_argument("-p", type=str, nargs="?", default="6090:6096",
                        help="port range (from:to) for the application. 1 port = 1 concurrent container.")
    result = parser.parse_args()
    try:
        if result.mode in modes:
            modes[result.mode]()
    except KeyboardInterrupt:
        pass
