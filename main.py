import argparse
import logging
import os
from pathlib import Path
import ignition
import asyncio
import subprocess


logger = ignition.get_logger(__name__, logging.INFO, stdout=True)


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
    status, response = loop.run_until_complete(server.process({
        "language": "python",
        "code": "print('hello world!')",
        "args": ""
    }))
    print(status, response)


async def _test_async():
    loop = asyncio.get_event_loop()
    server = ignition.Server(3, logger=logger, loop=loop)
    print("testing async")
    tasks = [asyncio.create_task(server.process({
        "language": "python",
        "code": "print('Hello world!')",
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "c",
        "code": "\n".join(["#include <stdio.h>", 'int main(){printf("Hello World");return 0;}']),
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "cpp",
        "code": "\n".join(['#include <iostream>', 'int main() {std::cout << "Hello world"; return 0;}']),
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "cs",
        "code": 'class Hello {static void Main(string[] args){System.Console.WriteLine("Hello world!");}}',
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "javascript",
        "code": "console.log('Hello world!')",
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "php",
        "code": "<?php echo 'Hello world!'; ?>",
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "java",
        "code": 'class HelloWorld {public static void main(String[] args) {System.out.println("Hello world!");}}',
        "args": ""
    })), asyncio.create_task(server.process({
        "language": "go",
        "code": "\n".join(["package main", 'import "fmt"', 'func main() {', 'fmt.Println("Hello world!")', "}"]),
        "args": ""
    }))]
    print(f"{len(tasks)} tasks running...")
    results = await asyncio.gather(*tasks)
    for index, (status, result) in enumerate(results):
        print(index + 1, status, result)
    print("results", server.results)
    print("queue", server.queue)
    print("queue_overflow", server.overflow)


def test_async():
    asyncio.run(_test_async())


def test_all():
    loop = asyncio.get_event_loop()
    server = ignition.Server(10, logger=logger, loop=loop)
    logger.info("starting to test all")
    status, response = loop.run_until_complete(server.process({
        "language": "python",
        "code": "print('hello world!')",
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
        "language": "c",
        "code": "\n".join(["#include <stdio.h>", 'int main(){printf("Hello World");return 0;}']),
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
        "language": "cpp",
        "code": "\n".join(['#include <iostream>', 'int main() {std::cout << "Hello World"; return 0;}']),
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
        "language": "cs",
        "code": 'class Hello {static void Main(string[] args){System.Console.WriteLine("Hello World!");}}',
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
        "language": "javascript",
        "code": "console.log('hello world!')",
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
        "language": "php",
        "code": "<?php echo 'Hello world!';?>",
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
        "language": "java",
        "code": 'class HelloWorld {public static void main(String[] args) {System.out.println("Hello, World!");}}',
        "args": ""
    }))
    print(status, response)
    status, response = loop.run_until_complete(server.process({
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
        "test-all-async": test_async,
        "build-docker-image": build_docker_image
    }
    mode_help = ", ".join(f"'{mode}'" for mode in modes.keys())
    parser.add_argument("mode", type=str, nargs="?", default="server",
                        help=mode_help)
    parser.add_argument("-p", type=str, nargs="?", default="6090:6096",
                        help="application port.")
    args = parser.parse_args()
    try:
        if args.mode in modes:
            modes[args.mode]()
    except KeyboardInterrupt:
        pass
