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


def test_annual_reading_v0_is_written_for_user_001(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    annual_reading = rules.annual_reading_v0
    assert annual_reading.method == "annual_reading_v0"
    assert annual_reading.status == "determined"
    assert annual_reading.window.reference_year == 2026
    assert annual_reading.window.start_year == 2026
    assert annual_reading.window.end_year == 2030
    assert [item.year for item in annual_reading.entries] == [2026, 2027, 2028, 2029, 2030]
    assert [item.ganzhi for item in annual_reading.entries] == ["丙午", "丁未", "戊申", "己酉", "庚戌"]
    assert annual_reading.entries[0].mentor_signal == "favorable"
    assert annual_reading.entries[1].career_signal == "mixed"
    assert annual_reading.entries[2].career_signal == "favorable"
    assert annual_reading.entries[0].relationship_signal == "challenging"
    assert all(item.evidence_refs for item in annual_reading.entries)
    assert annual_reading.evidence_refs


def test_annual_reading_v0_uses_more_explicit_signals_without_neutral_fallback(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    entries = rules.annual_reading_v0.entries
    all_signals = {
        signal
        for item in entries
        for signal in (
            item.career_signal,
            item.wealth_signal,
            item.relationship_signal,
            item.mentor_signal,
        )
    }

    assert "neutral" not in all_signals
    assert {"favorable", "positive", "mixed", "cautious", "challenging"}.intersection(all_signals)
    assert any("整体较有利" in item.summary for item in entries)
    assert any("事业可稳中求进" in item.summary for item in entries)
    assert any("贵人助力偏强" in item.summary for item in entries)


def test_annual_reading_v0_stays_structured_and_non_absolute(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    texts = " ".join(item.summary for item in rules.annual_reading_v0.entries)
    for forbidden in (
        "一定升职",
        "一定发财",
        "一定结婚",
        "一定遇到贵人",
        "一定被提携",
        "保证升职",
        "保证发财",
        "保证结婚",
        "保证遇到贵人",
        "贵人必到",
        "必有贵人帮你",
        "某年必有贵人帮你",
        "必然被提携",
        "必然发生",
        "注定",
    ):
        assert forbidden not in texts


def test_report_future_five_years_only_restates_annual_reading(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    assert report.annual_reading_summary == rules.annual_reading_v0
    future_block = report.final_report_v0.future_five_years
    assert "未来五年阅读当前只基于既有规则做受控整合。" in future_block.overview.text
    assert "事业更值得主动推进的年份偏向2028年、2029年、2030年。" in future_block.overview.text
    assert "财务机会偏多的年份偏向2028年、2029年、2030年。" in future_block.overview.text
    assert "外部助力与贵人助力偏强的年份偏向2026年。" in future_block.overview.text
    assert [item.year for item in future_block.entries] == [2026, 2027, 2028, 2029, 2030]
    assert future_block.entries[0].text.startswith("2026年（丙午）：")
    assert "中性阅读" not in future_block.entries[0].text
