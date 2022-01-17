from typing import *
import asyncio
from pathlib import Path
from uuid import uuid4
from .protocol import Response
from time import perf_counter_ns


async def subprocess(stdin: str) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_exec(
        *stdin.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )


def create_result(status: int, stdout: Optional[bytes], stderr: Optional[bytes], time: float) -> Response:
    return {
        "status": status,
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
    async def php(file: Path, sys_args: str) -> bytes:
        process = await subprocess(f"php -f {file} {sys_args}")
        stdout, stderr = await process.communicate()
        return stdout if process.returncode == 0 else stderr

    @staticmethod
    async def java(file: Path, sys_args: str) -> bytes:
        process = await subprocess(f"java {file} {sys_args}")
        stdout, stderr = await process.communicate()
        return stdout if process.returncode == 0 else stderr

    @staticmethod
    async def javascript(file: Path, sys_args: str) -> bytes:
        process = await subprocess(f"node {file} {sys_args}")
        stdout, stderr = await process.communicate()
        return stdout if process.returncode == 0 else stderr

    @staticmethod
    async def go(file: Path, sys_args: str) -> bytes:
        process = await subprocess(f"go run {file} {sys_args}")
        stdout, stderr = await process.communicate()
        return stdout if process.returncode == 0 else stderr

    @staticmethod
    async def cpp(file: Path, sys_args: str) -> bytes:
        executable = file.parent.joinpath(str(uuid4()))
        process = await subprocess(f"g++ -o {executable} {file} {sys_args}")
        _, stderr = await process.communicate()
        if not process.returncode == 0:
            return stderr

        process = await subprocess(f"{executable}")
        stdout, stderr = await process.communicate()
        return stdout if process.returncode == 0 else stderr

    @staticmethod
    async def cs(file: Path, sys_args: str) -> bytes:
        cs_project = file.parent.joinpath("cs")

        process = await subprocess(f"dotnet new console --output {cs_project}")
        _, stderr = await process.communicate()
        if not process.returncode == 0:
            return stderr

        process = await subprocess(f"mv {file} {cs_project.joinpath(file.name)}")
        _, stderr = await process.communicate()
        if not process.returncode == 0:
            return stderr

        process = await subprocess(f"rm {cs_project.joinpath('Program.cs')}")
        _, stderr = await process.communicate()
        if not process.returncode == 0:
            return stderr

        process = await subprocess(f"dotnet run --project {cs_project} {sys_args}")
        stdout, stderr = await process.communicate()
        return stdout if process.returncode == 0 else stderr

    @staticmethod
    async def python(file: Path, sys_args: str) -> Response:
        start = perf_counter_ns()
        process = await subprocess(f"python3 {file} {sys_args}")
        end = perf_counter_ns()
        return create_result(
            process.returncode,
            *await process.communicate(),
            time=end - start
        )

    @staticmethod
    async def c(file: Path, sys_args: str) -> bytes:
        executable = file.parent.joinpath(str(uuid4()))
        process = await subprocess(f"gcc -o {executable} {file} {sys_args}")
        _, stderr = await process.communicate()
        if not process.returncode == 0:
            return stderr

        process = await subprocess(f"{executable}")
        stdout, stderr = await process.communicate()
        if not process.returncode == 0:
            return stderr
        return stdout
