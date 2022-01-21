from typing import *
import asyncio
from pathlib import Path
from uuid import uuid4
from .protocol import Response
from time import perf_counter_ns


async def process(stdin: str):
    return await (await asyncio.create_subprocess_exec(
        *stdin.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )).communicate()


async def shell(commands: List[str]):
    while commands and len(commands) > 1:
        await process(commands.pop(0))
    start = perf_counter_ns()
    stdout, stderr = await process(commands.pop(0))
    end = perf_counter_ns()
    return create_result(stdout, stderr, end - start)


def create_result(stdout: Optional[bytes], stderr: Optional[bytes], time: float) -> Response:
    return {
        "stdout": stdout.decode("utf-8") if stdout else None,
        "stderr": stderr.decode("utf-8") if stderr else None,
        "ns": time
    }


class LanguageMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls.languages = {
            attr: value.__func__
            for attr, value in dct.items()
            if not (attr.startswith("__") and attr.endswith("__"))
        }

    def __contains__(cls, item) -> bool:
        return item in cls.languages

    def __getitem__(cls, language) -> Callable[[Path, str], Response]:
        return cls.languages[language]


class Languages(metaclass=LanguageMeta):
    @staticmethod
    async def php(file: Path, sys_args: str) -> Response:
        return await shell([
            f"php -f {file} {sys_args}"
        ])

    @staticmethod
    async def java(file: Path, sys_args: str) -> Response:
        return await shell([
            f"java {file} {sys_args}"
        ])

    @staticmethod
    async def javascript(file: Path, sys_args: str) -> Response:
        return await shell([
            f"node {file} {sys_args}"
        ])

    @staticmethod
    async def go(file: Path, sys_args: str) -> Response:
        return await shell([
            f"go run {file} {sys_args}"
        ])

    @staticmethod
    async def cpp(file: Path, sys_args: str) -> Response:
        return await shell([
            f"g++ -o {(executable := file.parent.joinpath(str(uuid4())))} {file}",
            f"{executable} {sys_args}"
        ])

    @staticmethod
    async def cs(file: Path, sys_args: str) -> Response:
        return await shell([
            f"dotnet new console --output {(project := file.parent.joinpath('cs'))}",
            f"mv {file} {project.joinpath('Program.cs')}",  # overwrite the generated file with the real file
            f"dotnet run --project {project} {sys_args}"
        ])

    @staticmethod
    async def python(file: Path, sys_args: str) -> Response:
        return await shell([
            f"python3 {file} {sys_args}"
        ])

    @staticmethod
    async def c(file: Path, sys_args: str) -> Response:
        return await shell([
            f"gcc -o {(executable := file.parent.joinpath(str(uuid4())))} {file}",
            f"{executable} {sys_args}"
        ])

    @staticmethod
    async def typescript(file: Path, args: str) -> Response:
        return await shell([
            f"deno run {file} {args}"
        ])
