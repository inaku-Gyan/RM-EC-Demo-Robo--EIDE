# RM-EC-Demo-Robo

基于 STM32F407 的 RoboMaster 电控示例工程，使用 VS Code + EIDE 插件开发，以 C/C++ 混合编写。

---

## 目录结构

```
RM-EC-Demo-Robo--EIDE/
├── bsp/                    # 板级支持包（BSP）
│   ├── CubeMX/             # 由 STM32CubeMX 自动生成（HAL、FreeRTOS、USB 等）
│   └── bsp_interface.h     # BSP 接口声明
├── lib/                    # 外部库
│   ├── ecx/                # 内部公共库（算法、协议、RTOS 封装等）
│   └── etl/                # Embedded Template Library（Git Submodule）
├── lib-config/             # 外部库的配置文件（如 ETL 用户配置）
├── src/                    # 项目主体业务代码
│   ├── comm/               # 通信相关
│   ├── tasks/              # FreeRTOS 任务
│   └── entry.cpp           # 程序入口
├── .clang-format           # clang-format 格式化规则
├── .clang-tidy             # clang-tidy 静态分析规则
├── .eide/                  # EIDE 项目配置（目标、工具链、烧录等）
├── RMEC.code-workspace     # VS Code 工作区配置
└── script.py               # 格式化与静态分析辅助脚本
```

**代码开发时的注意事项：**

- `src/` 是本项目主体业务代码，所有格式化和静态分析**只作用于此目录**。
- `lib/` 中的是外部库，一般不直接修改，按需通过 `lib-config/` 提供配置。
- `bsp/CubeMX/` 由 STM32CubeMX 自动生成，开发时应尽量减少手动修改，避免 CubeMX 重新生成时产生冲突。

---

## 开发环境要求

### 必须安装

| 工具 | 说明 | 获取方式 |
| --- | --- | --- |
| **VS Code** | 编辑器 | [code.visualstudio.com](https://code.visualstudio.com) |
| **EIDE**（Embedded IDE） | VS Code 嵌入式开发插件，管理工具链、构建和烧录 | VS Code 扩展市场搜索 `EIDE` |
| **ARM GCC 工具链** | 交叉编译器（`arm-none-eabi-gcc`） | 通过 EIDE 插件下载 |
| **OpenOCD** | 烧录 / 调试工具，支持 CMSIS-DAP 调试器 | 通过 EIDE 插件下载 |
| **Python ≥ 3.10** | 运行 `script.py` 所需 | [python.org](https://www.python.org) |

### 需自行安装（不由 EIDE 管理）

| 工具 | 版本要求 | 说明 |
| --- | --- | --- |
| **clang-format** | ≥ 18 | 代码格式化 |
| **clang-tidy** | ≥ 18 | 静态代码分析 |

> 推荐通过系统包管理器安装，例如：
> - **Ubuntu/Debian**：`sudo apt install clang-format-18 clang-tidy-18`
> - **macOS**：`brew install llvm`（安装后需将 `/opt/homebrew/opt/llvm/bin` 加入 `PATH`）
> - **Windows**：从 [LLVM 官方发布页](https://github.com/llvm/llvm-project/releases) 下载安装包

安装完成后可运行以下命令验证版本：

```bash
python script.py check-tools
```

---

## Git Submodule

本项目使用 Git Submodule 引入 ETL（`lib/etl`）。

**首次克隆后初始化 submodule：**

```bash
git clone --recurse-submodules <repo-url>
# 或克隆后再初始化：
git submodule update --init --recursive
```

**更新 submodule 到最新版本：**

```bash
git submodule update --remote
```

---

## 构建与烧录

本项目通过 **EIDE 插件**管理构建和烧录，无需手动调用编译器。

1. 在 VS Code 中打开工作区（`RMEC.code-workspace`）。
2. 在 EIDE 面板中选择目标（`Debug`）并点击 **Build** 构建。
3. 构建成功后，EIDE 会在 `build/Debug/` 目录下生成 `compile_commands.json`，供 clangd 和 `script.py lint` 使用。
4. 使用 CMSIS-DAP 调试器连接硬件后，点击 **Upload** 烧录固件。

---

## `script.py` 使用说明

`script.py` 是一个跨平台辅助脚本，用于对 `src/` 目录下的用户代码进行格式化和静态分析。

```
usage: script.py [-q] {list,fmt,lint,clean,check-tools} ...
```

全局选项：

| 选项 | 说明 |
| --- | --- |
| `-q`, `--quiet` | 静默模式：减少输出，`fmt --fix` 时不追踪已修改的文件 |

---

### `list` — 列出所有用户源文件

```bash
python script.py list
```

---

### `fmt` — 代码格式化（clang-format）

```bash
# 仅检查，不修改（默认）
python script.py fmt

# 自动修复格式问题
python script.py fmt --fix

# 指定 clang-format 可执行文件路径
python script.py fmt --clang-format clang-format-18
```

---

### `lint` — 静态分析（clang-tidy）

> **依赖编译数据库**：`clang-tidy` 需要 `compile_commands.json` 才能正确解析头文件和宏定义。请在 EIDE 中至少执行一次构建，以便在 `build/Debug/` 下生成该文件。

```bash
# 仅检查（默认从 build/Debug/ 加载编译数据库）
python script.py lint

# 自动修复可修复的问题
python script.py lint --fix

# 指定编译数据库路径（目录或 compile_commands.json 文件）
python script.py lint -p build/Debug

# 指定 clang-tidy 可执行文件路径
python script.py lint --clang-tidy clang-tidy-18
```

| 选项 | 说明 |
| --- | --- |
| `--fix` | 应用可自动修复的建议 |
| `-p PATH`, `--compile-commands-db PATH` | 编译数据库目录或 `compile_commands.json` 文件路径（默认：`build/Debug`） |
| `--clang-tidy PATH` | 指定 clang-tidy 可执行文件（默认：`clang-tidy`） |

---

### `clean` — 删除构建产物

```bash
# 删除 build/ 目录
python script.py clean

# 同时删除 .clangd/ 和 .cache/（LSP 缓存）
python script.py clean --all
```

---

### `check-tools` — 检查工具版本

```bash
python script.py check-tools

# 指定可执行文件路径
python script.py check-tools --clang-format clang-format-18 --clang-tidy clang-tidy-18
```

---

## 编译选项说明

### C++ 特有

| 选项 | 说明 | 备注 |
| :-: | --- | :-: |
| `-D__PROGRAM_START` | 跳过 CMSIS V5.4.1 `cmsis_gcc.h` 的 `__cmsis_start`。该函数内使用局部类型声明 extern 变量，无法通过 C++ 编译。 | |
| `-fno-rtti` | 禁用 C++ 运行时类型信息 (RTTI)。 | EIDE 自带开关控制 |
| `-fno-exceptions` | 禁用 C++ 异常处理机制。 | EIDE 自带开关控制 |
| `-fno-threadsafe-statics` | 禁用线程安全的静态变量初始化。 | EIDE 自带开关控制 |
| `-fno-use-cxa-atexit` | 禁用使用 `__cxa_atexit` 函数来注册静态对象的析构函数。 | EIDE 自带开关控制 |

