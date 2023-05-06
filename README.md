# 崩坏·星穹铁道跃迁记录导出工具

<div>
<img src="docs/image/run_demo.gif" alt="run_demo" height = 70% width = 70% align="middle">
</div>


## 使用方式

在 Github [下载页面](https://github.com/cntvc/star-rail-wish-tools/releases/latest) 下载exe文件，双击即可使用

1. 设置账户：选择或输入需要导出的账号 UID
2. 打开游戏，在**抽卡记录页面**选择历史记录并翻页
3. 切换到软件，依次选择菜单 **导出抽卡数据** -> **使用游戏缓存导出**
4. 完成导出后，会在软件所在目录创建文件夹 StarRailTools，相关数据均存放在该文件夹中。
   <details>
    <summary>文件夹结构示例</b></summary>

    ```cmd
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
  </details>

<details>
  <summary>点击查看 <b>抽卡记录页面</b></summary>
  <p>
  <img src="docs/image/gacha_log.png" height = 70% width = 70% >
 </p>
</details>


**抽卡结果分析展示**
<p>
  <img src="docs/image/analyze_result.png" alt="analyze_result" height = 70% width = 70% align="middle">
</p>


## 参与贡献

非常欢迎您参与项目贡献，详情请参阅 [CONTRIBUTING.md](.github/CONTRIBUTING.md)
## 鸣谢

- 项目修改自 [**Genshin_Impact_Tools**](https://github.com/cntvc/Genshin-Impact-Tools)
- 导出XLSX代码参考 [**genshin-gacha-export**](https://github.com/sunfkny/genshin-gacha-export)
- 适配国际服的代码参考 [**star-rail-warp-export**](https://github.com/biuuu/star-rail-warp-export)
