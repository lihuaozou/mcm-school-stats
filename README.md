# 2026 MCM/ICM School Award Statistics

一个用于查询和可视化 2026 年 COMAP MCM/ICM 获奖结果的静态网站。输入学校英文名、中文名或队伍编号，即可查看该校完整队伍名单、具体奖项、Advisor、来源 PDF 页码和官方证书入口。

在线访问：

```text
https://lihuaozou.github.io/mcm-school-stats/
```

## 功能

- 支持学校英文名、中文名、大小写不同写法和队伍编号搜索。
- 同一学校的大小写差异会自动归并，例如 `Liuzhou Institute of technology` 和 `Liuzhou Institute of Technology` 会合并展示。
- 对常见 PDF 截断长校名进行补全，例如：
  - `Nanjing University of Posts and` -> `Nanjing University of Posts and Telecommunications`
  - `Huazhong University of Science and` -> `Huazhong University of Science and Technology`
  - `University of Electronic Science and` -> `University of Electronic Science and Technology of China`
- 为已知学校提供中文名映射，可直接搜索 `南京邮电大学`、`柳州工学院`、`浙江大学` 等中文名称。
- 展示学校奖项分布、题目分布、题目与奖项热力图、高奖项数量、排名、覆盖题目数、获奖率等分析。
- 表格展示完整队伍记录：队伍编号、学校、中文名、国家/地区、竞赛、题目、奖项等级、具体奖项、特别奖/备注、Advisor、来源 PDF 和证书。
- 每条队伍记录提供 COMAP 官方证书链接：

```text
https://www.comap-math.org/mcm/2026Certs/队伍编号.pdf
```

## 文件结构

```text
.
├── index.html                       # 网站入口
├── app.js                           # 搜索、聚合、图表和表格逻辑
├── styles.css                       # 页面样式
├── parse_results.py                 # 从 6 份结果 PDF 解析并生成 data/awards.json
├── audit_results.py                 # 数据审计脚本
├── data/
│   ├── awards-cn.json               # 网站使用的结构化数据，含中文学校名
│   ├── awards.json                  # 同步保留的结构化数据
│   ├── audit_report.json            # 审计报告
│   ├── blank_institution_rows.csv   # PDF 中未提供可用学校名的队伍清单
│   └── parse_issues.json            # 解析异常清单
└── 2026_*_Results.pdf               # COMAP 2026 MCM/ICM A-F 题结果 PDF
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
http://127.0.0.1:8000/?school=南京邮电大学
http://127.0.0.1:8000/?school=Nanjing%20University%20of%20Posts%20and%20Telecommunications
http://127.0.0.1:8000/?school=2603082
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
- 6 份 PDF 的队伍号集合与 `data/awards.json` 完全一致，无遗漏、无多余。
- 已映射中文名的记录：24,772 条。
- 已映射中文名的学校：420 所。

已知说明：

- Problem A 首页摘要比详细名单少 1 个 Successful Participant；本项目以详细队伍名单中的队伍号为准。
- 有 469 条记录在 PDF 文本层和坐标层都没有可用学校名，因此保留为空，并列在 `data/blank_institution_rows.csv`。
- 官方证书 PDF 用作人工核验入口，不作为批量解析来源。

## GitHub Pages

本项目是纯静态网站，已通过 GitHub Pages 发布。更新 `main` 分支后会自动部署到：

```text
https://lihuaozou.github.io/mcm-school-stats/
```
