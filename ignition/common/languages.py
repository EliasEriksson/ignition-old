from typing import *
import asyncio
from pathlib import Path
from uuid import uuid4
from .protocol import Response
from time import perf_counter_ns


async def process(stdin: str) -> Tuple[bytes, bytes]:
    """
    helper method to easily use a string as parameter for the subprocess.
    """
    return await (await asyncio.create_subprocess_exec(
        *stdin.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )).communicate()


async def shell(commands: List[str]) -> Response:
    """
    runs a list of shell commands.

    runs all commands in the given list of commands.
    the last command is timed and stdout and stderr is captured
    to be returned as a protocol.Response object
    """
    while commands and len(commands) > 1:
        await process(commands.pop(0))
    start = perf_counter_ns()
    stdout, stderr = await process(commands.pop(0))
    end = perf_counter_ns()
    return create_result(stdout, stderr, end - start)


def create_result(stdout: Optional[bytes], stderr: Optional[bytes], time: int) -> Response:
    """
    helper method to easily convert parameters to a Response.

    used to convert tuples with stdout, stderr and time to a protocol.Response formed dictionary.
    """
    return {
        "stdout": stdout.decode("utf-8") if stdout else None,
        "stderr": stderr.decode("utf-8") if stderr else None,
        "ns": time
    }


class LanguageMeta(type):
    """
    metaclass for the Language class bellow.

    creates a language dictionary attribute on the class
    in which all the class attributes not starting and ending with __ is stored.

    this allows a nice API to work with the Language class and to add a new language
    a static method is added and the rest is sorted automagically.
    """

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls.languages = {
            attr: value.__func__
            for attr, value in dct.items()
            if not (attr.startswith("__") and attr.endswith("__"))
        }

    def __contains__(cls, item) -> bool:
        """
        implements __contains__ on a class level .

        queries the language attribute set up in __init__.
        """
        return item in cls.languages

    def __getitem__(cls, language) -> Callable[[Path, str], Response]:
        """
        implements __getitem__ on a class level.

        queries the language attribute set up in __init__.
        """
        return cls.languages[language]


class Languages(metaclass=LanguageMeta):
    """
    Class holding procedures to all supported languages.

    to add support for a language create a new static method with the language name,
    use the shell function to define commands in the order they should run.

    the last command in the list of commands in the shell function must be the
    command that executes the program.

    the file parameter in the method is the file where the source code is located.
    """

    @staticmethod
    async def php(file: Path, sys_args: str) -> Response:
        """
        procedure for php
        """
        return await shell([
            f"php -f {file} {sys_args}"
        ])

    @staticmethod
    async def java(file: Path, sys_args: str) -> Response:
        """
        procedure for java
        """
        return await shell([
            f"java {file} {sys_args}"
        ])

    @staticmethod
    async def javascript(file: Path, sys_args: str) -> Response:
        """
        procedure for javascript using node.js
        """
        return await shell([
            f"node {file} {sys_args}"
        ])

    @staticmethod
    async def go(file: Path, sys_args: str) -> Response:
        """
        procedure for go
        """
        return await shell([
            f"go run {file} {sys_args}"
        ])

    @staticmethod
    async def cpp(file: Path, sys_args: str) -> Response:
        """
        procedure for c++
        """
        return await shell([
            f"g++ -o {(executable := file.parent.joinpath(str(uuid4())))} {file}",
            f"{executable} {sys_args}"
        ])

    @staticmethod
    async def cs(file: Path, sys_args: str) -> Response:
        """
        procedure for C#
        """
        return await shell([
            f"mv {file} {(project := Path('/cs')).joinpath('Program.cs')}",  # move to prepared console project
            f"dotnet run --project {project} {sys_args}"
        ])

    @staticmethod
    async def python(file: Path, sys_args: str) -> Response:
        """
        procedure for python
        """
        return await shell([
            f"python3 {file} {sys_args}"
        ])

    @staticmethod
    async def c(file: Path, sys_args: str) -> Response:
        """
        procedure for C
        """
        return await shell([
            f"gcc -o {(executable := file.parent.joinpath(str(uuid4())))} {file}",
            f"{executable} {sys_args}"
        ])

    @staticmethod
    async def typescript(file: Path, args: str) -> Response:
        """
        procedure for typescript using Deno
        """
        return await shell([
            f"deno run {file} {args}"
        ])
