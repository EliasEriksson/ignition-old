import argparse
import logging
import os
from pathlib import Path
import ignition
import asyncio
import subprocess


logger = ignition.get_logger(__name__, logging.INFO)


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
    client = ignition.Client(loop)
    loop.run_until_complete(client.run())


def start_server():
    loop = asyncio.get_event_loop()
    ignition.Server(loop=loop)
    loop.run_forever()


def test():
    loop = asyncio.get_event_loop()
    server = ignition.Server(10, logger=logger, loop=loop)
    logger.info("starting test")
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "python",
        "code": "print('hello world!')",
        "args": ""
    }))
    print(status, response)


def test_all():
    loop = asyncio.get_event_loop()
    server = ignition.Server(10, logger=logger, loop=loop)
    logger.info("starting to test all")
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "python",
        "code": "print('hello world!')",
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "c",
        "code": "\n".join(["#include <stdio.h>", 'int main(){printf("Hello World");return 0;}']),
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "cpp",
        "code": "\n".join(['#include <iostream>', 'int main() {std::cout << "Hello World"; return 0;}']),
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "cs",
        "code": 'class Hello {static void Main(string[] args){System.Console.WriteLine("Hello World!");}}',
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "javascript",
        "code": "console.log('hello world!')",
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "php",
        "code": "echo 'Hello world!'",
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "java",
        "code": 'class HelloWorld {public static void main(String[] args) {System.out.println("Hello, World!");}}',
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.schedule_process({
        "language": "go",
        "code": "\n".join(["package main", 'import "fmt"', 'func main() {', 'fmt.Println("Hello world!")', "}"]),
        "args": ""
    }))
    print(status, response)


def build_docker_image():
    process("sudo docker build --tag ignition .")


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser()
    modes = {
        "server": start_server,
        "client": start_client,
        "test": test,
        "test-all": test_all,
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
