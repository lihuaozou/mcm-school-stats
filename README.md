# 2026 MCM/ICM School Award Statistics

一个用于查询和可视化 2026 年 MCM/ICM 获奖结果的本地静态网站。输入学校英文名后，可以查看该校所有队伍的题目、奖项等级、具体奖项、Advisor、来源 PDF 页码，并一键打开 COMAP 官方证书。

## 功能

- 按学校英文名搜索，大小写不同会自动归并到同一学校。
- 对常见被结果 PDF 截断的长学校名进行补全，例如：
  - `Nanjing University of Posts and` -> `Nanjing University of Posts and Telecommunications`
  - `Huazhong University of Science and` -> `Huazhong University of Science and Technology`
  - `University of Electronic Science and` -> `University of Electronic Science and Technology of China`
- 展示学校奖项分布图，包括 O/F/M/H/S/U/D/N 各等级数量。
- 展示学校在 A-F 各题目的队伍分布。
- 表格展示完整队伍记录：队伍编号、学校、国家/地区、竞赛、题目、奖项等级、具体奖项、特别奖/备注、Advisor、来源 PDF、证书入口。
- 每条队伍记录提供官方证书链接：
  `https://www.comap-math.org/mcm/2026Certs/队伍编号.pdf`
- 保留 PDF 原始学校写法，补全后的学校名可追溯。

## 文件结构

```text
.
├── index.html                         # 网站入口
├── app.js                             # 搜索、聚合、图表和表格逻辑
├── styles.css                         # 页面样式
├── parse_results.py                   # 从 6 份结果 PDF 解析并生成 data/awards.json
├── audit_results.py                   # 数据审计脚本
├── data/
│   ├── awards.json                    # 网站使用的结构化数据
│   ├── audit_report.json              # 审计报告
│   ├── blank_institution_rows.csv     # PDF 中未提供可用学校名的队伍清单
│   └── parse_issues.json              # 解析异常清单
└── 2026_*_Results.pdf                 # COMAP 2026 MCM/ICM A-F 题结果 PDF
```

## 本地运行

需要 Python 3。

```bash
python -m http.server 8000 --bind 127.0.0.1
```

然后打开：

```text
http://127.0.0.1:8000/
```

也可以用 URL 参数直接打开某个学校：

```text
http://127.0.0.1:8000/?school=Nanjing%20University%20of%20Posts%20and%20Telecommunications
```

## 重新生成数据

安装依赖：

```bash
python -m pip install pypdf
```

生成结构化数据：

```bash
python parse_results.py
```

运行审计：

```bash
python audit_results.py
```

## 数据核查结果

当前数据来自 6 份 PDF：

- `2026_MCM_Problem_A_Results.pdf`
- `2026_MCM_Problem_B_Results.pdf`
- `2026_MCM_Problem_C_Results.pdf`
- `2026_ICM_Problem_D_Results.pdf`
- `2026_ICM_Problem_E_Results.pdf`
- `2026_ICM_Problem_F_Results.pdf`

审计结果摘要：

- 总记录数：32,214
- 唯一队伍号：32,214
- 重复队伍号：0
- 非法队伍号：0
- 题目错配：0
- 国家/地区空值：0
- 6 份 PDF 的队伍号集合与 `data/awards.json` 完全一致。

已知说明：

- Problem A 首页摘要比详细名单少 1 个 Successful Participant；本项目以详细名单中的队伍号为准。
- 有少量队伍在 PDF 文本层和坐标层都没有可用学校名，这些记录保留为空并列在 `data/blank_institution_rows.csv`。
- 官方证书 PDF 的动态字段无法稳定用普通 PDF 文本抽取读取，因此证书用于人工核验入口，不作为批量解析来源。

## GitHub Pages

这是纯静态网站，可以直接通过 GitHub Pages 发布。仓库设置中选择：

- Source: Deploy from a branch
- Branch: `main`
- Folder: `/ (root)`

发布后即可在线访问网站。

默认公开访问地址为：

```text
https://lihuaozou.github.io/mcm-school-stats/
```
