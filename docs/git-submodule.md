# Git Submodule

Git Submodule 是 Git 的一个功能，它允许你将一个 Git 仓库作为另一个 Git 仓库的子目录。本项目中 Git Submodule 被用于引入一些外部库。

## 推荐的 Git 配置

以下大量命令中都会用到 `--recurse-submodules` 选项。可以使用如下命令来设置 Git 使其默认启用该选项，这样就不用每次都手动指定：

```bash
git config --global submodule.recurse true
```

上述配置会让 Git 对除了 `git clone` 以外的所有拥有 `--recurse-submodules` 选项的命令都默认启用该选项。

## 仓库克隆和初始化 Submodule

使用如下命令克隆主仓库：

```bash
git clone --recurse-submodules <main-repo-url>
```

启用 `--recurse-submodules` 选项会自动递归地克隆并初始化所有的子模块（包括嵌套的子模块）。

如果没有使用该选项，那么克隆下来后，所有的子模块目录会是空的。此时可以通过以下命令来递归地初始化和更新所有子模块：

```bash
git submodule update --init --recursive

# 或者等价地：
git submodule init && git submodule update --recursive
```

## 拉取远端主仓库对子仓库的更新

`git pull` 会抓取子模块的变更，但不会自动更新子模块的内容。使用 `--recurse-submodules` 选项可以自动更新子模块：

```bash
git pull --recurse-submodules

# 或等价地：
git pull && git submodule update --recursive
```

但是有一种情况会导致上述操作失败：远端主仓库改变了子模块的 URL（`.gitmodules` 文件中记录的 URL 有变更）。此时需要多一步操作将新的 URL 复制到本地配置中：

```bash
git pull
git submodule sync --recursive
git submodule update --init --recursive
```

## 拉取子模块远端的更新

##### 方式一：在主仓库中进行

```bash
# 更新所有子模块到其追踪的远端分支的最新提交
git submodule update --remote
# 或指定特定的子模块
git submodule update --remote <submodule-name>
```

然后正常地在主仓库中提交对子模块的更新。

##### 方式二：进入子仓库中

```bash
cd <submodule-name>

git pull
# 也可以签出到特定的 commit / branch / tag
git checkout <ref>

# 返回主仓库
cd ..
```

然后正常地在主仓库中提交对子模块的更新。

## 在主仓库中切换分支

使用 `--recurse-submodules` 选项确保主仓库切换分支时，子模块也会处于正确的状态：

```bash
git checkout <branch-name> --recurse-submodules
```

如果没有启用 `--recurse-submodules` 选项，切换分支后子模块可能会处于未更新的状态。

## 添加新的子模块

```bash
git submodule add -b <branch-name> <submodule-repo-url> <path-to-submodule>
git submodule update --init --recursive
```

然后继续在主仓库中提交该更改。

## 删除子模块

```bash
git submodule deinit -f <submodule-name>
rm -rf .git/modules/<submodule-name>
git rm -f <submodule-name>
```

然后继续在主仓库中提交该更改。


