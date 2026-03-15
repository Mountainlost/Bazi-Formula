# Bazi-Formula

`Bazi-Formula` is a deterministic and auditable bazi repository for `Windows PowerShell` and `Python 3.10`.

This project is not a chat-style fortune-telling tool. It is a rule-driven engineering prototype that keeps calculation, rule evaluation, reporting, and auditing separated.

## Project Summary

Current implemented layers:
- Real four-pillar calculation for `calc`
- Basic ten-god mapping for visible stems and hidden stems
- Strength scoring `v0`
- Candidate yongshen output `v0`
- `final_useful_god_v0` controlled decision layer
- Luck-cycle skeleton with start direction, start age, start datetime, and 10 cycles
- Evidence-linked `report` and `audit`

Chinese terminology alignment:
- 已实现：真实四柱排盘、十神基础映射、旺衰评分 v0、候选用神 v0、最终用神受控版 v0、大运起运骨架、evidence 审计链
- 未实现：完整格局体系、调候、神煞、流年流月、全球任意时区、无闰月标识的闰月输入、多流派支持

## Current Scope

The current repository supports:
- `calendar_type=solar`
- `calendar_type=lunar` via controlled normalization to solar datetime before the existing calc chain
- `timezone` whitelist: `Asia/Shanghai`, `Asia/Singapore`, `Asia/Tokyo`
- `true_solar_time=false`
- `true_solar_time=true` only when `birth_place` is in `configs/input_normalization.yaml`
- Supported input year range `1900-2099`
- A single-school ziping-style deterministic workflow

Available commands:
- `calc`
- `judge`
- `report`
- `audit`

## Explicitly Not Implemented

The current repository does not implement:
- complete pattern system
- climate adjustment
- shensha
- yearly or monthly luck
- multi-school logic
- global arbitrary timezones
- leap-month lunar input without an explicit marker

## Repository Layout

```text
Bazi-Formula/
├─ README.md
├─ AGENTS.md
├─ 项目说明.md
├─ 开发流程.md
├─ 规则说明.md
├─ GitHub提交前检查.md
├─ pyproject.toml
├─ schemas/
├─ src/bazi/
├─ tests/
├─ 用户输入/
├─ 输出结果/
├─ 测试样本/
├─ 规则映射/
└─ .github/workflows/
```

Key directories:
- `src/bazi`: Python package, deterministic engines, and CLI entrypoints
- `schemas`: JSON Schema files for stage outputs
- `tests`: regression tests, pipeline checks, and audit boundary tests
- `用户输入`: sample input JSON
- `输出结果`: runtime outputs, tracked with `.gitkeep` only
- `测试样本`: golden files for regression control
- `规则映射`: table-driven rules, mappings, and evidence registry

## Quick Start on Windows PowerShell

```powershell
python --version
python -m pip install -e .[dev]
pytest
```

## Run Commands

```powershell
python -m bazi.cli calc --input 用户输入/user_001.json
python -m bazi.cli judge --chart 输出结果/chart.json
python -m bazi.cli report --chart 输出结果/chart.json --rules 输出结果/rules.json
python -m bazi.cli audit --chart 输出结果/chart.json --rules 输出结果/rules.json --report 输出结果/report.json
```

The console entrypoint is also installed:

```powershell
bazi calc --input 用户输入/user_001.json
```

## Test Commands

```powershell
pytest
python -m bazi.cli calc --input 用户输入/user_001.json
python -m bazi.cli judge --chart 输出结果/chart.json
python -m bazi.cli report --chart 输出结果/chart.json --rules 输出结果/rules.json
python -m bazi.cli audit --chart 输出结果/chart.json --rules 输出结果/rules.json --report 输出结果/report.json
```

## Rule Boundary

Stage contract:
- `calc` produces deterministic structured chart data
- `judge` produces deterministic rule-layer outputs
- `report` only restates existing `chart.json` and `rules.json` content
- `audit` checks evidence linkage, field boundaries, consistency, and out-of-scope wording

Useful god boundary:
- `candidate yongshen v0` is provisional only
- `final_useful_god_v0` is a controlled `v0` layer and is emitted only when current rule evidence is sufficiently aligned
- If evidence is insufficient or conflicting, the system returns a non-final status instead of forcing a conclusion

## Reliability Boundary

Please treat this repository as:
- a rule-driven and auditable prototype
- not a complete metaphysics system
- not a complete traditional yongshen determination system
- not a complete commercial product

Candidate output does not equal final useful god. `final_useful_god_v0` is intentionally conservative and may return `insufficient_for_final_determination` or `blocked_by_conflict`.
This repository should also be understood as a 规则驱动原型，不是完整商业产品。

## Contribution and Iteration

Changes should preserve:
- deterministic local computation
- evidence-linked outputs
- Windows and Python 3.10 compatibility
- strict separation between rule layer and explanation layer

## 微信联系

如需在 GitHub 页面展示微信二维码，请将图片文件放置到 `assets/wechat_qr.png`。
如果该文件当前尚未提供，这里保留为占位链接。

![微信二维码占位](assets/wechat_qr.png)
