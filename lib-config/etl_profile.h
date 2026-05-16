#pragma once

/**
 * @file ETL configuration file.
 *
 * 具体配置项目参考：
 *     https://www.etlcpp.com/macros.html
 *
 */

// 选择不使用 STL，而是使用 ETL 自己的实现。
// 参考: https://www.etlcpp.com/no_stl.html
#define ETL_NO_STL

// 选择编译器。ETL 会根据编译器自动检测，但也可以手动指定。
// 这里手动指定的目的是让 clangd 语言服务器也能正确识别编译器。
// 否则 clangd 中，ETL 会推断编译器为 clang，而不是 gcc，导致一些编译器特定的代码无法正确解析。
// 实际编译时，使用 gcc 编译器，ETL 会正确识别，故不手动指定也不会有问题。
#define ETL_COMPILER_GCC

////////////////////////////////////////
////////////// Debug 配置 //////////////
///////////////////////////////////////

#ifdef DEBUG

// 由于我们禁用了 C++ 的异常处理机制，所以这里不能启用 ETL_THROW_EXCEPTIONS
// #define ETL_THROW_EXCEPTIONS

  #define ETL_LOG_ERRORS
  #define ETL_VERBOSE_ERRORS

  // 检查 push 和 pop 操作是否成功（容器满或空）。
  #define ETL_CHECK_PUSH_POP

#endif
