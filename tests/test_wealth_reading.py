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


def test_wealth_reading_v0_is_written(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    wealth = rules.wealth_reading_v0
    assert wealth.method == "wealth_reading_v0"
    assert wealth.status == "determined"
    assert wealth.base_support in {"positive", "favorable"}
    assert wealth.current_phase == "cautious"
    assert wealth.wealth_mode in {"steady_accumulation", "leverage_growth", "risk_control"}
    assert wealth.future_tendency in {"positive", "favorable"}
    assert wealth.resource_support in {"mixed", "positive", "favorable"}
    assert wealth.risk_control in {
        "tight_control",
        "balanced_control",
        "measured_expansion",
    }
    assert wealth.conclusion
    assert wealth.notes
    assert wealth.evidence_refs


def test_wealth_reading_v0_uses_controlled_non_event_conclusion(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    conclusion = rules.wealth_reading_v0.conclusion
    assert "财" in conclusion
    assert "当前阶段" in conclusion
    assert "未来几年" in conclusion
    assert report.wealth_reading_summary == rules.wealth_reading_v0
    assert conclusion in report.final_report_v0.wealth.text

    for forbidden in (
        "一定发财",
        "一定赚大钱",
        "必然暴富",
        "投资必赚",
        "必然投资成功",
        "某年一定发财",
    ):
        assert forbidden not in conclusion
        assert forbidden not in report.final_report_v0.wealth.text


def test_wealth_reading_v0_does_not_change_final_useful_god(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    assert rules.final_useful_god_v0.status == "determined"
    assert rules.final_useful_god_v0.primary_element == "metal"
    assert rules.final_useful_god_v0.secondary_elements == ["earth"]
