import argparse
import logging
import os
from pathlib import Path
import ignition
import asyncio
import subprocess
import uvicorn
import enum
import sql


logger = ignition.get_logger(__name__, logging.INFO, stdout=True)


class LogLevel(enum.Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"

    def __str__(self):
        return self.value


def process(stdin: str) -> str:
    p = subprocess.run(stdin.split())
    return (
        (p.stdout.decode("utf-8") if p.stdout else "")
        if p.returncode == 0 else
        (p.stderr.decode("utf-8") if p.stderr else "")
    )


def start_client(_args):
    loop = asyncio.get_event_loop()
    client = ignition.Client(loop)
    loop.run_until_complete(client.run())


def start_server(_args):
    kwargs = {
        "port": _args.port,
        "proxy_headers": True,
        "forwarded_allow_ips": "*"
    }
    if _args.dev:
        kwargs["reload"] = True

    uvicorn.run(
        "app:app", **kwargs
    )


def test(_args):
    async def _test():
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

    asyncio.run(_test())


def db(_args):
    sql.models.Base.metadata.create_all(bind=sql.database.engine)


def build_docker_image(_args):
    process(f"docker build --tag ignition {Path(__file__).parent}")


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser()

    sub_parsers = parser.add_subparsers(dest="mode")

    docker_parser = sub_parsers.add_parser(
        "build-docker-image", help="building the docker image.")

    server_parser = sub_parsers.add_parser(
        "server", help="start ignitions webserver.")
    server_parser.add_argument(
        "--port", type=int, default=8080, help="port for the webserver.")
    server_parser.add_argument(
        "--dev", action="store_true", help="start a development server.")

    client_parser = sub_parsers.add_parser(
        "client", help="starts a ignition client (internal use).")

    test_parser = sub_parsers.add_parser(
        "test", help="test the ignition internals.")
    test_parser.add_argument("--app-port", type=int, help="port for ignitions internal use.")

    db_parser = sub_parsers.add_parser(
        "db", help="CLI utility for managing the database.")
    db_sub_parser = db_parser.add_subparsers(dest="db_mode")
    db_init_parser = db_sub_parser.add_parser("init", help="initializes the database.")

    modes = {
        "build-docker-image": lambda _args: build_docker_image(_args),
        "server": lambda _args: start_server(_args),
        "client": lambda _args: start_client(_args),
        "test": lambda _args: test(_args),
        "db": lambda _args: db(_args)
    }
    modes[(args := parser.parse_args()).mode](args)
