# 崩坏：星穹铁道跃迁记录导出工具

<p>
  <img src="docs/image/analyze_result.png" alt="analyze_result" height = 70% width = 70% align="middle">
</p>


## 简介

软件为崩坏：星穹铁道跃迁记录导出工具，以单文件应用方式发布，目前仅支持 Windows 系统。

软件导出抽卡数据的方式有以下几种
- 使用游戏缓存导出 （**推荐** 通过读取游戏日志文件获取链接
- 剪切板读取链接导出
- 从软件缓存的链接导出 （在使用游戏缓存导出后，软件会将抽卡链接保存在 UserProfile_{UID}.json 文件中，本方式即读取该文件以获取抽卡链接


软件产生的所有数据均存储在 exe 文件所在目录的 StarRailTools 文件夹下，以下是软件数据存储结构示例
```cmd
  StarRailTools_0.1.1.exe # 主程序文件
  StarRailTools # 软件数据目录
  +---101793414 # 账号 101793414 的抽卡数据
  |       Analyze_101793414.json # 抽卡分析结果
  |       GachaLog_101793414.json # 抽卡原始数据
  |       GachaLog_101793414.xlsx # 导出的XLSX文件
  |       UserProfile_101793414.json # 账号信息
  |
  +---config
  |       settings.toml # 软件设置（如果没有进行过设置则不存在
  |
  \---log
          log_2023-05.log # 日志文件
```


## 使用方式

在 Github [下载页面](https://github.com/cntvc/star-rail-wish-tools/releases/latest) 下载exe文件，双击即可使用

1. 设置账户：选择或输入需要导出的账号 UID
2. 打开游戏，在**抽卡记录页面**选择历史记录并翻页
3. 切换到软件，依次选择菜单 **导出抽卡数据** -> **使用游戏缓存导出**
4. 完成导出后，根据提示查看抽卡报告

<details>
  <summary>点击查看 <b>抽卡记录页面</b></summary>
  <p>
  <img src="docs/image/gacha_log.png" height = 70% width = 70% >
 </p>
</details>

## 参与贡献

非常欢迎您参与项目贡献
- 如果您有新的想法或功能建议，请创建 Issue 进行讨论
- 如果您发现了软件 Bug 或者希望对文档进行更新，可直接创建 PR

更多详情请参阅 [CONTRIBUTING](.github/CONTRIBUTING.md)

## 鸣谢

- 项目修改自 [**Genshin_Impact_Tools**](https://github.com/cntvc/Genshin-Impact-Tools)
- 导出XLSX代码参考 [**genshin-gacha-export**](https://github.com/sunfkny/genshin-gacha-export)
- 适配国际服的代码参考 [**star-rail-warp-export**](https://github.com/biuuu/star-rail-warp-export)
