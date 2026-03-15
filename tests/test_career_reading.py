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


def test_career_reading_v0_is_written(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    career = rules.career_reading_v0
    assert career.method == "career_reading_v0"
    assert career.status == "determined"
    assert career.base_support in {"positive", "favorable"}
    assert career.current_phase == "cautious"
    assert career.growth_mode in {"steady_build", "leverage_support", "active_breakthrough"}
    assert career.future_tendency in {"positive", "favorable"}
    assert career.resource_support in {"mixed", "positive", "favorable"}
    assert career.conclusion
    assert career.notes
    assert career.evidence_refs


def test_career_reading_v0_uses_controlled_non_event_conclusion(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    conclusion = rules.career_reading_v0.conclusion
    assert "事业" in conclusion
    assert "当前阶段" in conclusion
    assert "未来几年" in conclusion
    assert report.career_reading_summary == rules.career_reading_v0
    assert conclusion in report.final_report_v0.career.text

    for forbidden in (
        "一定升职",
        "保证升职",
        "必然晋升",
        "一定创业成功",
        "创业必成",
        "必然换工作",
        "一定跳槽成功",
    ):
        assert forbidden not in conclusion
        assert forbidden not in report.final_report_v0.career.text


def test_career_reading_v0_does_not_change_final_useful_god(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    assert rules.final_useful_god_v0.status == "determined"
    assert rules.final_useful_god_v0.primary_element == "metal"
    assert rules.final_useful_god_v0.secondary_elements == ["earth"]
