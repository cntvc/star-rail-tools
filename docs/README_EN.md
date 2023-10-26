[中文][zh_cn] | English

# Honkai: Star Rail Tools

[![Test](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml/badge.svg)](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml)
[![commit](https://img.shields.io/github/last-commit/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/commits/main)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/cntvc/star-rail-tools)][latest_release]
[![license](https://img.shields.io/github/license/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/blob/main/LICENSE)


Honkai Star Rail Tools is a utility that allows you to export warp records.

<p>
  <img src="image/analyze_result_en_us.png" alt="analyze_result_en_us" height = 80% width = 80% align="middle">
</p>


## Basic Usage

Download source:
- [Github][latest_release]
- [Artifact Repository][coding_latest] (Recommended for users in China)

### 1. Export Warp Records
1. Set up your account: Input or select your Honkai Star Rail UID.
2. Open the Warp page and select the "View Details".
3. Switch to the Star Rail Tools application and choose "Export Gacha Data" -> "Export using game web cache" from the menu.
4. Once the export is complete, follow the instructions to view the warp report.
### 2. Import or Merge Warp Records Data
1. Set up your account: Input or select your Honkai Star Rail UID.
2. Place the data you want to import or merge into the merge folder. You can place multiple files at once. Supported formats include [SRGF][SRGF] and the software's own JSON format.
3. Switch to the Star Rail Tools application and choose "Import or Merge Data" from the menu.


<details>
  <summary>Click to view <b>directory structure</b></summary>
  <p>


```cmd
  StarRailTools_1.0.0.exe # Main program file
  StarRailTools # Software data directory
  +---101793414 # Gacha data for account 101793414
  |       GachaAnalyze_101793414.json # Gacha analysis result
  |       GachaLog_101793414.json # Raw gacha data
  |       GachaLog_101793414.xlsx # Exported XLSX file
  |       UserProfile_101793414.json # Account information
  |
  +---merge # Directory for reading imported or merged data files
  |
  +---config
  |       settings.json # Software settings (if no settings have been set yet)
  |
  \---log
          log_2023_05.log # Log file
```

 </p>
</details>


## Contributing
Your contributions to this project are highly appreciated.

- If you have new ideas or feature suggestions, please create an issue to discuss them.
- If you find any bugs in the software or would like to update the documentation, feel free to create a pull request.

For more details, please refer to [CONTRIBUTING](../.github/CONTRIBUTING.md)


## Acknowledgments

- Code reference for exporting Excel files [**genshin-gacha-export**](https://github.com/sunfkny/genshin-gacha-export)
- Code reference for adapting to the global server [**star-rail-warp-export**](https://github.com/biuuu/star-rail-warp-export)


[latest_release]: https://github.com/cntvc/star-rail-tools/releases/latest
[coding_latest]: https://cntvc.coding.net/public-artifacts/star-rail-tools/releases/packages

[SRGF]: https://uigf.org/en/standards/SRGF.html
[zh_cn]: https://github.com/cntvc/star-rail-tools
