# Bazi-Formula project instructions

## Project identity
- This repository is a deterministic bazi project skeleton for Windows and Python 3.10.
- It is not a chat fortune-telling project.
- Keep outputs structured, auditable, and reproducible.
- Do not add shensha, advanced patterns, free-form destiny claims, or non-auditable logic.

## Scope boundary
- Only the bazi flow is allowed in this repository.
- Never mix ziwei, liuyao, tarot, western astrology, qimen, or any other school.
- Do not let the explanation layer override the rule layer.

## Execution order
1. calc
2. judge
3. report
4. audit

## Layer contract
- `calc` reads `用户输入/*.json` and writes `输出结果/chart.json`.
- `judge` reads `chart.json` and writes `rules.json`.
- `report` may use only `chart.json` and `rules.json` to write `report.json`.
- `report` must not rewrite, embellish, or reverse deterministic conclusions from `rules.json`.
- `audit` checks file existence, evidence linkage, and field boundaries before writing `audit.json`.

## Evidence contract
- Every conclusion must include `evidence_refs`.
- If evidence is insufficient, output `不足以判断` or a conservative empty result.
- `report.json` can only describe conclusions already present in `chart.json` and `rules.json`.
- All outputs must carry version fields appropriate to their stage.

## Supported scope in the current repository
- `calendar_type=solar`
- `timezone=Asia/Shanghai`
- `true_solar_time=false`
- real four-pillar calculation
- basic ten-god mapping
- strength scoring v0
- candidate-only yongshen v0
- luck-cycle skeleton

## Delivery rule
- Keep package names, module names, schema field names, and technical filenames in English.
- Prefer Chinese for business directories and business documents when compatibility is not harmed.
- Use UTF-8 for code, config, docs, and JSON files.
- Run relevant tests before finishing.
