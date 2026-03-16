import json
from pathlib import Path

from bazi.cli import run_calc
from bazi.judge_engine import build_rules_output
from bazi.models import ChartOutput

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"
GOLDEN_DIR = ROOT / "测试样本"


def _load_rules(tmp_path: Path) -> dict:
    chart_path = tmp_path / "chart.json"
    run_calc(USER_INPUT_DIR / "user_001.json", chart_path)
    chart = ChartOutput.model_validate(json.loads(chart_path.read_text(encoding="utf-8")))
    return build_rules_output(chart).model_dump()


def test_ten_gods_mapping_matches_user_001_golden(tmp_path: Path) -> None:
    rules = _load_rules(tmp_path)

    visible = {(item["pillar"], item["stem"]): item["god"] for item in rules["ten_gods"]["stems_visible"]}
    assert visible[("year", "乙")] == "偏财"
    assert visible[("month", "丁")] == "七杀"
    assert visible[("day", "辛")] == "day_master"
    assert visible[("hour", "甲")] == "正财"

    hidden = {
        (item["pillar"], item["branch"]): [hidden_item["god"] for hidden_item in item["hidden_stems"]]
        for item in rules["ten_gods"]["branches_hidden"]
    }
    assert hidden[("year", "亥")] == ["伤官", "正财"]
    assert hidden[("month", "亥")] == ["伤官", "正财"]
    assert hidden[("day", "亥")] == ["伤官", "正财"]
    assert hidden[("hour", "午")] == ["七杀", "偏印"]


def test_rules_and_golden_sample_match(tmp_path: Path) -> None:
    rules = _load_rules(tmp_path)
    golden = json.loads((GOLDEN_DIR / "user_001_rules_golden.json").read_text(encoding="utf-8"))

    assert rules == golden
    assert rules["rules_version"] == "bazi-rules-shen-sha-v5"
    assert rules["strength"]["label"] == "weak"
    assert rules["strength"]["summary"] == "偏弱"

    annual_reading = rules["annual_reading_v0"]
    assert annual_reading["method"] == "annual_reading_v0"
    assert annual_reading["status"] == "determined"
    assert [item["year"] for item in annual_reading["entries"]] == [2026, 2027, 2028, 2029, 2030]
    assert annual_reading["entries"][0]["career_signal"] == "cautious"
    assert annual_reading["entries"][2]["career_signal"] == "favorable"

    career = rules["career_reading_v0"]
    assert career["method"] == "career_reading_v0"
    assert career["status"] == "determined"
    assert career["base_support"] in {"positive", "favorable"}
    assert career["current_phase"] == "cautious"
    assert career["growth_mode"] in {"steady_build", "leverage_support", "active_breakthrough"}
    assert career["future_tendency"] in {"positive", "favorable"}
    assert career["resource_support"] in {"mixed", "positive", "favorable"}
    assert career["conclusion"]
    assert career["evidence_refs"]

    wealth = rules["wealth_reading_v0"]
    assert wealth["method"] == "wealth_reading_v0"
    assert wealth["status"] == "determined"
    assert wealth["base_support"] in {"positive", "favorable"}
    assert wealth["current_phase"] == "cautious"
    assert wealth["wealth_mode"] in {"steady_accumulation", "leverage_growth", "risk_control"}
    assert wealth["future_tendency"] in {"positive", "favorable"}
    assert wealth["resource_support"] in {"mixed", "positive", "favorable"}
    assert wealth["risk_control"] in {
        "tight_control",
        "balanced_control",
        "measured_expansion",
    }
    assert wealth["conclusion"]
    assert wealth["evidence_refs"]

    relationship = rules["relationship_reading_v0"]
    assert relationship["method"] == "relationship_reading_v0"
    assert relationship["status"] == "determined"
    assert relationship["base_support"] in {"positive", "favorable"}
    assert relationship["partner_support"] in {"mixed", "positive", "favorable"}
    assert relationship["stability_tendency"] in {"positive", "favorable"}
    assert relationship["current_phase"] == "cautious"
    assert relationship["future_tendency"] == "favorable"
    assert relationship["conclusion"]
    assert relationship["evidence_refs"]

    final_result = rules["final_useful_god_v0"]
    assert final_result["status"] == "determined"
    assert final_result["primary_element"] == "metal"
    assert final_result["secondary_elements"] == ["earth"]
    assert final_result["decision_basis"]["allowed_to_finalize"] is True
