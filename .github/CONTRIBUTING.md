> 欢迎您参与项目的开发，下面是参与代码贡献的指南，以供参考！ヾ(ﾟ∀ﾟゞ)

# 代码贡献步骤

## 0. 提交 issue
**任何**新功能或者功能改进建议和 BUG 修复都先提交 [issue][issues] 讨论一下，再进行开发。如果是文档拼写错误等琐碎问题不需要创建 issue

## 1. Fork 此仓库并 clone 到本地

```shell
# 克隆仓库
git clone https://github.com/{YOUR_USERNAME}/star-rail-tools.git
```

## 2. 创建开发环境

如果您不熟悉 poetry 虚拟环境的使用，请参照 [poetry wiki][poetry]

### 安装开发环境依赖包
```bash
pip install poetry

cd star-rail-tools

# 安装开发环境依赖包，这将为当前项目自动创建一个虚拟环境
poetry install
```

### 进入虚拟环境
```bash
poetry shell
```

### 初始化 git hook（非常重要）

```bash
pre-commit install
```

## 3. 创建新的开发分支

创建新的分支用于开发新功能或修复bug

```shell
git checkout -b {BRANCH_NAME}
```

## 4. 编写代码和测试用例后进行代码测试

代码格式请遵循 [PEP8][pep-8]，提交前会强制进行代码格式化，若未通过检测，请根据提示进行修改后再次尝试commit

如果进行新功能的开发或者有破坏性更新，请编写必要的单元测试来验证代码逻辑的正确性

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
[poetry]: https://python-poetry.org/docs/
[google-style-guide]: https://google.github.io/styleguide/pyguide.html
[google-style-guide-cn]: https://google-styleguide.readthedocs.io/zh_CN/latest/google-python-styleguide/contents.html
[pep-8]: https://peps.python.org/pep-0008/