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


def test_shen_sha_v0_is_written_for_user_001(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    shen_sha = rules.shen_sha_v0
    assert shen_sha.method == "shen_sha_v0"
    assert shen_sha.status == "determined"
    assert [item.key for item in shen_sha.hits] == ["tianyi_guiren"]
    assert [item.name for item in shen_sha.hits] == ["天乙贵人"]
    assert shen_sha.hits[0].basis.basis_type == "day_stem"
    assert shen_sha.hits[0].basis.basis_value == "辛"
    assert shen_sha.hits[0].matched_pillar_refs[0].pillar == "hour"
    assert shen_sha.hits[0].matched_pillar_refs[0].target_value == "午"
    assert shen_sha.evidence_refs
    assert rules.final_useful_god_v0.primary_element == "metal"


def test_shen_sha_hits_are_structured_without_verdict_fields(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    hit_dump = rules.shen_sha_v0.hits[0].model_dump()
    assert set(hit_dump) == {"key", "name", "basis", "matched_pillar_refs", "evidence_refs"}
    assert "reason" not in hit_dump
    assert "吉" not in json.dumps(
        [item.model_dump() for item in rules.shen_sha_v0.hits],
        ensure_ascii=False,
    )


def test_report_shen_sha_summary_only_restates_rules(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    assert report.shen_sha_summary == rules.shen_sha_v0
    assert report.shen_sha_summary.status == rules.shen_sha_v0.status
