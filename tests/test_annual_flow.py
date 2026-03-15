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


def test_annual_flow_v0_is_written_for_user_001(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    annual_flow = rules.annual_flow_v0
    assert annual_flow.method == "annual_flow_v0"
    assert annual_flow.status == "determined"
    assert annual_flow.window.start_year == 1998
    assert annual_flow.window.end_year == 2007
    assert annual_flow.window.preview_year_count == 10
    assert [item.year for item in annual_flow.entries] == list(range(1998, 2008))
    assert [item.relative_index for item in annual_flow.entries] == list(range(10))
    assert [item.ganzhi for item in annual_flow.entries[:5]] == ["戊寅", "己卯", "庚辰", "辛巳", "壬午"]
    assert annual_flow.evidence_refs
    assert all(item.evidence_refs for item in annual_flow.entries)


def test_annual_flow_notes_stay_within_skeleton_scope(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    note_text = " ".join(item.text for item in rules.annual_flow_v0.notes)
    for forbidden in ("大吉", "大凶", "应期", "断语"):
        assert forbidden not in note_text


def test_report_annual_flow_summary_only_restates_rules(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    assert report.annual_flow_summary == rules.annual_flow_v0
    assert report.annual_flow_summary.entries[0].ganzhi == "戊寅"
