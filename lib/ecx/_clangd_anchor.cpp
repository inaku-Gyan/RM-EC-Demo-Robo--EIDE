// clangd interpolation anchor —— 不是给运行时用的，是给 IDE 用的。
//
// 背景：lib/ecx/ 是 header-only 中间件，没有任何 .cpp。clangd 处理 header
// 文件时依赖 compile_commands.json 找编译参数；找不到时回退到默认 flag
// （host clang，无 stdlib），就会报 "Use of undeclared identifier 'std'"
// 之类的假错。clangd 的 interpolation 启发式会按路径相似度从已知 .cpp
// 里挑最近的来"借用"参数——只要 lib/ecx/ 下存在任意一个 .cpp 条目，
// 子目录里的所有 .hpp 就都能正确解析。
//
// 这个文件就是那个"任意 .cpp"。保持空文件即可：
//   * 编译产物为空 .o；
//   * 没有外部符号 → 链接器死代码消除直接丢弃；
//   * 也不会触发 -Wall/-Werror、clang-tidy 任何检查。
//
// 以后若 lib/ 下再加 header-only 子库（如 lib/foo/），clangd 同样能借用
// 本文件的参数（路径前缀 lib/ 仍最近），无需新增 anchor。
