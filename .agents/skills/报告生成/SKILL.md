---
name: bazi-report
description: Generate report.json from chart.json and rules.json without changing conclusions.
---

Use when:
1. `chart.json` and `rules.json` already exist
2. The task is to run `report`

Rules:
1. Read only `输出结果/chart.json` and `输出结果/rules.json`
2. Write only `输出结果/report.json`
3. Keep every conclusion aligned with `rules.json`
4. Every section must keep `evidence_refs`
