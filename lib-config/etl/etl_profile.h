#ifndef ETL_PROFILE_H
#define ETL_PROFILE_H

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

#ifdef DEBUG
  #define ETL_THROW_EXCEPTIONS
  #define ETL_LOG_ERRORS
  #define ETL_VERBOSE_ERRORS

  // 检查 push 和 pop 操作是否成功（容器满或空）。
  #define ETL_CHECK_PUSH_POP

#endif

#endif
