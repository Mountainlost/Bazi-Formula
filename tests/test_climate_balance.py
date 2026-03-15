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


def _build_candidate_only_climate_chart(chart: ChartOutput) -> ChartOutput:
    mutated = chart.model_dump()
    mutated["pillars"]["year"] = {"stem": "甲", "branch": "子", "ganzhi": "甲子"}
    mutated["pillars"]["month"] = {"stem": "乙", "branch": "卯", "ganzhi": "乙卯"}
    mutated["pillars"]["day"] = {"stem": "辛", "branch": "酉", "ganzhi": "辛酉"}
    mutated["pillars"]["hour"] = {"stem": "丙", "branch": "子", "ganzhi": "丙子"}
    mutated["day_master"] = "辛"
    return ChartOutput.model_validate(mutated)


def test_climate_balance_v0_is_written_for_user_001(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    climate = rules.climate_balance_v0
    assert climate.method == "climate_balance_v0"
    assert climate.status == "candidate_only"
    assert climate.season_context is not None
    assert climate.season_context.month_branch == "亥"
    assert climate.season_context.season == "winter"
    assert climate.season_context.detected_tendencies == ["damp"]
    assert len(climate.candidate_adjustments) == 2
    assert climate.candidate_adjustments[0].element == "fire"
    assert climate.candidate_adjustments[0].direction == "warming"
    assert climate.candidate_adjustments[1].element == "earth"
    assert climate.candidate_adjustments[1].direction == "drying"
    assert climate.evidence_refs
    assert rules.final_useful_god_v0.primary_element == "metal"


def test_climate_balance_candidate_only_when_distribution_signal_is_weak(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    candidate_only_chart = _build_candidate_only_climate_chart(chart)

    rules = build_rules_output(candidate_only_chart)
    climate = rules.climate_balance_v0
    assert climate.status == "candidate_only"
    assert climate.season_context is not None
    assert climate.season_context.season == "spring"
    assert climate.candidate_adjustments
    assert climate.candidate_adjustments[0].direction == "drying"
    assert climate.candidate_adjustments[1].direction == "warming"
    assert rules.final_useful_god_v0.decision_basis.method == "controlled_useful_god_v0"


def test_report_climate_summary_only_restates_rules(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    assert report.climate_balance_summary == rules.climate_balance_v0
    assert report.climate_balance_summary.status == rules.climate_balance_v0.status
