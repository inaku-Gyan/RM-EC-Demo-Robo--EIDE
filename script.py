#!/usr/bin/env python
"""Cross-platform script for formatting, linting, and other checks."""

from __future__ import annotations as _annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal, NoReturn, cast

# region Configuration

# 用户代码所在的目录（相对于项目根目录）
# 只会处理这些目录下的文件，其他目录（例如 .vscode、.github、build 等）会被忽略
# 新增或移除用户目录时，请修改此处。
USER_DIRS = ("src", "lib")

VALID_SUFFIXES = frozenset((".c", ".h", ".cpp", ".hpp"))

# endregion

# region CLI Argument

ActionType = Literal["list", "check", "format"]

VerboseLevel = Literal[0, 1, 2, 3]


class ParsedArgs(argparse.Namespace):
    action: ActionType
    clang_format: str
    verbose: VerboseLevel


def parse_args() -> ParsedArgs:
    parser = argparse.ArgumentParser(description="A script for formatting, linting, and other checks.")
    parser.add_argument(
        "action",
        choices=ActionType.__args__,
        help="list files, check formatting, or apply formatting",
    )
    parser.add_argument(
        "--clang-format",
        default="clang-format",
        help="clang-format executable name or path (default: clang-format)",
    )
    parser.add_argument(
        "--verbose",
        choices=VerboseLevel.__args__,
        default=2,
        type=int,
        help="verbosity level",
    )
    return cast(ParsedArgs, parser.parse_args())


# endregion

# region Helper Functions


def project_root() -> Path:
    return Path(__file__).resolve().parent


def collect_file_paths(root: Path) -> list[Path]:
    files: list[Path] = []
    for user_dir in USER_DIRS:
        base = root / user_dir
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in VALID_SUFFIXES:
                files.append(path)
    files.sort(key=lambda p: p.relative_to(root).as_posix())
    return files


def collect_file_paths_as_posix(root: Path) -> tuple[str, ...]:
    return tuple(path.relative_to(root).as_posix() for path in collect_file_paths(root))


def ensure_clang_format(binary: str) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        print(f"ERROR: {binary} not found!", file=sys.stderr)
        sys.exit(1)

    version = subprocess.run(
        [resolved, "--version"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(version.stdout.strip())
    return resolved


def quick_check(clang_format: str, target_file: str) -> bool:
    result = subprocess.run(
        [clang_format, target_file, "--dry-run", "--Werror", "--ferror-limit=1"],
        capture_output=True,
    )
    return result.returncode == 0


# endregion

# region Main Actions


def run_check(root: Path, clang_format: str, verbose: VerboseLevel) -> NoReturn:
    print("Checking user code format...")
    files = collect_file_paths_as_posix(root)
    print(f"{len(files)} files Found.\n", flush=True)  # 刷新一下，避免 subprocess 的输出出现在这行之前

    failed = 0
    for target_file in files:
        if verbose == 3:
            print(f"Checking: {target_file}", flush=True)

        if quick_check(clang_format, target_file):
            continue  # Already formatted

        failed += 1

        if verbose == 1:
            print(f"Needs formatting: {target_file}", flush=True)
        elif verbose >= 2:
            #  重新执行以输出彩色错误信息
            subprocess.run(
                # 当 verbose == 3 时，不限制 clang-format 输出错误数量（即设为 0）
                [clang_format, target_file, "--dry-run"],
                text=True,
            )

    if (verbose > 0 and failed > 0) or verbose == 3:
        print()

    if failed > 0:
        print(f"Format check failed: {failed} file(s) need formatting.")
        sys.exit(1)

    print("All files are properly formatted.")
    sys.exit(0)


def run_format(root: Path, clang_format: str, verbose: VerboseLevel) -> NoReturn:
    print("Formatting user code files...")
    files = collect_file_paths_as_posix(root)
    print(f"{len(files)} files Found.\n")

    cnt = 0

    for target_file in files:
        if verbose >= 1:
            # Check
            if verbose == 3:
                print(f"Checking: {target_file}")

            if quick_check(clang_format, target_file):
                continue  # Already formatted

            cnt += 1

        if verbose >= 2:
            print(f"Formatting: {target_file}")

        subprocess.run([clang_format, "-i", target_file], check=True)

    if verbose == 0:
        print("Done.")
    else:
        print(f"Done. Formatted {cnt} files.")

    sys.exit(0)


# endregion

# region Entry Point


def main() -> NoReturn:
    args = parse_args()
    root = project_root()
    clang_format = ensure_clang_format(args.clang_format)

    match args.action:
        case "list":
            for file in collect_file_paths_as_posix(root):
                print(file)
            sys.exit(0)
        case "format":
            return run_format(root, clang_format, args.verbose)
        case "check":
            return run_check(root, clang_format, args.verbose)


# endregion

if __name__ == "__main__":
    main()
