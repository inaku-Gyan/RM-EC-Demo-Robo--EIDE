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

CommandType = Literal["list", "fmt", "lint", "clean"]

VerboseLevel = Literal[0, 1, 2, 3]


class ParsedArgs(argparse.Namespace):
    command: CommandType
    fix: bool
    clean_all: bool
    clang_format: str
    clang_tidy: str
    verbose: VerboseLevel


def parse_args() -> ParsedArgs:
    parser = argparse.ArgumentParser(description="A script for formatting, linting, and other checks.")
    parser.add_argument(
        "--verbose",
        choices=VerboseLevel.__args__,
        default=2,
        type=int,
        help="verbosity level",
    )
    # Set defaults so all attributes are always present regardless of which subcommand is used
    parser.set_defaults(fix=False, clean_all=False, clang_format="clang-format", clang_tidy="clang-tidy")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="list all user source files")

    fmt_parser = subparsers.add_parser("fmt", help="check or apply clang-format formatting")
    fmt_parser.add_argument("--fix", action="store_true", help="apply formatting (default: check only)")
    fmt_parser.add_argument(
        "--clang-format",
        default="clang-format",
        help="clang-format executable name or path (default: clang-format)",
    )

    lint_parser = subparsers.add_parser("lint", help="check or apply clang-tidy linting")
    lint_parser.add_argument("--fix", action="store_true", help="apply fixes (default: check only)")
    lint_parser.add_argument(
        "--clang-tidy",
        default="clang-tidy",
        help="clang-tidy executable name or path (default: clang-tidy)",
    )

    clean_parser = subparsers.add_parser("clean", help="remove build artifacts")
    clean_parser.add_argument(
        "-a",
        "--all",
        dest="clean_all",
        action="store_true",
        help="also remove .clangd and .cache from the project root",
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


def ensure_tool(binary: str) -> str:
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


def run_fmt_check(root: Path, clang_format: str, verbose: VerboseLevel) -> NoReturn:
    print("Checking user code format...")
    files = collect_file_paths_as_posix(root)
    print(f"{len(files)} files found.\n", flush=True)  # 刷新一下，避免 subprocess 的输出出现在这行之前

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


def run_fmt_fix(root: Path, clang_format: str, verbose: VerboseLevel) -> NoReturn:
    print("Formatting user code files...")
    files = collect_file_paths_as_posix(root)
    print(f"{len(files)} files found.\n")

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


def run_lint_check(root: Path, clang_tidy: str, verbose: VerboseLevel) -> NoReturn:
    print("Linting user code files...")
    files = collect_file_paths_as_posix(root)
    print(f"{len(files)} files found.\n", flush=True)  # 刷新一下，避免 subprocess 的输出出现在这行之前

    failed = 0
    for target_file in files:
        if verbose == 3:
            print(f"Checking: {target_file}", flush=True)

        result = subprocess.run(
            [clang_tidy, "--quiet", target_file],
            capture_output=(verbose < 2),
            text=True,
        )

        if result.returncode == 0:
            continue  # No issues

        failed += 1

        if verbose == 1:
            print(f"Lint issues found: {target_file}", flush=True)
        elif verbose >= 2 and result.returncode != 0:
            # 当 capture_output=False 时输出已直接流向终端，此处无需重复打印
            pass

    if (verbose > 0 and failed > 0) or verbose == 3:
        print()

    if failed > 0:
        print(f"Lint check failed: {failed} file(s) have issues.")
        sys.exit(1)

    print("All files passed lint checks.")
    sys.exit(0)


def run_lint_fix(root: Path, clang_tidy: str, verbose: VerboseLevel) -> NoReturn:
    print("Applying lint fixes to user code files...")
    files = collect_file_paths_as_posix(root)
    print(f"{len(files)} files found.\n")

    for target_file in files:
        if verbose >= 2:
            print(f"Linting: {target_file}")

        subprocess.run(
            [clang_tidy, "--fix", "--fix-errors", "--quiet", target_file],
            check=False,
        )

    print("Done.")
    sys.exit(0)


def run_clean(root: Path, clean_all: bool) -> NoReturn:
    targets: list[Path] = [root / "build"]
    if clean_all:
        targets += [root / ".clangd", root / ".cache"]

    for target in targets:
        if not target.exists():
            print(f"Skipped (not found): {target.relative_to(root)}")
            continue

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        print(f"Removed: {target.relative_to(root)}")

    sys.exit(0)


# endregion

# region Entry Point


def main() -> NoReturn:
    args = parse_args()
    root = project_root()

    match args.command:
        case "list":
            for file in collect_file_paths_as_posix(root):
                print(file)
            sys.exit(0)
        case "fmt":
            clang_format = ensure_tool(args.clang_format)
            if args.fix:
                return run_fmt_fix(root, clang_format, args.verbose)
            return run_fmt_check(root, clang_format, args.verbose)
        case "lint":
            clang_tidy = ensure_tool(args.clang_tidy)
            if args.fix:
                return run_lint_fix(root, clang_tidy, args.verbose)
            return run_lint_check(root, clang_tidy, args.verbose)
        case "clean":
            return run_clean(root, args.clean_all)


# endregion

if __name__ == "__main__":
    main()
