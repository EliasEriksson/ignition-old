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


def run_server():
    loop = asyncio.get_event_loop()
    server = ignition.Server(loop)
    loop.run_until_complete(server.run())


def run_service():
    loop = asyncio.get_event_loop()
    service = ignition.Service(loop)
    loop.run_until_complete(service.manager.test())
    print("was here")
    # loop.run_until_complete(service.run({
    #     "language": "python",
    #     "code": "print('hello world!')",
    #     "args": ""
    # }))
    # loop.run_forever()


def build_docker_image():
    process("sudo docker build --tag ignition .")


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser()
    modes = {
        "service": run_service,
        "server": run_server,
        "build-docker-image": build_docker_image
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
