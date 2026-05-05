# Clangd Anchors

### 背景

一个项目中的每个编译单元（TU）可能使用不同的编译指令来编译。编译指令包括了编译器、编译选项、宏定义、包含路径等信息，一个语言服务器必须知道了这些信息才能正确地解析和分析代码。

Clangd 如何确定一个文件的编译指令？

1. 先在编译数据库 `compile_commands.json` 里寻找，如果找到了就用它。
2. 如果没找到，则在 `compile_commands.json` 中**启发式**地寻找一个合适的条目，借用它的编译指令来解析当前这个文件。
   一般而言，Clangd 会根据文件名和路径的相似度来挑选条目。

实际上，头文件（`.h`、`.hpp` 等）一般都不会直接出现在 `compile_commands.json` 中，因为它们通常不是独立的编译单元，而是被源文件（`.c`、`.cpp` 等）包含的。

通常，头文件和其对应的源文件成对出现，并且使用相同的命名。所以 Clangd 会找到每个头文件对应的源文件，并使用源文件的编译指令来解析头文件。

对于 header-only 的库（如一些模板库），库中没有源文件，这时 Clangd 就会去找其他文件来借用编译指令了。大部分情况下，项目中不同编译单元的编译指令是相似的，所以不会有太大问题。

但完全可能出现一些情况，Clangd 错误地借用了不合适的编译指令。有不少相关历史讨论：

- [Use parsed files to improve header compile commands](https://github.com/clangd/clangd/issues/123)
- [Source file chosen to infer compile commands for a header sometimes has the wrong language](https://github.com/clangd/clangd/issues/519)
- [Clangd cannot find a header file](https://github.com/clangd/clangd/issues/695)

### 问题

本项目中，由于 FreeRTOS 中出现了和 ETL 中头文件同名的源代码文件（比如 `queue.c` 和 `list.c`），Clangd 错误地使用了 C 编译器来解析 ETL 中的同名头文件，出现了错误。

### 解决方案

我们在本目录中创建同名的空源文件（比如 `queue.cpp` 和 `list.cpp`）。由于本目录路径距离 ETL 中的头文件更近，所以 Clangd 就会优先使用这些空源文件的编译指令来解析 ETL 中的头文件了。
