# RM-EC-Demo-Robo

基于 STM32F407 的 RoboMaster 电控示例工程，使用 VS Code + EIDE 插件开发，以 C/C++ 混合编写。

---

本仓库使用了 Git Submodule 引入部分外部库。仓库拉取方法见 [Git Submodule 相关说明](docs/git-submodule.md)。

## 目录结构

```
/
├── bsp/                    # 板级支持包（BSP）
│   ├── CubeMX/             # 由 STM32CubeMX 自动生成（HAL、FreeRTOS、USB 等）
│   └── ...                 # BSP 接口声明等，用于桥接 CubeMX 代码
├── lib/                    # 外部库
│   ├── ecx/                # 内部公共库（算法、协议、RTOS 封装等）（Git Submodule）
│   ├── etl/                # Embedded Template Library（Git Submodule）
│   └── ...
├── lib-config/             # 外部库的配置文件（如 ETL 用户配置）
│   ├── ecx/
│   ├── etl/
│   └── ...
├── src/                    # 项目主体业务代码
│   ├── tasks/              # RTOS 任务
│   └── ...
├── ...
├── .eide/                  # EIDE 项目配置（目标、工具链、烧录等）
├── xxx.code-workspace      # VS Code 工作区配置
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
| 其他工作区推荐的扩展 | 提供语言服务、调试、串口监控等功能 | 详见 VS Code 工作区配置文件 |
| **ARM GCC 工具链** | 交叉编译器（`arm-none-eabi-gcc`） | 通过 EIDE 插件下载 |
| **OpenOCD** | 烧录 / 调试工具，支持 CMSIS-DAP 调试器 | 通过 EIDE 插件下载 |
| **Python ≥ 3.10** | 运行 `script.py` 所需 | [python.org](https://www.python.org) 或 [uv](https://docs.astral.sh/uv/) |

推荐使用 VS Code 的 **配置文件（Profile）** 功能安装工作区插件，这样可以在不同的项目间实现隔离，互不干扰。

#### 语言服务

本项目配置使用 LLVM 的 [clangd 扩展](https://marketplace.visualstudio.com/items?itemName=llvm-vs-code-extensions.vscode-clangd)提供 C/C++ 语言服务。该插件与[微软的 C/C++](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools)扩展相冲突，故请禁用或卸载后者。

与微软的 C/C++ 扩展相比，clangd 提供了更智能的代码分析、语法跳转、重构等功能，并兼具格式化、lint 检查功能。

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
python3 script.py check-tools
```

---

## 构建与烧录

本项目通过 **EIDE 插件**管理构建和烧录，无需手动调用编译器。

1. 在 VS Code 中打开工作区（`.code-workspace` 文件）。
2. 在 EIDE 面板中选择目标（`Debug` 或 `Release`）并点击 **Build** 构建。
3. 构建成功后，EIDE 会生成 `compile_commands.json`，供 clangd 和 clang-tidy 使用。
4. 使用 CMSIS-DAP 调试器连接硬件后，通过 EIDE 烧录固件。

---

## `script.py` 使用说明

`script.py` 是一个跨平台辅助脚本，用于对用户代码进行格式化和静态分析。

```bash
# 列出所有参数选项说明
python3 ./script.py -h

# 对特定的命令列出选项说明
python3 ./script.py fmt -h

# 如果你使用 uv，请使用脚本模式运行（`-s`）
uv run -s ./script.py -h
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

