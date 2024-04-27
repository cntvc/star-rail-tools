[中文][zh_cn] | English

# Honkai: Star Rail Tools

[![Test](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml/badge.svg)](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml)
[![commit](https://img.shields.io/github/last-commit/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/commits/main)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/cntvc/star-rail-tools)][latest_release]
[![license](https://img.shields.io/github/license/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/blob/main/LICENSE)


Honkai: Star Rail Tools, a small utility for exporting gacha records and exporting calendar.


| ![cover](image/star_rail_tools_cover.png) | ![cover_month_info](image/month.png) |
|:-----------------------------------------:|:-------------------------------------|


## Basic Usage

### Download Sources

- [GitHub][latest_release]: has two releases
  - zip suffix: folder compressed version, faster startup compared to the single-file version
  - exe suffix: single-file version
- [Artifact Repository][coding_latest] (faster download in China, includes only the single-file version)

### Add or update account cookies.

  **Note: Cookies are crucial account credentials. Do not disclose them to avoid potential account security issues.**

  Firstly, log in to [miHoYo](https://user.mihoyo.com/) (International server users log in to [HoYoLAB](https://account.hoyoverse.com/)). Press F12, select the console, paste the following code, copy the cookie from the dialog that appears.

  ```javascript
  javascript:(function(){prompt(document.domain,document.cookie)})();
  ```

  Then click the "Read Cookie" button, which will automatically read clipboard data and parse it.

  <details>
    <summary>Cookie Retrieval Example</summary>

  <p>
    <img src="../docs/image/web_cookie.png" alt="web cookie" height = 80% width = 80% align="middle">
  </p>

  </details>

### Data Migration
This software is a member of the [UIGF](https://uigf.org) organization, supports import and export of `SRGF` format data.

Importing SRGF format data:
Place the data files you want to import into the "Import" folder. You can add multiple files at once. Click the "Import Data" button to proceed.

<details>
  <summary>Click to view Data Directory Structure</summary>
  <p>

```cmd
  StarRailTools_1.0.0.exe # Main program file
  StarRailTools # Software data directory
  ├── 101793414 # Exported data for account 101793414
  │   ├── GachaLog_101793414.xlsx
  │   └── GachaLog_SRGF_101793414.json
  ├── AppData # Software runtime data
  │   ├── config
  │   │   └── settings.json
  │   ├── data
  │   │   └── star_rail.db
  │   ├── log
  │   │   └── log_2023_08.log
  │   └── temp
  │       └── GachaAnalyze_101793414.json
  └── Import # Directory for loding import data
```

 </p>
</details>


## Contributing
Your contributions to this project are highly appreciated.

- If you have new ideas or feature suggestions, please create an issue.
- If you find any bugs in the software or would like to update the documentation, feel free to create a pull request.

For more details, please refer to [CONTRIBUTING](../.github/CONTRIBUTING.md)


## Acknowledgments

- Reference project for early development : [**genshin-gacha-export**](https://github.com/sunfkny/genshin-gacha-export)
- Pagination module : [**genshin.py**](https://github.com/thesadru/genshin.py)

### JetBrains Development Tools
Thanks to JetBrains for providing development licenses for open-source projects.

![JetBrains](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg)

[latest_release]: https://github.com/cntvc/star-rail-tools/releases/latest
[coding_latest]: https://cntvc.coding.net/public-artifacts/star-rail-tools/releases/packages
[zh_cn]: ../README.md
