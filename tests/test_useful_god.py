import json
from pathlib import Path

from bazi.cli import run_calc
from bazi.judge_engine import build_rules_output
from bazi.models import CandidateElement, ChartOutput, EvidenceNote, ProvisionalConclusions, StrengthOutput
from bazi.reporter import build_report
from bazi.useful_god import build_final_useful_god

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"


def _load_chart(tmp_path: Path) -> ChartOutput:
    chart_path = tmp_path / "chart.json"
    run_calc(USER_INPUT_DIR / "user_001.json", chart_path)
    return ChartOutput.model_validate(json.loads(chart_path.read_text(encoding="utf-8")))


def test_user_001_final_useful_god_is_determined(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    result = rules.final_useful_god_v0
    assert result.status == "determined"
    assert result.primary_element == "metal"
    assert result.secondary_elements == ["earth"]
    assert result.decision_basis.allowed_to_finalize is True
    assert result.decision_basis.conflict_detected is False
    assert result.evidence_refs


def test_balanced_strength_does_not_finalize(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    balanced_strength = StrengthOutput(
        score=4,
        label="balanced",
        summary="中和",
        factors=rules.strength.factors,
        evidence_refs=rules.strength.evidence_refs,
    )
    provisional = ProvisionalConclusions(
        favorable_elements_candidates=[],
        unfavorable_elements_candidates=[],
        method="candidate_only_v0",
        notes=[EvidenceNote(text="当前基础旺衰评分为中和。", evidence_refs=["E204"])],
    )

    result = build_final_useful_god(chart, balanced_strength, rules.ten_gods, provisional)
    assert result.status == "insufficient_for_final_determination"
    assert result.primary_element is None
    assert result.decision_basis.allowed_to_finalize is False


def test_conflicting_candidate_does_not_finalize(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    conflicting_provisional = ProvisionalConclusions(
        favorable_elements_candidates=[
            CandidateElement(
                element="fire",
                reason="构造冲突候选。",
                evidence_refs=["E201", "E206"],
            )
        ],
        unfavorable_elements_candidates=[],
        method="candidate_only_v0",
        notes=[EvidenceNote(text="构造冲突候选。", evidence_refs=["E107"])],
    )

    result = build_final_useful_god(chart, rules.strength, rules.ten_gods, conflicting_provisional)
    assert result.status == "blocked_by_conflict"
    assert result.primary_element is None
    assert result.decision_basis.allowed_to_finalize is False
    assert result.decision_basis.conflict_detected is True


def test_report_does_not_upgrade_insufficient_to_determined(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    insufficient_final = build_final_useful_god(
        chart,
        StrengthOutput(
            score=4,
            label="balanced",
            summary="中和",
            factors=rules.strength.factors,
            evidence_refs=rules.strength.evidence_refs,
        ),
        rules.ten_gods,
        ProvisionalConclusions(
            favorable_elements_candidates=[],
            unfavorable_elements_candidates=[],
            method="candidate_only_v0",
            notes=[EvidenceNote(text="当前基础旺衰评分为中和。", evidence_refs=["E204"])],
        ),
    )

    rules_data = rules.model_dump()
    rules_data["final_useful_god_v0"] = insufficient_final.model_dump()
    rebuilt_rules = type(rules).model_validate(rules_data)
    report = build_report(chart, rebuilt_rules)

    assert report.final_useful_god_summary.status == "insufficient_for_final_determination"
    assert report.final_useful_god_summary.primary_element is None
    assert "最终用神受控版 v0 当前证据不足" in report.final_useful_god_summary.text
