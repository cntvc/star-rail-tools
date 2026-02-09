> 欢迎您参与项目的开发，下面是参与代码贡献的指南，以供参考！ヾ(ﾟ∀ﾟゞ)

# 代码贡献步骤

## 0. 提交 issue

**任何新功能或者功能改进建议都先提交 [issue][issues] 讨论后再进行开发，如果是文档更新或 Bug 修复等问题可直接提交 PR。**

## 1. Fork 此仓库并 clone 到本地

```shell
# 克隆仓库
git clone https://github.com/{YOUR_USERNAME}/star-rail-tools.git
```

## 2. 创建开发环境

本项目使用 Rust 语言开发，请确保您的开发环境已安装 Rust 工具链。

### 安装 Rust
如果您尚未安装 Rust，请访问 [rustup.rs](https://rustup.rs/) 下载并安装。

### 编辑器推荐
推荐使用 VS Code 配合 [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer) 插件进行开发。

### 构建项目
在项目根目录下运行以下命令来下载依赖并构建项目：

```shell
cargo build
```

## 3. 创建新的开发分支

创建新的分支用于开发新功能或修复bug. PS: 请始终保持 main 分支与本仓库一致

```shell
git checkout -b {BRANCH_NAME}
```

## 4. 编写代码和测试用例后运行代码测试

### 运行程序

本项目包含多个 crate，主程序入口位于 `tui` 包中。您可以使用以下命令运行主程序：

```shell
cargo run -p tui
```

### 代码格式化与检查

在提交代码前，请确保代码通过了格式化和静态检查。

```shell
# 格式化代码
cargo fmt

# 运行静态检查
cargo clippy
```

### 运行测试

```shell
cargo test
```

## 5. 提交 pull request

```shell
# 将代码推送到自己 fork 仓库的分支
git push origin {BRANCH_NAME}
```

回到自己的 GitHub 仓库页面，选择 New pull request 按钮，创建 Pull request 到原仓库的 main 分支。

然后等待 Review 即可，如有 Change Request，再本地修改之后再次提交即可。

# 代码风格

代码风格遵循 Rust 标准风格，请使用 `cargo fmt` 自动格式化您的代码。

[issues]: https://github.com/cntvc/star-rail-tools/issues
