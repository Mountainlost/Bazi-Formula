import json
from pathlib import Path

from bazi.cli import run_calc
from bazi.judge_engine import build_rules_output
from bazi.models import ChartOutput
from bazi.reporter import build_report
from bazi.verifier import audit_outputs

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


def test_audit_rejects_out_of_scope_report_terms(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()
    report["summary"]["text"] += " 唯一最终用神已完全确定，完整格局已定，调候已完成。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["report_boundary_terms_absent"].passed is False


def test_audit_rejects_invalid_determined_final_useful_god(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["final_useful_god_v0"]["status"] = "determined"
    rules["final_useful_god_v0"]["primary_element"] = None
    rules["final_useful_god_v0"]["decision_basis"]["allowed_to_finalize"] = False

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules,
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_useful_god_structure_valid"].passed is False


def test_audit_rejects_climate_without_evidence(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["climate_balance_v0"]["candidate_adjustments"][0]["evidence_refs"] = []

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules,
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["schema_validation"].passed is False


def test_audit_rejects_report_climate_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    candidate_only_chart = _build_candidate_only_climate_chart(chart)
    rules = build_rules_output(candidate_only_chart)
    assert rules.climate_balance_v0.status == "candidate_only"
    report = build_report(candidate_only_chart, rules).model_dump()

    report["climate_balance_summary"]["status"] = "determined"
    report["climate_balance_summary"]["notes"].append(
        {"text": "调候已完成。", "evidence_refs": ["E507"]}
    )

    audit = audit_outputs(
        chart_raw=candidate_only_chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["report_within_chart_rules_scope"].passed is False


def test_audit_rejects_shen_sha_without_evidence(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["shen_sha_v0"]["hits"][0]["evidence_refs"] = []

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules,
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["schema_validation"].passed is False


def test_audit_rejects_report_shen_sha_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["shen_sha_summary"]["notes"].append(
        {"text": "天乙贵人大吉，吉凶已定。", "evidence_refs": ["E604"]}
    )

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["shen_sha_not_fortune_verdict"].passed is False


def test_audit_rejects_annual_flow_without_evidence(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["annual_flow_v0"]["entries"][0]["evidence_refs"] = []

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules,
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["schema_validation"].passed is False


def test_audit_rejects_report_annual_flow_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["annual_flow_summary"]["notes"].append(
        {"text": "该流年大吉，应期已定。", "evidence_refs": ["E704"]}
    )

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["annual_flow_not_fortune_verdict"].passed is False


def test_audit_rejects_annual_reading_absolute_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["annual_reading_v0"]["entries"][0]["summary"] += " 2028年一定升职发财。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules,
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["annual_reading_not_absolute_verdict"].passed is False


def test_audit_rejects_final_report_candidate_to_final_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["wealth"]["text"] += " 候选用神就是最终用神。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_report_candidate_not_finalized"].passed is False


def test_audit_rejects_final_report_shen_sha_and_annual_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["relationship"]["text"] += " 天乙贵人大吉，2006年应期已定。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_report_shen_sha_not_fortune_verdict"].passed is False
    assert checks["final_report_annual_flow_not_fortune_verdict"].passed is False


def test_audit_rejects_final_report_climate_as_final_useful_god(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["career"]["text"] += " 调候层已直接给出最终用神。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_report_climate_not_final_useful_god"].passed is False


def test_audit_rejects_final_report_future_five_years_absolute_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["future_five_years"]["entries"][0]["text"] += " 2028年一定升职发财并遇到贵人。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_report_future_five_years_not_absolute_verdict"].passed is False
