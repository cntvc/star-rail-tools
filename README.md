中文 | [English][en_us]

# 崩坏：星穹铁道小工具

[![Test](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml/badge.svg)](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml)
[![commit](https://img.shields.io/github/last-commit/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/commits/main)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/cntvc/star-rail-tools)][latest_release]
[![license](https://img.shields.io/github/license/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/blob/main/LICENSE)


崩坏：星穹铁道小工具，可统计跃迁记录


| ![cover](docs/image/star_rail_tools_cover.png) | ![cover_month_info](docs/image/month.png) |
|:----------------------------------------------:|:------------------------------------------|

## 基本使用

### 获取跃迁记录

1. 打开游戏的跃迁记录历史页面
2. 在软件使用 "刷新" -> 增量更新


### 数据导入
  软件支持导入 `SRGF/UIGFv4`[^1] 格式数据:
  将需要导入的数据文件放入 "UserData/Import" 文件夹内，可一次放入多个文件，点击 "导入" 按钮即可

<details>
  <summary>点击查看 数据目录结构</summary>
  <p>

```cmd
  StarRailTools
  ├── StarRailTools.exe
  ├── AppData
  │   ├── config
  │   │   └── settings.json
  │   ├── data
  │   │   └── star_rail.db
  │   ├── log
  │   │   └── log_2023_08.log
  │   └── temp
  │       └── GachaAnalyze_101793414.json
  └── UserData
      ├── 101793414
      └── Import
```

 </p>
</details>


## 参与贡献

非常欢迎您参与项目贡献
- 如果您有新的想法或功能建议，请创建 Issue 进行讨论
- 如果您发现了软件 Bug 或者希望对文档进行更新，可直接创建 PR

更多详情请参阅 [CONTRIBUTING](.github/CONTRIBUTING.md)


## 鸣谢

- 早期开发的参考项目 : [**genshin-gacha-export**](https://github.com/sunfkny/genshin-gacha-export)
- 分页查询模块 : [**genshin.py**](https://github.com/thesadru/genshin.py)

### JetBrains 开发工具
特别感谢 [**JetBrains**](https://jb.gg/OpenSourceSupport) 为开源项目提供的开发许可证

![JetBrains](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg)


[latest_release]: https://github.com/cntvc/star-rail-tools/releases/latest
[coding_latest]: https://cntvc.coding.net/public-artifacts/star-rail-tools/releases/packages
[en_us]: docs/README_EN.md

[^1]: `SRGF/UIGFv4` 格式为 UIGF 组织制定的数据交换格式，详情请访问 [UIGF](https://uigf.org) 官网
