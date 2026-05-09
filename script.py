#!/usr/bin/env python
"""用于格式化、静态检查及其他代码检查的跨平台脚本。"""

from __future__ import annotations as _annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal, NoReturn, cast

# region 配置

# 用户代码所在的目录（相对于项目根目录）
# 只会处理这些目录下的文件，其他目录（例如 .vscode、.github、build 等）会被忽略
# 新增或移除用户目录时，请修改此处。
USER_DIRS = ("src",)

VALID_SUFFIXES = frozenset((".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx"))

# clang-format 和 clang-tidy 的版本要求（最低大版本号，最高大版本号）
# 使用 None 表示该方向不限制版本
CLANG_FORMAT_VERSION_RANGE: tuple[int | None, int | None] = (18, None)
CLANG_TIDY_VERSION_RANGE: tuple[int | None, int | None] = (18, None)

# clang-tidy 编译数据库（compile_commands.json）所在目录的默认路径（相对于项目根目录）
# EIDE 构建时会在此目录下生成 compile_commands.json。
# 若文件不存在，clang-tidy 将缺少头文件路径和宏定义，导致检查结果不准确。
COMPILE_COMMANDS_PATH = "build/Debug"

# endregion

# region CLI 参数

CommandType = Literal["list", "fmt", "lint", "clean", "check-tools"]


class ParsedArgs(argparse.Namespace):
    command: CommandType
    fix: bool
    clean_all: bool
    clang_format: str
    clang_tidy: str
    quiet: bool
    compile_commands_db: str


def parse_args() -> ParsedArgs:
    parser = argparse.ArgumentParser(description="用于格式化、静态检查及其他代码检查的脚本。")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="静默模式：减少输出信息，fmt fix 时不追踪修改的文件",
    )
    # 设置默认值，使所有子命令都能访问这些属性
    parser.set_defaults(
        fix=False,
        clean_all=False,
        clang_format="clang-format",
        clang_tidy="clang-tidy",
        compile_commands_db=COMPILE_COMMANDS_PATH,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="列出所有用户源文件")

    fmt_parser = subparsers.add_parser("fmt", help="检查或应用 clang-format 格式化")
    fmt_parser.add_argument("--fix", action="store_true", help="应用格式化（默认：仅检查）")
    fmt_parser.add_argument(
        "--clang-format",
        default="clang-format",
        help="clang-format 可执行文件名或路径（默认：clang-format）",
    )

    lint_parser = subparsers.add_parser("lint", help="检查或应用 clang-tidy 静态分析")
    lint_parser.add_argument("--fix", action="store_true", help="应用修复（默认：仅检查）")
    lint_parser.add_argument(
        "--clang-tidy",
        default="clang-tidy",
        help="clang-tidy 可执行文件名或路径（默认：clang-tidy）",
    )
    lint_parser.add_argument(
        "-p",
        "--compile-commands-db",
        default=COMPILE_COMMANDS_PATH,
        metavar="PATH",
        help=f"编译数据库目录或 compile_commands.json 文件路径（默认：{COMPILE_COMMANDS_PATH}）",
    )

    clean_parser = subparsers.add_parser("clean", help="删除构建产物")
    clean_parser.add_argument(
        "-a",
        "--all",
        dest="clean_all",
        action="store_true",
        help="同时删除项目根目录的 .clangd 和 .cache",
    )

    check_tools_parser = subparsers.add_parser(
        "check-tools", help="检查 clang-format 和 clang-tidy 是否可用且版本符合要求"
    )
    check_tools_parser.add_argument(
        "--clang-format",
        default="clang-format",
        help="clang-format 可执行文件名或路径（默认：clang-format）",
    )
    check_tools_parser.add_argument(
        "--clang-tidy",
        default="clang-tidy",
        help="clang-tidy 可执行文件名或路径（默认：clang-tidy）",
    )

    return cast(ParsedArgs, parser.parse_args())


# endregion

# region 辅助函数


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
        print(f"错误：未找到工具 {binary!r}，请确认已安装并在 PATH 中。", file=sys.stderr)
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


def parse_tool_version(version_output: str) -> int | None:
    """从版本输出中解析大版本号。"""
    m = re.search(r"version\s+(\d+)", version_output)
    return int(m.group(1)) if m else None


def check_version_in_range(major: int, version_range: tuple[int | None, int | None]) -> bool:
    """检查大版本号是否在要求的范围内。"""
    lo, hi = version_range
    if lo is not None and major < lo:
        return False
    if hi is not None and major > hi:
        return False
    return True


def format_file_inplace(clang_format: str, file_path: str) -> bool:
    """运行 clang-format 并将输出与原始文件对比，有变化则写回文件。

    仅需运行一次 clang-format 即可同时完成格式化和变更检测，返回文件是否被修改。
    """
    path = Path(file_path)
    original = path.read_bytes()
    result = subprocess.run([clang_format, file_path], capture_output=True)
    if result.returncode != 0:
        # clang-format 报错（如文件语法有误），跳过写回，将错误信息输出到 stderr
        sys.stderr.buffer.write(result.stderr)
        return False
    formatted = result.stdout
    if formatted != original:
        path.write_bytes(formatted)
        return True
    return False


# endregion

# region 主要操作


def run_check_tools(clang_format: str, clang_tidy: str) -> NoReturn:
    """检查工具是否可用且版本符合要求。"""
    print("检查工具可用性及版本...\n")
    all_ok = True

    for binary, version_range, label in (
        (clang_format, CLANG_FORMAT_VERSION_RANGE, "clang-format"),
        (clang_tidy, CLANG_TIDY_VERSION_RANGE, "clang-tidy"),
    ):
        lo, hi = version_range
        if lo is not None and hi is not None:
            range_desc = f"[{lo}, {hi}]"
        elif lo is not None:
            range_desc = f">= {lo}"
        elif hi is not None:
            range_desc = f"<= {hi}"
        else:
            range_desc = "不限"

        resolved = shutil.which(binary)
        if not resolved:
            print(f"  ✗ {label}：未找到（{binary!r} 不在 PATH 中）")
            print(f"    → 请安装 {label}（要求版本：{range_desc}）")
            all_ok = False
            continue

        version_result = subprocess.run(
            [resolved, "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        version_str = version_result.stdout.strip()
        major = parse_tool_version(version_str)

        if major is None:
            print(f"  ✗ {label}：无法解析版本号")
            print(f"    版本信息：{version_str}")
            all_ok = False
        elif not check_version_in_range(major, version_range):
            print(f"  ✗ {label}：版本 {major} 不符合要求（要求：{range_desc}）")
            print(f"    当前版本：{version_str}")
            all_ok = False
        else:
            print(f"  ✓ {label}：版本 {major} 符合要求（要求：{range_desc}）")
            print(f"    {version_str}")

        print()

    if all_ok:
        print("所有工具检查通过。")
        sys.exit(0)
    else:
        print("工具检查未通过，请按照上述提示安装或升级相应工具。")
        sys.exit(1)


def run_fmt_check(root: Path, clang_format: str, quiet: bool) -> NoReturn:
    print("检查用户代码格式...")
    files = collect_file_paths_as_posix(root)
    print(f"共找到 {len(files)} 个文件。\n", flush=True)

    failed = 0
    for target_file in files:
        # 静默模式仅需判断通过与否，用 --ferror-limit=1 提前终止检查以提升性能
        args = [clang_format, target_file, "--dry-run", "--Werror"]
        if quiet:
            args.append("--ferror-limit=1")
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            continue

        failed += 1
        print(f"需要格式化：{target_file}", flush=True)
        if not quiet and result.stderr:
            print(result.stderr, end="", flush=True)

    if failed > 0:
        print(f"\n格式检查失败：{failed} 个文件需要格式化。")
        sys.exit(1)

    print("所有文件格式正确。")
    sys.exit(0)


def run_fmt_fix(root: Path, clang_format: str, quiet: bool) -> NoReturn:
    print("格式化用户代码文件...")
    files = collect_file_paths_as_posix(root)
    print(f"共找到 {len(files)} 个文件。\n")

    if quiet:
        # 静默模式：直接使用 -i 原地修改，不追踪修改的文件
        for target_file in files:
            subprocess.run([clang_format, "-i", target_file], check=True)
        print("完成。")
    else:
        # 普通模式：通过比较输出与原文件来判断是否有修改，仅运行一遍
        cnt = 0
        for target_file in files:
            if format_file_inplace(clang_format, target_file):
                cnt += 1
                print(f"已格式化：{target_file}")
        print(f"\n完成，共格式化 {cnt} 个文件。")

    sys.exit(0)


def _prepare_lint_args(root: Path, db_path: str) -> list[str]:
    """组装 clang-tidy 的数据库 / 交叉工具链相关参数。

    包括 -p 指向 compile_commands.json，以及让 clang 找到 ARM GCC 标准库头的开关：
    --target=<triple> 和 --gcc-toolchain=<root>，外加 -Wno-unused-command-line-argument
    用来屏蔽 clang 对 --specs=*.specs 等 GCC-only flag 的"argument unused"警告
    （与 .clang-tidy 中 WarningsAsErrors: "*" 叠加后会变成 error）。
    """
    suppress_unused = "--extra-arg-before=-Wno-unused-command-line-argument"

    resolved = (root / db_path).resolve()
    if not resolved.exists():
        print(
            f"警告：编译数据库路径不存在：{db_path}\n"
            "  clang-tidy 将在缺少编译信息的情况下运行，检查结果可能不准确。\n"
            "  请先构建项目以生成 compile_commands.json，或通过 -p 参数指定正确路径。",
            file=sys.stderr,
        )
        return [suppress_unused]

    args = ["-p", str(resolved)]
    json_file = resolved if resolved.is_file() else resolved / "compile_commands.json"
    args.extend(_detect_cross_toolchain_args(json_file))
    args.append(suppress_unused)
    return args


def _detect_cross_toolchain_args(json_file: Path) -> list[str]:
    """从 compile_commands.json 推断交叉工具链，转成 clang-tidy 的额外参数。

    本来想用 --target=<triple> + --gcc-toolchain=<root> 让 clang 自己定位 GCC 头，
    但 clang ≥ 16 的 BareMetal driver（--target=arm-none-eabi 触发）已不再走 GCC
    发现机制，会忽略 --gcc-toolchain/--gcc-install-dir。所以只能退回到 query-driver：
    跑一次交叉 g++ 拿到系统头列表，再以 --target=<triple> + 一组 -isystem 透传给 clang。

    成功时返回 --target= 加多个 -isystem 的 --extra-arg-before= 列表；无法推断时返回 []。
    """
    if not json_file.is_file():
        return []

    try:
        with json_file.open(encoding="utf-8") as f:
            db = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(db, list):
        return []

    # 优先选 g++ 条目：g++ 的 system include 是 gcc 的超集（多了 c++/...）
    # 找不到 g++ 时退而求其次用 gcc 路径反推 g++（同目录同前缀，把 -gcc 换成 -g++）
    selected: tuple[str, str, list[str]] | None = None
    fallback: tuple[str, str, list[str]] | None = None
    for entry in db:
        if not isinstance(entry, dict):
            continue
        compiler = _extract_compiler(entry)
        if compiler is None:
            continue
        info = _classify_compiler(compiler, entry)
        if info is None:
            continue
        triple, kind, gpp_path, arch_flags = info
        if kind == "g++":
            selected = (triple, gpp_path, arch_flags)
            break
        if fallback is None:
            fallback = (triple, gpp_path, arch_flags)
    chosen = selected or fallback
    if chosen is None:
        return []
    triple, gpp_path, arch_flags = chosen

    includes = _query_gcc_system_includes(gpp_path, arch_flags)
    if not includes:
        return []

    args = [f"--extra-arg-before=--target={triple}"]
    args.extend(f"--extra-arg-before=-isystem{p}" for p in includes)
    return args


def _extract_compiler(entry: dict) -> str | None:
    """从一条 compile_commands.json 记录中取出编译器路径字符串。"""
    args = entry.get("arguments")
    if isinstance(args, list) and args and isinstance(args[0], str):
        return args[0]
    cmd = entry.get("command")
    if isinstance(cmd, str):
        try:
            tokens = shlex.split(cmd, posix=True)
        except ValueError:
            return None
        if tokens:
            return tokens[0]
    return None


def _classify_compiler(
    compiler: str, entry: dict
) -> tuple[str, str, str, list[str]] | None:
    """把一条记录解析成 (target_triple, kind, g++ 路径, 架构 flag 列表)。

    kind 为 'g++' 表示该条本身就是 g++（首选），'gcc' 表示需要把同目录下的 -gcc 换成 -g++。
    非交叉命名或路径解析失败时返回 None。
    """
    path = Path(compiler)
    stem = path.stem  # 顺带去 .exe（Windows）

    kind: str | None = None
    triple: str | None = None
    for suffix, tag in (("-g++", "g++"), ("-gcc", "gcc")):
        if stem.endswith(suffix) and stem != suffix:
            kind = tag
            triple = stem[: -len(suffix)]
            break
    if kind is None or triple is None:
        return None

    if not path.is_absolute():
        resolved = shutil.which(compiler)
        if resolved is None:
            return None
        path = Path(resolved)

    if kind == "gcc":
        gpp_name = path.stem[: -len("-gcc")] + "-g++" + path.suffix
        gpp_path = str(path.with_name(gpp_name))
    else:
        gpp_path = str(path)

    return triple, kind, gpp_path, _extract_arch_flags(entry)


def _extract_arch_flags(entry: dict) -> list[str]:
    """提取条目中的 -m* 架构 flag，用来让 GCC 选对 multilib 变体。"""
    args = entry.get("arguments")
    if isinstance(args, list):
        tokens = [a for a in args if isinstance(a, str)]
    else:
        cmd = entry.get("command")
        if not isinstance(cmd, str):
            return []
        try:
            tokens = shlex.split(cmd, posix=True)
        except ValueError:
            return []
    return [t for t in tokens if t.startswith("-m")]


def _query_gcc_system_includes(gpp: str, arch_flags: list[str]) -> list[str]:
    """跑 g++ -E -Wp,-v 解析其默认系统头搜索路径。

    输入用关闭的 stdin（input=""），无须 /dev/null 或 NUL，跨平台一致。
    """
    try:
        result = subprocess.run(
            [gpp, "-E", "-Wp,-v", "-x", "c++", *arch_flags, "-"],
            input="",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        return []

    paths: list[str] = []
    in_block = False
    for line in result.stderr.splitlines():
        if "#include <...> search starts here:" in line:
            in_block = True
            continue
        if line.startswith("End of search list."):
            break
        if in_block:
            stripped = line.strip()
            if stripped:
                paths.append(stripped)
    return paths


def run_lint_check(root: Path, clang_tidy: str, quiet: bool, compile_commands_db: str) -> NoReturn:
    print("对用户代码文件进行静态分析...")
    files = collect_file_paths_as_posix(root)
    print(f"共找到 {len(files)} 个文件。\n", flush=True)

    lint_args = _prepare_lint_args(root, compile_commands_db)

    failed = 0
    for target_file in files:
        result = subprocess.run(
            [clang_tidy, "--quiet", *lint_args, target_file],
            capture_output=quiet,
            text=True,
        )
        if result.returncode == 0:
            continue

        failed += 1
        if quiet:
            print(f"存在静态分析问题：{target_file}", flush=True)

    if failed > 0:
        print(f"\n静态分析失败：{failed} 个文件存在问题。")
        sys.exit(1)

    print("所有文件通过静态分析。")
    sys.exit(0)


def run_lint_fix(root: Path, clang_tidy: str, quiet: bool, compile_commands_db: str) -> NoReturn:
    print("对用户代码文件应用静态分析修复...")
    files = collect_file_paths_as_posix(root)
    print(f"共找到 {len(files)} 个文件。\n")

    lint_args = _prepare_lint_args(root, compile_commands_db)

    for target_file in files:
        if not quiet:
            print(f"正在处理：{target_file}")

        subprocess.run(
            [clang_tidy, "--fix", "--fix-errors", "--quiet", *lint_args, target_file],
            check=False,
        )

    print("完成。")
    sys.exit(0)


def run_clean(root: Path, clean_all: bool) -> NoReturn:
    targets: list[Path] = [root / "build"]
    if clean_all:
        targets += [root / ".clangd", root / ".cache"]

    for target in targets:
        if not target.exists():
            print(f"跳过（不存在）：{target.relative_to(root)}")
            continue

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        print(f"已删除：{target.relative_to(root)}")

    sys.exit(0)


# endregion

# region 入口点


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
                return run_fmt_fix(root, clang_format, args.quiet)
            return run_fmt_check(root, clang_format, args.quiet)
        case "lint":
            clang_tidy = ensure_tool(args.clang_tidy)
            if args.fix:
                return run_lint_fix(root, clang_tidy, args.quiet, args.compile_commands_db)
            return run_lint_check(root, clang_tidy, args.quiet, args.compile_commands_db)
        case "clean":
            return run_clean(root, args.clean_all)
        case "check-tools":
            return run_check_tools(args.clang_format, args.clang_tidy)


# endregion

if __name__ == "__main__":
    main()
