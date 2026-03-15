# GitHub提交前检查

## 本地先执行
```powershell
python -m pip install -e .[dev]
pytest
python -m bazi.cli calc --input 用户输入/user_001.json
python -m bazi.cli judge --chart 输出结果/chart.json
python -m bazi.cli report --chart 输出结果/chart.json --rules 输出结果/rules.json
python -m bazi.cli audit --chart 输出结果/chart.json --rules 输出结果/rules.json --report 输出结果/report.json
```

## 默认不应提交的内容
- `__pycache__/`
- `.pytest_cache/`
- `.venv/`
- `build/`
- `dist/`
- `*.egg-info/`
- `输出结果/*.json`

保留：
- `输出结果/.gitkeep`

## 必须保留的 golden 样本
- `测试样本/user_001_chart_golden.json`
- `测试样本/user_001_rules_golden.json`

## 提交前确认
1. `pytest` 已通过
2. `calc -> judge -> report -> audit` 已顺序跑通
3. `输出结果/` 下没有误提交运行产物
4. GitHub Actions `CI` 已通过，或当前改动预期能通过

## 当前版本边界提醒
- 当前仓库是规则驱动原型，不是完整商业产品
- `final_useful_god_v0` 是受控版 v0，不是完整传统命理最终判定系统
- 当前未实现完整格局体系、调候、神煞、流年流月、宽输入范围、多流派支持
