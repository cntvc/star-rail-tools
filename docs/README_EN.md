[中文][zh_cn] | English

# Honkai: Star Rail Tools

[![Test](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml/badge.svg)](https://github.com/cntvc/star-rail-tools/actions/workflows/test.yml)
[![commit](https://img.shields.io/github/last-commit/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/commits/main)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/cntvc/star-rail-tools)][latest_release]
[![license](https://img.shields.io/github/license/cntvc/star-rail-tools)](https://github.com/cntvc/star-rail-tools/blob/main/LICENSE)


Honkai: Star Rail Tools can export your gacha records and trailblazer calendar.


| ![cover](image/star_rail_tools_cover.png) | ![cover_month_info](image/month.png) |
|:-----------------------------------------:|:-------------------------------------|


## Basic Usage

### Adding or Updating Account Cookie

  > [!WARNING]
  > **Cookie is a very important account credential; please do not leak it to avoid potential account security issues.**

  First, log in to the [miHoYo](https://user.mihoyo.com/) (for international users, log in to [HoYoLAB](https://account.hoyoverse.com/)). Press F12, select the console, paste the following code, and copy the Cookie from the dialog

  ```javascript
  javascript:(function(){prompt(document.domain,document.cookie)})();
  ```

  Then click the "Read Cookie" button, which will automatically read the clipboard data and parse it.

  <details>
    <summary>Cookie Retrieval Example</summary>

  <p>
    <img src="../docs/image/web_cookie.png" alt="web cookie" height = 80% width = 80% align="middle">
  </p>

  </details>

### Data Migration
Importing SRGF/UIGFv4`[^1] format data:
To import your data files, move them into the "Import" folder. You have the option to add several files simultaneously. After doing so, proceed by clicking the "Import Data" button.

<details>
  <summary>Click to view Data Directory Structure</summary>
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


## Contributing
Welcome your contributions to the project.
- For new ideas or feature suggestions, please open an Issue.
- If you discover a bug or wish to update the documentation, feel free to create a PR directly.

For more details, please refer to [CONTRIBUTING](../.github/CONTRIBUTING.md)


## Acknowledgments

- Early development reference project : [**genshin-gacha-export**](https://github.com/sunfkny/genshin-gacha-export)
- Pagination query module : [**genshin.py**](https://github.com/thesadru/genshin.py)

### JetBrains Development Tools
Special thanks to JetBrains for providing development licenses for open-source projects.

![JetBrains](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg)

[latest_release]: https://github.com/cntvc/star-rail-tools/releases/latest
[coding_latest]: https://cntvc.coding.net/public-artifacts/star-rail-tools/releases/packages
[zh_cn]: ../README.md

[^1]: `SRGF/UIGFv4` format is a data exchange format established by the UIGF organization. For more information, please visit the [UIGF](https://uigf.org) official website
