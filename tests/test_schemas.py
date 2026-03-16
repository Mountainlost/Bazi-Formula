import json
from pathlib import Path

from bazi.models import BaziInput, ChartOutput, ReportOutput, RulesOutput
from bazi.reporter import build_report

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"
GOLDEN_DIR = ROOT / "测试样本"

SCHEMA_EXPECTATIONS = {
    "input.schema.json": {"birth_date", "birth_time", "birth_place", "gender", "calendar_type"},
    "chart.schema.json": {
        "engine_version",
        "school",
        "calc_basis",
        "input_snapshot",
        "pillars",
        "day_master",
        "luck_cycle",
    },
    "rules.schema.json": {
        "rules_version",
        "engine_version",
        "based_on_chart_version",
        "status",
        "day_master",
        "ten_gods",
        "strength",
        "pattern_system_v1",
        "climate_balance_v0",
        "annual_flow_v0",
        "annual_reading_v0",
        "career_reading_v0",
        "wealth_reading_v0",
        "relationship_reading_v0",
        "shen_sha_v0",
        "provisional_conclusions",
        "final_useful_god_v0",
    },
    "report.schema.json": {
        "report_version",
        "engine_version",
        "rules_version",
        "status",
        "summary",
        "ten_gods_summary",
        "strength_summary",
        "pattern_system_summary",
        "climate_balance_summary",
        "annual_flow_summary",
        "annual_reading_summary",
        "career_reading_summary",
        "wealth_reading_summary",
        "relationship_reading_summary",
        "shen_sha_summary",
        "candidate_elements_summary",
        "final_useful_god_summary",
        "final_report_v0",
        "luck_cycle_summary",
        "caveats",
    },
    "audit.schema.json": {"audit_version", "engine_version", "rules_version", "report_version", "checks"},
}


def test_schema_files_have_required_fields() -> None:
    for file_name, required_fields in SCHEMA_EXPECTATIONS.items():
        schema = json.loads((ROOT / "schemas" / file_name).read_text(encoding="utf-8"))
        assert schema["type"] == "object"
        assert required_fields.issubset(set(schema["required"]))


def test_input_model_reads_sample_json() -> None:
    sample = json.loads((USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"))
    payload = BaziInput.model_validate(sample)
    assert payload.school == "bazi_ziping_v1"
    assert payload.timezone == "Asia/Shanghai"


def test_chart_model_reads_golden_sample() -> None:
    sample = json.loads((GOLDEN_DIR / "user_001_chart_golden.json").read_text(encoding="utf-8"))
    chart = ChartOutput.model_validate(sample)
    assert chart.status == "ok"
    assert chart.day_master == "辛"
    assert chart.pillars.month.ganzhi == "丁亥"
    assert chart.luck_cycle.direction == "backward"
    assert chart.luck_cycle.cycles[0].ganzhi == "丙戌"


def test_report_model_round_trip() -> None:
    chart_raw = json.loads((GOLDEN_DIR / "user_001_chart_golden.json").read_text(encoding="utf-8"))
    rules_raw = json.loads((GOLDEN_DIR / "user_001_rules_golden.json").read_text(encoding="utf-8"))
    chart = ChartOutput.model_validate(chart_raw)
    rules = RulesOutput.model_validate(rules_raw)

    report = build_report(chart, rules)
    loaded = ReportOutput.model_validate(report.model_dump())

    assert loaded.career_reading_summary == rules.career_reading_v0
    assert loaded.wealth_reading_summary == rules.wealth_reading_v0
    assert loaded.relationship_reading_summary == rules.relationship_reading_v0
    assert loaded.career_reading_summary.method == "career_reading_v0"
    assert loaded.wealth_reading_summary.method == "wealth_reading_v0"
    assert loaded.relationship_reading_summary.method == "relationship_reading_v0"
    assert loaded.final_useful_god_summary.primary_element == "metal"
    assert loaded.final_report_v0.method == "final_report_v0"
    assert rules.career_reading_v0.conclusion in loaded.final_report_v0.career.text
    assert rules.wealth_reading_v0.conclusion in loaded.final_report_v0.wealth.text
    assert rules.relationship_reading_v0.conclusion in loaded.final_report_v0.relationship.text
