from typing import *
import asyncio
from pathlib import Path
from uuid import uuid4
from enum import Enum


async def subprocess(stdin: str) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_exec(
        *stdin.split(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )


async def php(file: Path, sys_args: str) -> bytes:
    process = await subprocess(f"php -f {file} {sys_args}")
    stdout, stderr = await process.communicate()
    return stdout if process.returncode == 0 else stderr


async def java(file: Path, sys_args: str) -> bytes:
    process = await subprocess(f"java {file} {sys_args}")
    stdout, stderr = await process.communicate()
    return stdout if process.returncode == 0 else stderr


async def javascript(file: Path, sys_args: str) -> bytes:
    process = await subprocess(f"node {file} {sys_args}")
    stdout, stderr = await process.communicate()
    return stdout if process.returncode == 0 else stderr


async def go(file: Path, sys_args: str) -> bytes:
    process = await subprocess(f"go run {file} {sys_args}")
    stdout, stderr = await process.communicate()
    return stdout if process.returncode == 0 else stderr


async def cpp(file: Path, sys_args: str) -> bytes:
    executable = file.parent.joinpath(str(uuid4()))
    process = await subprocess(f"g++ -o {executable} {file} {sys_args}")
    _, stderr = await process.communicate()
    if not process.returncode == 0:
        return stderr

    process = await subprocess(f"{executable}")
    stdout, stderr = await process.communicate()
    return stdout if process.returncode == 0 else stderr


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


async def python(file: Path, sys_args: str) -> bytes:
    process = await subprocess(f"python3 {file} {sys_args}")
    stdout, stderr = await process.communicate()
    return stdout if process.returncode == 0 else stderr


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


languages = {
    "php": php,
    "java": java,
    "javascript": javascript,
    "js": javascript,
    "go": go,
    "cpp": cpp,
    "cs": cs,
    "python": python,
    "py": python,
    "python3": python,
    "c": c
}
