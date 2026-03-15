---
name: bazi-calc
description: Generate chart.json from input JSON with deterministic local code only.
---

Use when:
1. The task is to run `calc`
2. The input comes from `用户输入/*.json`

Rules:
1. Validate input structure first
2. Only write `输出结果/chart.json`
3. Output placeholder pillars for phase 1
4. Never add narrative fate interpretation
