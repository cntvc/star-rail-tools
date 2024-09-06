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

如果您不熟悉 PDM 工具的使用，请参阅 [PDM Introduction](https://pdm-project.org/en/stable/)

### 安装开发环境依赖包
```bash
pip install pdm

cd star-rail-tools

# 安装开发环境依赖包，这将为当前项目自动创建一个虚拟环境
pdm sync
```

### 初始化 git hook（非常重要）

```bash
pre-commit install
```

## 3. 创建新的开发分支

创建新的分支用于开发新功能或修复bug. PS: 请始终保持 main 分支与本仓库一致

```shell
git checkout -b {BRANCH_NAME}
```

## 4. 编写代码和测试用例后运行代码测试

默认情况下，PDM 会搜索当前目录的虚拟环境，并使用它来运行代码，如果没有则会自行创建虚拟环境。

在运行代码前，您需要先进入虚拟环境
```powershell
# 进入虚拟环境
.venv\\Scripts\\activate

# 退出虚拟环境
deactivate
```

> [!IMPORTANT]
> 如果进行 UI 部分的开发，请参阅 [textualize wiki](https://textual.textualize.io/getting_started/) 以了解该 TUI 框架的基本使用方式
> ```shell
> # 在终端开启textual控制台
> textual console
> ```
>
> ```shell
> # 在另外的终端运行TUI程序并连接控制台以进行界面调试
> textual run main.py --dev
> ```

在编写完代码后，运行测试并执行代码格式化操作。代码格式请遵循 [PEP8][pep-8]，提交前会强制进行代码格式化，若未通过检测，请根据提示进行修改后再次尝试 commit

```shell
# 代码格式化
pdm run lint

# test
pdm run test

# 覆盖率测试
pdm run cov

# 本地构建
pdm run release
```

## 5. 提交 pull request

```shell
# 将代码推送到自己 fork 仓库的分支
git push origin {BRANCH_NAME}
```

回到自己的 GitHub 仓库页面，选择 New pull request 按钮，创建 Pull request 到原仓库的 main 分支。

然后等待 Review 即可，如有 Change Request，再本地修改之后再次提交即可。


# 代码风格

代码风格遵循 [Google python style guide][google-style-guide]（[中文版][google-style-guide-cn]）


[issues]: https://github.com/cntvc/star-rail-tools/issues
[google-style-guide]: https://google.github.io/styleguide/pyguide.html
[google-style-guide-cn]: https://google-styleguide.readthedocs.io/zh_CN/latest/google-python-styleguide/contents.html
[pep-8]: https://peps.python.org/pep-0008/
