import json
from pathlib import Path

from bazi.cli import run_calc
from bazi.judge_engine import build_rules_output
from bazi.models import ChartOutput
from bazi.reporter import build_report

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"


def _load_chart(tmp_path: Path) -> ChartOutput:
    chart_path = tmp_path / "chart.json"
    run_calc(USER_INPUT_DIR / "user_001.json", chart_path)
    return ChartOutput.model_validate(json.loads(chart_path.read_text(encoding="utf-8")))


def test_pattern_system_v1_is_written_for_user_001(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    pattern = rules.pattern_system_v1
    assert pattern.method == "month_main_qi_pattern_v1"
    assert pattern.status == "candidate_only"
    assert pattern.candidate_pattern is not None
    assert pattern.final_pattern is None
    assert pattern.candidate_pattern.pattern_key == "yueshangguan"
    assert pattern.candidate_pattern.pattern_name == "月伤官格"
    assert pattern.candidate_pattern.source_stem == "壬"
    assert pattern.candidate_pattern.source_god == "伤官"
    assert pattern.candidate_pattern.transparency == "hidden_only"
    assert pattern.evidence_refs
    assert rules.final_useful_god_v0.primary_element == "metal"


def test_pattern_system_becomes_determined_when_month_main_qi_is_visible(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    mutated = chart.model_dump()
    mutated["pillars"]["month"]["stem"] = "壬"
    mutated["pillars"]["month"]["ganzhi"] = "壬亥"
    determined_chart = ChartOutput.model_validate(mutated)

    rules = build_rules_output(determined_chart)
    pattern = rules.pattern_system_v1
    assert pattern.status == "determined"
    assert pattern.candidate_pattern is not None
    assert pattern.final_pattern is not None
    assert pattern.candidate_pattern.pattern_key == "yueshangguan"
    assert pattern.candidate_pattern.transparency == "visible"
    assert pattern.final_pattern.pattern_key == "yueshangguan"


def test_report_pattern_summary_only_restates_rules(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    assert report.pattern_system_summary == rules.pattern_system_v1
    assert report.pattern_system_summary.status == rules.pattern_system_v1.status
