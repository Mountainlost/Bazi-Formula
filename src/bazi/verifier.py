from __future__ import annotations

import json
from typing import Iterable

from pydantic import ValidationError

from . import AUDIT_VERSION
from .judge_engine import build_rules_output
from .luck_cycle import calculate_luck_cycle
from .models import (
    AnnualReadingOutput,
    AnnualFlowOutput,
    AuditCheck,
    AuditOutput,
    BaziInput,
    CareerReadingOutput,
    ChartOutput,
    ClimateBalanceOutput,
    FinalReportOutput,
    FinalUsefulGodOutput,
    PatternSystemOutput,
    ProvisionalConclusions,
    ReportOutput,
    RelationshipReadingOutput,
    RulesOutput,
    ShenShaOutput,
    WealthReadingOutput,
)
from .reporter import build_report
from .rule_data import load_enabled_evidence_ids

FORBIDDEN_SCHOOL_TERMS = ("紫微", "六爻", "西占", "塔罗", "奇门")
FORBIDDEN_DEFINITIVE_TERMS = (
    "最终用神",
    "唯一用神",
    "唯一喜用",
    "definitive",
    "final useful god",
)
FORBIDDEN_REPORT_BOUNDARY_TERMS = (
    "唯一最终用神已完全确定",
    "完整格局已定",
    "调候已完成",
    "神煞定论",
)
FORBIDDEN_SHEN_SHA_VERDICT_TERMS = (
    "大吉",
    "大凶",
    "必贵",
    "富贵定论",
    "吉凶已定",
)
FORBIDDEN_ANNUAL_FLOW_VERDICT_TERMS = (
    "大吉",
    "大凶",
    "吉凶已定",
    "应期",
    "断语",
    "事件预测结论",
)
FORBIDDEN_FINAL_REPORT_CANDIDATE_FINAL_TERMS = (
    "候选用神已定",
    "候选用神就是最终用神",
    "候选方向已定为最终用神",
)
FORBIDDEN_FINAL_REPORT_CLIMATE_FINAL_TERMS = (
    "调候候选已定为最终用神",
    "调候层已直接给出最终用神",
)
FORBIDDEN_ANNUAL_READING_ABSOLUTE_TERMS = (
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
)
FORBIDDEN_ANNUAL_READING_NEUTRAL_TERMS = (
    "以中性阅读为主",
    "中性阅读为宜",
    "neutral",
)
FORBIDDEN_CAREER_ABSOLUTE_TERMS = (
    "一定升职",
    "保证升职",
    "必然晋升",
    "一定创业成功",
    "创业必成",
    "必然换工作",
    "一定跳槽成功",
)
FORBIDDEN_CAREER_SHEN_SHA_TERMS = (
    "天乙贵人定事业",
    "文昌定事业",
    "神煞定事业",
)
FORBIDDEN_CAREER_ANNUAL_FLOW_TERMS = (
    "流年骨架定事业",
    "干支骨架定事业",
    "annual_flow_v0直接定事业",
)
FORBIDDEN_WEALTH_ABSOLUTE_TERMS = (
    "一定发财",
    "一定赚大钱",
    "必然暴富",
    "财务自由已定",
    "投资必赚",
    "必然投资成功",
    "某年一定发财",
    "一定买房",
)
FORBIDDEN_WEALTH_SHEN_SHA_TERMS = (
    "天乙贵人定财运",
    "文昌定财运",
    "驿马定财运",
    "神煞定财运",
)
FORBIDDEN_WEALTH_ANNUAL_FLOW_TERMS = (
    "流年骨架定财运",
    "干支骨架定财运",
    "annual_flow_v0直接定财运",
)
FORBIDDEN_RELATIONSHIP_ABSOLUTE_TERMS = (
    "一定结婚",
    "一定遇到正缘",
    "正缘必到",
    "必然结婚",
    "必然分手",
    "注定分开",
    "一定复合",
    "必然复合",
)
FORBIDDEN_RELATIONSHIP_SHEN_SHA_TERMS = (
    "天乙贵人定婚",
    "桃花定婚",
    "神煞定婚恋",
    "神煞定姻缘",
)
FORBIDDEN_RELATIONSHIP_ANNUAL_FLOW_TERMS = (
    "流年骨架定婚恋",
    "干支骨架定婚恋",
    "annual_flow_v0直接定婚恋",
)
NEGATED_ANNUAL_FLOW_VERDICT_PATTERNS = (
    "涓嶅疁浣滀簨浠舵€ф柇璇?",
    "涓嶅睍寮€鍏蜂綋浜嬩欢棰勬祴銆佹祦鏈堟垨缁濆鏂",
)
NEGATED_DEFINITIVE_PATTERNS = (
    "不等同最终用神",
    "不是最终用神",
    "非最终用神",
    "不能安全地给出最终用神",
    "cannot safely determine",
    "not definitive",
    "not final useful god",
)
NEGATED_ANNUAL_FLOW_VERDICT_PATTERNS_V0 = (
    "\u4e0d\u5b9c\u4f5c\u4e8b\u4ef6\u6027\u65ad\u8bed",
    "\u4e0d\u4f5c\u4e8b\u4ef6\u6027\u65ad\u8bed",
    "\u4e0d\u5c55\u5f00\u5177\u4f53\u4e8b\u4ef6\u9884\u6d4b\u3001\u6d41\u6708\u6216\u7edd\u5bf9\u65ad\u8bed",
)
CHART_FIELDS = {
    "engine_version",
    "school",
    "calc_basis",
    "input_snapshot",
    "solar_datetime",
    "pillars",
    "day_master",
    "luck_cycle",
    "status",
}
RULES_FIELDS = {
    "rules_version",
    "engine_version",
    "based_on_chart_version",
    "status",
    "day_master",
    "summary",
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
}
REPORT_FIELDS = {
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
}


def _find_extra_fields(raw_data: dict, allowed_fields: Iterable[str]) -> list[str]:
    return sorted(set(raw_data).difference(set(allowed_fields)))


def _safe_version(raw_data: dict, field_name: str) -> str:
    value = raw_data.get(field_name)
    return value if isinstance(value, str) else "unknown"


def _append_unique(target: list[str], refs: Iterable[str]) -> None:
    for ref in refs:
        if ref not in target:
            target.append(ref)


def _collect_provisional_refs(provisional: ProvisionalConclusions) -> list[str]:
    refs: list[str] = []
    for item in provisional.favorable_elements_candidates:
        _append_unique(refs, item.evidence_refs)
    for item in provisional.unfavorable_elements_candidates:
        _append_unique(refs, item.evidence_refs)
    for note in provisional.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_pattern_refs(pattern_system: PatternSystemOutput) -> list[str]:
    refs = list(pattern_system.evidence_refs)
    if pattern_system.candidate_pattern is not None:
        _append_unique(refs, pattern_system.candidate_pattern.evidence_refs)
    if pattern_system.final_pattern is not None:
        _append_unique(refs, pattern_system.final_pattern.evidence_refs)
    for note in pattern_system.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_climate_refs(climate_balance: ClimateBalanceOutput) -> list[str]:
    refs = list(climate_balance.evidence_refs)
    if climate_balance.season_context is not None:
        _append_unique(refs, climate_balance.season_context.evidence_refs)
    for item in climate_balance.candidate_adjustments:
        _append_unique(refs, item.evidence_refs)
    for note in climate_balance.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_annual_flow_refs(annual_flow: AnnualFlowOutput) -> list[str]:
    refs = list(annual_flow.evidence_refs)
    for entry in annual_flow.entries:
        _append_unique(refs, entry.evidence_refs)
    for note in annual_flow.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_annual_reading_refs(annual_reading: AnnualReadingOutput) -> list[str]:
    refs = list(annual_reading.evidence_refs)
    for entry in annual_reading.entries:
        _append_unique(refs, entry.evidence_refs)
    for note in annual_reading.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_career_reading_refs(career_reading: CareerReadingOutput) -> list[str]:
    refs = list(career_reading.evidence_refs)
    for note in career_reading.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_relationship_reading_refs(
    relationship_reading: RelationshipReadingOutput,
) -> list[str]:
    refs = list(relationship_reading.evidence_refs)
    for note in relationship_reading.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_wealth_reading_refs(wealth_reading: WealthReadingOutput) -> list[str]:
    refs = list(wealth_reading.evidence_refs)
    for note in wealth_reading.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_shen_sha_refs(shen_sha: ShenShaOutput) -> list[str]:
    refs = list(shen_sha.evidence_refs)
    for hit in shen_sha.hits:
        _append_unique(refs, hit.evidence_refs)
        _append_unique(refs, hit.basis.evidence_refs)
        for matched in hit.matched_pillar_refs:
            _append_unique(refs, matched.evidence_refs)
    for note in shen_sha.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_final_refs(final_output: FinalUsefulGodOutput) -> list[str]:
    refs = list(final_output.evidence_refs)
    for item in final_output.reason_chain:
        _append_unique(refs, item.evidence_refs)
    for item in final_output.blockers:
        _append_unique(refs, item.evidence_refs)
    return refs


def _collect_chart_refs(chart: ChartOutput) -> list[str]:
    refs: list[str] = []
    if chart.calc_basis.normalization_steps:
        for step in chart.calc_basis.normalization_steps:
            _append_unique(refs, step.evidence_refs)
    _append_unique(refs, chart.luck_cycle.evidence_refs)
    for cycle in chart.luck_cycle.cycles:
        _append_unique(refs, cycle.evidence_refs)
    return refs


def _collect_rules_refs(rules: RulesOutput) -> list[str]:
    refs: list[str] = []
    for item in rules.ten_gods.stems_visible:
        _append_unique(refs, item.evidence_refs)
    for branch_item in rules.ten_gods.branches_hidden:
        for hidden_item in branch_item.hidden_stems:
            _append_unique(refs, hidden_item.evidence_refs)
    for factor in rules.strength.factors:
        _append_unique(refs, factor.evidence_refs)
    _append_unique(refs, rules.strength.evidence_refs)
    _append_unique(refs, _collect_pattern_refs(rules.pattern_system_v1))
    _append_unique(refs, _collect_climate_refs(rules.climate_balance_v0))
    _append_unique(refs, _collect_annual_flow_refs(rules.annual_flow_v0))
    _append_unique(refs, _collect_annual_reading_refs(rules.annual_reading_v0))
    _append_unique(refs, _collect_career_reading_refs(rules.career_reading_v0))
    _append_unique(refs, _collect_wealth_reading_refs(rules.wealth_reading_v0))
    _append_unique(refs, _collect_relationship_reading_refs(rules.relationship_reading_v0))
    _append_unique(refs, _collect_shen_sha_refs(rules.shen_sha_v0))
    _append_unique(refs, _collect_provisional_refs(rules.provisional_conclusions))
    _append_unique(refs, _collect_final_refs(rules.final_useful_god_v0))
    return refs


def _collect_report_refs(report: ReportOutput) -> list[str]:
    refs: list[str] = []
    _append_unique(refs, report.summary.evidence_refs)
    for item in report.ten_gods_summary.stems_visible:
        _append_unique(refs, item.evidence_refs)
    for branch_item in report.ten_gods_summary.branches_hidden:
        for hidden_item in branch_item.hidden_stems:
            _append_unique(refs, hidden_item.evidence_refs)
    _append_unique(refs, report.ten_gods_summary.evidence_refs)
    _append_unique(refs, report.strength_summary.evidence_refs)
    _append_unique(refs, _collect_pattern_refs(report.pattern_system_summary))
    _append_unique(refs, _collect_climate_refs(report.climate_balance_summary))
    _append_unique(refs, _collect_annual_flow_refs(report.annual_flow_summary))
    _append_unique(refs, _collect_annual_reading_refs(report.annual_reading_summary))
    _append_unique(refs, _collect_career_reading_refs(report.career_reading_summary))
    _append_unique(refs, _collect_wealth_reading_refs(report.wealth_reading_summary))
    _append_unique(refs, _collect_relationship_reading_refs(report.relationship_reading_summary))
    _append_unique(refs, _collect_shen_sha_refs(report.shen_sha_summary))
    _append_unique(refs, _collect_provisional_refs(report.candidate_elements_summary))
    _append_unique(refs, report.final_useful_god_summary.evidence_refs)
    _append_unique(refs, report.final_report_v0.summary.evidence_refs)
    _append_unique(refs, report.final_report_v0.career.evidence_refs)
    _append_unique(refs, report.final_report_v0.wealth.evidence_refs)
    _append_unique(refs, report.final_report_v0.relationship.evidence_refs)
    _append_unique(refs, report.final_report_v0.future_five_years.overview.evidence_refs)
    _append_unique(refs, report.final_report_v0.future_five_years.evidence_refs)
    for entry in report.final_report_v0.future_five_years.entries:
        _append_unique(refs, entry.evidence_refs)
    _append_unique(refs, report.final_report_v0.evidence_refs)
    for note in report.final_report_v0.limitations:
        _append_unique(refs, note.evidence_refs)
    _append_unique(refs, report.luck_cycle_summary.evidence_refs)
    for cycle in report.luck_cycle_summary.cycles:
        _append_unique(refs, cycle.evidence_refs)
    for note in report.caveats:
        _append_unique(refs, note.evidence_refs)
    return refs


def _candidate_items_have_refs(provisional: ProvisionalConclusions) -> bool:
    items = [
        *provisional.favorable_elements_candidates,
        *provisional.unfavorable_elements_candidates,
    ]
    return all(bool(item.evidence_refs) for item in items)


def _contains_forbidden_terms(
    texts: Iterable[str],
    forbidden_terms: Iterable[str],
    negated_patterns: Iterable[str] = (),
) -> list[str]:
    lowered = "\n".join(texts).lower()
    hits: list[str] = []
    for pattern in negated_patterns:
        lowered = lowered.replace(pattern.lower(), "")
    for term in forbidden_terms:
        if term.lower() in lowered and term not in hits:
            hits.append(term)
    return hits


def _provisional_texts(provisional: ProvisionalConclusions) -> list[str]:
    texts = [item.reason for item in provisional.favorable_elements_candidates]
    texts.extend(item.reason for item in provisional.unfavorable_elements_candidates)
    texts.extend(note.text for note in provisional.notes)
    return texts


def _climate_texts(climate_balance: ClimateBalanceOutput) -> list[str]:
    texts = [item.reason for item in climate_balance.candidate_adjustments]
    texts.extend(note.text for note in climate_balance.notes)
    return texts


def _shen_sha_texts(shen_sha: ShenShaOutput) -> list[str]:
    return [note.text for note in shen_sha.notes]


def _annual_flow_texts(annual_flow: AnnualFlowOutput) -> list[str]:
    return [note.text for note in annual_flow.notes]


def _annual_reading_texts(annual_reading: AnnualReadingOutput) -> list[str]:
    texts = [item.summary for item in annual_reading.entries]
    texts.extend(note.text for note in annual_reading.notes)
    return texts


def _career_reading_texts(career_reading: CareerReadingOutput) -> list[str]:
    texts = [career_reading.conclusion]
    texts.extend(note.text for note in career_reading.notes)
    return texts


def _relationship_reading_texts(relationship_reading: RelationshipReadingOutput) -> list[str]:
    texts = [relationship_reading.conclusion]
    texts.extend(note.text for note in relationship_reading.notes)
    return texts


def _wealth_reading_texts(wealth_reading: WealthReadingOutput) -> list[str]:
    texts = [wealth_reading.conclusion]
    texts.extend(note.text for note in wealth_reading.notes)
    return texts


def _final_report_texts(final_report: FinalReportOutput) -> list[str]:
    texts = [
        final_report.summary.text,
        final_report.career.text,
        final_report.wealth.text,
        final_report.relationship.text,
        final_report.future_five_years.overview.text,
    ]
    texts.extend(item.text for item in final_report.future_five_years.entries)
    texts.extend(note.text for note in final_report.limitations)
    return texts


def _future_five_years_texts(final_report: FinalReportOutput) -> list[str]:
    texts = [final_report.future_five_years.overview.text]
    texts.extend(item.text for item in final_report.future_five_years.entries)
    return texts


def _pattern_system_section_valid(pattern_system: PatternSystemOutput) -> tuple[bool, str]:
    if not pattern_system.evidence_refs:
        return False, "pattern_system_v1 must include evidence_refs."
    if not pattern_system.notes:
        return False, "pattern_system_v1 must include notes."

    if pattern_system.status == "determined":
        candidate = pattern_system.candidate_pattern
        final = pattern_system.final_pattern
        if candidate is None or final is None:
            return False, "determined pattern_system_v1 must include candidate_pattern and final_pattern."
        if candidate.pattern_key != final.pattern_key or candidate.pattern_name != final.pattern_name:
            return False, "candidate_pattern and final_pattern must align when determined."
        if candidate.transparency != "visible" or final.transparency != "visible":
            return False, "determined pattern_system_v1 must use visible transparency."
        return True, "pattern_system_v1 determined state is structurally valid."

    if pattern_system.status == "candidate_only":
        candidate = pattern_system.candidate_pattern
        if candidate is None:
            return False, "candidate_only pattern_system_v1 must include candidate_pattern."
        if pattern_system.final_pattern is not None:
            return False, "candidate_only pattern_system_v1 must not include final_pattern."
        if candidate.transparency != "hidden_only":
            return False, "candidate_only pattern_system_v1 must keep transparency=hidden_only."
        return True, "pattern_system_v1 candidate_only state is structurally valid."

    if pattern_system.candidate_pattern is not None or pattern_system.final_pattern is not None:
        return False, "insufficient_for_determination pattern_system_v1 must not force pattern output."
    return True, "pattern_system_v1 insufficient state is structurally valid."


def _climate_balance_section_valid(climate_balance: ClimateBalanceOutput) -> tuple[bool, str]:
    if not climate_balance.evidence_refs:
        return False, "climate_balance_v0 must include evidence_refs."
    if not climate_balance.notes:
        return False, "climate_balance_v0 must include notes."

    priorities = [item.priority for item in climate_balance.candidate_adjustments]
    if priorities and (priorities != sorted(priorities) or len(priorities) != len(set(priorities))):
        return False, "climate_balance_v0 candidate_adjustments must use unique ascending priorities."
    if any(not item.evidence_refs for item in climate_balance.candidate_adjustments):
        return False, "every climate_balance_v0 candidate_adjustment must include evidence_refs."

    if climate_balance.status == "determined":
        if climate_balance.season_context is None:
            return False, "determined climate_balance_v0 must include season_context."
        if not climate_balance.candidate_adjustments:
            return False, "determined climate_balance_v0 must include candidate_adjustments."
        if not climate_balance.season_context.detected_tendencies:
            return False, "determined climate_balance_v0 must include detected_tendencies."
        return True, "climate_balance_v0 determined state is structurally valid."

    if climate_balance.status == "candidate_only":
        if climate_balance.season_context is None:
            return False, "candidate_only climate_balance_v0 must include season_context."
        if not climate_balance.candidate_adjustments:
            return False, "candidate_only climate_balance_v0 must include candidate_adjustments."
        return True, "climate_balance_v0 candidate_only state is structurally valid."

    if climate_balance.candidate_adjustments:
        return False, "insufficient_for_determination climate_balance_v0 must not force candidate_adjustments."
    return True, "climate_balance_v0 insufficient state is structurally valid."


def _shen_sha_section_valid(shen_sha: ShenShaOutput) -> tuple[bool, str]:
    if not shen_sha.evidence_refs:
        return False, "shen_sha_v0 must include evidence_refs."
    if not shen_sha.notes:
        return False, "shen_sha_v0 must include notes."

    if shen_sha.status == "determined":
        for hit in shen_sha.hits:
            if not hit.evidence_refs:
                return False, "every shen_sha_v0 hit must include evidence_refs."
            if not hit.basis.evidence_refs:
                return False, "every shen_sha_v0 basis must include evidence_refs."
            if not hit.matched_pillar_refs:
                return False, "every shen_sha_v0 hit must include matched_pillar_refs."
            for matched in hit.matched_pillar_refs:
                if not matched.evidence_refs:
                    return False, "every shen_sha_v0 matched_pillar_ref must include evidence_refs."
        return True, "shen_sha_v0 determined state is structurally valid."

    if shen_sha.hits:
        return False, "insufficient_for_determination shen_sha_v0 must not force hits."
    return True, "shen_sha_v0 insufficient state is structurally valid."


def _annual_flow_section_valid(annual_flow: AnnualFlowOutput) -> tuple[bool, str]:
    if not annual_flow.evidence_refs:
        return False, "annual_flow_v0 must include evidence_refs."
    if not annual_flow.notes:
        return False, "annual_flow_v0 must include notes."
    if annual_flow.window.preview_year_count < 1:
        return False, "annual_flow_v0 preview_year_count must be positive."

    if annual_flow.status == "determined":
        start_year = annual_flow.window.start_year
        end_year = annual_flow.window.end_year
        if start_year is None or end_year is None:
            return False, "determined annual_flow_v0 must include start_year and end_year."
        if not annual_flow.entries:
            return False, "determined annual_flow_v0 must include entries."
        expected_count = annual_flow.window.preview_year_count
        if len(annual_flow.entries) != expected_count:
            return False, "determined annual_flow_v0 entries must match preview_year_count."
        if end_year != start_year + expected_count - 1:
            return False, "annual_flow_v0 end_year must align with the fixed preview window."
        expected_years = list(range(start_year, end_year + 1))
        actual_years = [entry.year for entry in annual_flow.entries]
        if actual_years != expected_years:
            return False, "annual_flow_v0 entries must use consecutive ascending years."
        if [entry.relative_index for entry in annual_flow.entries] != list(range(expected_count)):
            return False, "annual_flow_v0 relative_index must start at 0 and increase by 1."
        if any(not entry.evidence_refs for entry in annual_flow.entries):
            return False, "every annual_flow_v0 entry must include evidence_refs."
        return True, "annual_flow_v0 determined state is structurally valid."

    if annual_flow.entries:
        return False, "insufficient_for_determination annual_flow_v0 must not force entries."
    if annual_flow.window.start_year is not None or annual_flow.window.end_year is not None:
        return False, "insufficient_for_determination annual_flow_v0 must not force a resolved year window."
    return True, "annual_flow_v0 insufficient state is structurally valid."


def _annual_reading_section_valid(annual_reading: AnnualReadingOutput) -> tuple[bool, str]:
    if not annual_reading.evidence_refs:
        return False, "annual_reading_v0 must include evidence_refs."
    if not annual_reading.notes:
        return False, "annual_reading_v0 must include notes."
    if annual_reading.window.preview_year_count < 1:
        return False, "annual_reading_v0 preview_year_count must be positive."

    if annual_reading.status == "determined":
        start_year = annual_reading.window.start_year
        end_year = annual_reading.window.end_year
        if start_year is None or end_year is None:
            return False, "determined annual_reading_v0 must include start_year and end_year."
        expected_count = annual_reading.window.preview_year_count
        if len(annual_reading.entries) != expected_count:
            return False, "determined annual_reading_v0 entries must match preview_year_count."
        if end_year != start_year + expected_count - 1:
            return False, "annual_reading_v0 end_year must align with the fixed preview window."
        actual_years = [entry.year for entry in annual_reading.entries]
        if actual_years != list(range(start_year, end_year + 1)):
            return False, "annual_reading_v0 entries must use consecutive ascending years."
        for entry in annual_reading.entries:
            if not entry.summary:
                return False, "annual_reading_v0 entries must include summary."
            if not entry.evidence_refs:
                return False, "every annual_reading_v0 entry must include evidence_refs."
        return True, "annual_reading_v0 determined state is structurally valid."

    if annual_reading.entries:
        return False, "insufficient_for_determination annual_reading_v0 must not force entries."
    if annual_reading.window.start_year is not None or annual_reading.window.end_year is not None:
        return False, "insufficient_for_determination annual_reading_v0 must not force a resolved year window."
    return True, "annual_reading_v0 insufficient state is structurally valid."


def _career_reading_section_valid(career_reading: CareerReadingOutput) -> tuple[bool, str]:
    if not career_reading.evidence_refs:
        return False, "career_reading_v0 must include evidence_refs."
    if not career_reading.notes:
        return False, "career_reading_v0 must include notes."
    if not career_reading.conclusion:
        return False, "career_reading_v0 must include conclusion."
    return True, f"career_reading_v0 {career_reading.status} state is structurally valid."


def _relationship_reading_section_valid(
    relationship_reading: RelationshipReadingOutput,
) -> tuple[bool, str]:
    if not relationship_reading.evidence_refs:
        return False, "relationship_reading_v0 must include evidence_refs."
    if not relationship_reading.notes:
        return False, "relationship_reading_v0 must include notes."
    if not relationship_reading.conclusion:
        return False, "relationship_reading_v0 must include conclusion."
    return True, f"relationship_reading_v0 {relationship_reading.status} state is structurally valid."


def _wealth_reading_section_valid(wealth_reading: WealthReadingOutput) -> tuple[bool, str]:
    if not wealth_reading.evidence_refs:
        return False, "wealth_reading_v0 must include evidence_refs."
    if not wealth_reading.notes:
        return False, "wealth_reading_v0 must include notes."
    if not wealth_reading.conclusion:
        return False, "wealth_reading_v0 must include conclusion."
    return True, f"wealth_reading_v0 {wealth_reading.status} state is structurally valid."


def _final_report_section_valid(final_report: FinalReportOutput) -> tuple[bool, str]:
    if not final_report.evidence_refs:
        return False, "final_report_v0 must include evidence_refs."
    sections = [
        final_report.summary,
        final_report.career,
        final_report.wealth,
        final_report.relationship,
    ]
    if any(not section.text for section in sections):
        return False, "final_report_v0 sections must include text."
    if any(not section.evidence_refs for section in sections):
        return False, "final_report_v0 sections must include evidence_refs."
    if not final_report.future_five_years.overview.text:
        return False, "final_report_v0 future_five_years must include overview text."
    if not final_report.future_five_years.overview.evidence_refs:
        return False, "final_report_v0 future_five_years overview must include evidence_refs."
    if not final_report.future_five_years.evidence_refs:
        return False, "final_report_v0 future_five_years must include evidence_refs."
    if any(not item.evidence_refs for item in final_report.future_five_years.entries):
        return False, "final_report_v0 future_five_years entries must include evidence_refs."
    if not final_report.limitations:
        return False, "final_report_v0 must include limitations."
    if any(not note.evidence_refs for note in final_report.limitations):
        return False, "final_report_v0 limitations must include evidence_refs."
    return True, "final_report_v0 structure is valid."


def _final_section_valid(final_output: FinalUsefulGodOutput) -> tuple[bool, str]:
    if final_output.status == "determined":
        if final_output.primary_element is None:
            return False, "determined final_useful_god_v0 must include primary_element."
        if not final_output.evidence_refs:
            return False, "determined final_useful_god_v0 must include evidence_refs."
        if not final_output.decision_basis.allowed_to_finalize:
            return False, "determined final_useful_god_v0 must set allowed_to_finalize=true."
        if final_output.decision_basis.conflict_detected:
            return False, "determined final_useful_god_v0 cannot keep conflict_detected=true."
        if final_output.decision_basis.strength_label == "balanced":
            return False, "balanced strength cannot finalize final_useful_god_v0."
        return True, "final_useful_god_v0 determined state is structurally valid."

    if final_output.primary_element is not None:
        return False, "non-determined final_useful_god_v0 must not force primary_element."
    if final_output.decision_basis.allowed_to_finalize:
        return False, "non-determined final_useful_god_v0 must keep allowed_to_finalize=false."
    if not final_output.blockers and not final_output.reason_chain:
        return False, "non-determined final_useful_god_v0 must explain why it cannot finalize."
    return True, "final_useful_god_v0 non-determined state is structurally valid."


def _luck_cycle_complete(chart: ChartOutput) -> bool:
    luck_cycle = chart.luck_cycle
    if not luck_cycle.basis.enabled:
        return False
    if luck_cycle.direction not in {"forward", "backward"}:
        return False
    if len(luck_cycle.cycles) < 8:
        return False
    for cycle in luck_cycle.cycles:
        if cycle.start_age >= cycle.end_age:
            return False
        if cycle.start_year >= cycle.end_year:
            return False
        if not cycle.evidence_refs:
            return False
    return True


def audit_outputs(
    chart_raw: dict,
    rules_raw: dict,
    report_raw: dict,
    chart_exists: bool,
    rules_exists: bool,
    report_exists: bool,
) -> AuditOutput:
    checks: list[AuditCheck] = []

    files_exist = chart_exists and rules_exists and report_exists
    checks.append(
        AuditCheck(
            name="files_exist",
            passed=files_exist,
            message="chart.json, rules.json, and report.json all exist."
            if files_exist
            else "At least one required file is missing.",
        )
    )

    extra_fields = {
        "chart": _find_extra_fields(chart_raw, CHART_FIELDS),
        "rules": _find_extra_fields(rules_raw, RULES_FIELDS),
        "report": _find_extra_fields(report_raw, REPORT_FIELDS),
    }
    checks.append(
        AuditCheck(
            name="no_obvious_extra_fields",
            passed=not any(extra_fields.values()),
            message="No obvious out-of-scope fields were detected."
            if not any(extra_fields.values())
            else f"Unexpected fields detected: {extra_fields}",
        )
    )

    try:
        chart = ChartOutput.model_validate(chart_raw)
        rules = RulesOutput.model_validate(rules_raw)
        report = ReportOutput.model_validate(report_raw)
        schema_valid = True
        schema_message = "chart.json, rules.json, and report.json passed model validation."
    except ValidationError as exc:
        chart = None
        rules = None
        report = None
        schema_valid = False
        schema_message = f"Model validation failed: {exc.errors()}"

    checks.append(
        AuditCheck(
            name="schema_validation",
            passed=schema_valid,
            message=schema_message,
        )
    )

    engine_version = _safe_version(chart_raw, "engine_version")
    rules_version = _safe_version(rules_raw, "rules_version")
    report_version = _safe_version(report_raw, "report_version")

    if not schema_valid or chart is None or rules is None or report is None:
        return AuditOutput(
            audit_version=AUDIT_VERSION,
            engine_version=engine_version,
            rules_version=rules_version,
            report_version=report_version,
            passed=all(check.passed for check in checks),
            checks=checks,
        )

    version_ok = (
        chart.engine_version == rules.engine_version == report.engine_version
        and rules.rules_version == report.rules_version
        and rules.based_on_chart_version == chart.engine_version
    )
    checks.append(
        AuditCheck(
            name="version_alignment",
            passed=version_ok,
            message="engine_version, rules_version, and based_on_chart_version are aligned."
            if version_ok
            else "Version alignment check failed.",
        )
    )

    rules_required_sections_ok = (
        bool(rules.ten_gods.stems_visible)
        and bool(rules.ten_gods.branches_hidden)
        and bool(rules.strength.factors)
        and rules.pattern_system_v1.method == "month_main_qi_pattern_v1"
        and bool(rules.pattern_system_v1.notes)
        and rules.climate_balance_v0.method == "climate_balance_v0"
        and bool(rules.climate_balance_v0.notes)
        and rules.annual_flow_v0.method == "annual_flow_v0"
        and bool(rules.annual_flow_v0.notes)
        and rules.annual_reading_v0.method == "annual_reading_v0"
        and bool(rules.annual_reading_v0.notes)
        and rules.career_reading_v0.method == "career_reading_v0"
        and bool(rules.career_reading_v0.notes)
        and rules.wealth_reading_v0.method == "wealth_reading_v0"
        and bool(rules.wealth_reading_v0.notes)
        and rules.relationship_reading_v0.method == "relationship_reading_v0"
        and bool(rules.relationship_reading_v0.notes)
        and rules.shen_sha_v0.method == "shen_sha_v0"
        and bool(rules.shen_sha_v0.notes)
        and rules.provisional_conclusions.method == "candidate_only_v0"
        and bool(rules.provisional_conclusions.notes)
    )
    checks.append(
        AuditCheck(
            name="rules_required_sections_present",
            passed=rules_required_sections_ok,
            message="rules.json contains all required rule sections."
            if rules_required_sections_ok
            else "rules.json is missing one or more required rule sections.",
        )
    )

    pattern_ok, pattern_message = _pattern_system_section_valid(rules.pattern_system_v1)
    checks.append(
        AuditCheck(
            name="pattern_system_structure_valid",
            passed=pattern_ok,
            message=pattern_message,
        )
    )

    climate_ok, climate_message = _climate_balance_section_valid(rules.climate_balance_v0)
    checks.append(
        AuditCheck(
            name="climate_balance_structure_valid",
            passed=climate_ok,
            message=climate_message,
        )
    )

    annual_flow_ok, annual_flow_message = _annual_flow_section_valid(rules.annual_flow_v0)
    checks.append(
        AuditCheck(
            name="annual_flow_structure_valid",
            passed=annual_flow_ok,
            message=annual_flow_message,
        )
    )

    annual_reading_ok, annual_reading_message = _annual_reading_section_valid(rules.annual_reading_v0)
    checks.append(
        AuditCheck(
            name="annual_reading_structure_valid",
            passed=annual_reading_ok,
            message=annual_reading_message,
        )
    )

    career_reading_ok, career_reading_message = _career_reading_section_valid(
        rules.career_reading_v0
    )
    checks.append(
        AuditCheck(
            name="career_reading_structure_valid",
            passed=career_reading_ok,
            message=career_reading_message,
        )
    )

    wealth_reading_ok, wealth_reading_message = _wealth_reading_section_valid(
        rules.wealth_reading_v0
    )
    checks.append(
        AuditCheck(
            name="wealth_reading_structure_valid",
            passed=wealth_reading_ok,
            message=wealth_reading_message,
        )
    )

    relationship_reading_ok, relationship_reading_message = _relationship_reading_section_valid(
        rules.relationship_reading_v0
    )
    checks.append(
        AuditCheck(
            name="relationship_reading_structure_valid",
            passed=relationship_reading_ok,
            message=relationship_reading_message,
        )
    )

    shen_sha_ok, shen_sha_message = _shen_sha_section_valid(rules.shen_sha_v0)
    checks.append(
        AuditCheck(
            name="shen_sha_structure_valid",
            passed=shen_sha_ok,
            message=shen_sha_message,
        )
    )

    final_section_ok, final_section_message = _final_section_valid(rules.final_useful_god_v0)
    checks.append(
        AuditCheck(
            name="final_useful_god_structure_valid",
            passed=final_section_ok,
            message=final_section_message,
        )
    )

    final_report_ok, final_report_message = _final_report_section_valid(report.final_report_v0)
    checks.append(
        AuditCheck(
            name="final_report_structure_valid",
            passed=final_report_ok,
            message=final_report_message,
        )
    )

    enabled_evidence_ids = load_enabled_evidence_ids()
    chart_refs = _collect_chart_refs(chart)
    rules_refs = _collect_rules_refs(rules)
    report_refs = _collect_report_refs(report)
    unknown_refs = sorted(
        {
            ref
            for ref in [*chart_refs, *rules_refs, *report_refs]
            if ref not in enabled_evidence_ids
        }
    )
    checks.append(
        AuditCheck(
            name="evidence_refs_registered",
            passed=not unknown_refs,
            message="All evidence_refs are registered in evidence_registry.yaml."
            if not unknown_refs
            else f"Unknown evidence_refs detected: {unknown_refs}",
        )
    )

    candidate_refs_ok = _candidate_items_have_refs(rules.provisional_conclusions)
    checks.append(
        AuditCheck(
            name="wealth_reading_has_evidence_refs",
            passed=bool(rules.wealth_reading_v0.evidence_refs),
            message="wealth_reading_v0 includes evidence_refs."
            if rules.wealth_reading_v0.evidence_refs
            else "wealth_reading_v0 is missing evidence_refs.",
        )
    )
    checks.append(
        AuditCheck(
            name="candidate_elements_have_evidence_refs",
            passed=candidate_refs_ok,
            message="Every candidate element includes evidence_refs."
            if candidate_refs_ok
            else "One or more candidate elements are missing evidence_refs.",
        )
    )

    definitive_hits = _contains_forbidden_terms(
        [
            *_provisional_texts(rules.provisional_conclusions),
            *_provisional_texts(report.candidate_elements_summary),
        ],
        FORBIDDEN_DEFINITIVE_TERMS,
        NEGATED_DEFINITIVE_PATTERNS,
    )
    checks.append(
        AuditCheck(
            name="candidate_elements_not_definitive",
            passed=not definitive_hits,
            message="Candidate output remains provisional."
            if not definitive_hits
            else f"Definitive wording detected: {definitive_hits}",
        )
    )

    climate_definitive_hits = _contains_forbidden_terms(
        [
            *_climate_texts(rules.climate_balance_v0),
            *_climate_texts(report.climate_balance_summary),
        ],
        FORBIDDEN_DEFINITIVE_TERMS,
        NEGATED_DEFINITIVE_PATTERNS,
    )
    checks.append(
        AuditCheck(
            name="climate_balance_not_final_useful_god",
            passed=not climate_definitive_hits,
            message="Climate balance output remains independent from final useful god."
            if not climate_definitive_hits
            else f"Definitive climate wording detected: {climate_definitive_hits}",
        )
    )

    final_report_candidate_hits = _contains_forbidden_terms(
        _final_report_texts(report.final_report_v0),
        FORBIDDEN_FINAL_REPORT_CANDIDATE_FINAL_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_candidate_not_finalized",
            passed=not final_report_candidate_hits,
            message="final_report_v0 preserves candidate-versus-final boundaries."
            if not final_report_candidate_hits
            else f"Candidate-to-final overreach detected: {final_report_candidate_hits}",
        )
    )

    final_report_climate_hits = _contains_forbidden_terms(
        _final_report_texts(report.final_report_v0),
        FORBIDDEN_FINAL_REPORT_CLIMATE_FINAL_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_climate_not_final_useful_god",
            passed=not final_report_climate_hits,
            message="final_report_v0 does not treat climate candidates as final useful god."
            if not final_report_climate_hits
            else f"Climate-to-final overreach detected: {final_report_climate_hits}",
        )
    )

    annual_flow_verdict_hits = _contains_forbidden_terms(
        [
            *_annual_flow_texts(rules.annual_flow_v0),
            *_annual_flow_texts(report.annual_flow_summary),
        ],
        FORBIDDEN_ANNUAL_FLOW_VERDICT_TERMS,
        NEGATED_ANNUAL_FLOW_VERDICT_PATTERNS_V0,
    )
    checks.append(
        AuditCheck(
            name="annual_flow_not_fortune_verdict",
            passed=not annual_flow_verdict_hits,
            message="Annual flow output remains a structured ganzhi skeleton without verdict language."
            if not annual_flow_verdict_hits
            else f"Annual flow verdict wording detected: {annual_flow_verdict_hits}",
        )
    )

    annual_reading_absolute_hits = _contains_forbidden_terms(
        [
            *_annual_reading_texts(rules.annual_reading_v0),
            *_annual_reading_texts(report.annual_reading_summary),
        ],
        FORBIDDEN_ANNUAL_READING_ABSOLUTE_TERMS,
    )
    checks.append(
        AuditCheck(
            name="annual_reading_not_absolute_verdict",
            passed=not annual_reading_absolute_hits,
            message="annual_reading_v0 remains a controlled tendency layer without absolute event claims."
            if not annual_reading_absolute_hits
            else f"annual_reading_v0 absolute wording detected: {annual_reading_absolute_hits}",
        )
    )

    annual_reading_neutral_hits = _contains_forbidden_terms(
        [
            *_annual_reading_texts(rules.annual_reading_v0),
            *_annual_reading_texts(report.annual_reading_summary),
        ],
        FORBIDDEN_ANNUAL_READING_NEUTRAL_TERMS,
    )
    checks.append(
        AuditCheck(
            name="annual_reading_not_neutral_fallback",
            passed=not annual_reading_neutral_hits,
            message="annual_reading_v0 avoids vague neutral fallback wording when stronger evidence exists."
            if not annual_reading_neutral_hits
            else f"annual_reading_v0 neutral fallback wording detected: {annual_reading_neutral_hits}",
        )
    )

    career_absolute_hits = _contains_forbidden_terms(
        [
            *_career_reading_texts(rules.career_reading_v0),
            *_career_reading_texts(report.career_reading_summary),
            report.final_report_v0.career.text,
        ],
        FORBIDDEN_CAREER_ABSOLUTE_TERMS,
    )
    checks.append(
        AuditCheck(
            name="career_reading_not_absolute_verdict",
            passed=not career_absolute_hits,
            message="career_reading_v0 remains a controlled career tendency layer without event guarantees."
            if not career_absolute_hits
            else f"career_reading_v0 absolute wording detected: {career_absolute_hits}",
        )
    )

    wealth_absolute_hits = _contains_forbidden_terms(
        [
            *_wealth_reading_texts(rules.wealth_reading_v0),
            *_wealth_reading_texts(report.wealth_reading_summary),
            report.final_report_v0.wealth.text,
        ],
        FORBIDDEN_WEALTH_ABSOLUTE_TERMS,
    )
    checks.append(
        AuditCheck(
            name="wealth_reading_not_absolute_verdict",
            passed=not wealth_absolute_hits,
            message="wealth_reading_v0 remains a controlled wealth tendency layer without event guarantees."
            if not wealth_absolute_hits
            else f"wealth_reading_v0 absolute wording detected: {wealth_absolute_hits}",
        )
    )

    wealth_candidate_final_hits = _contains_forbidden_terms(
        [
            *_wealth_reading_texts(rules.wealth_reading_v0),
            *_wealth_reading_texts(report.wealth_reading_summary),
            report.final_report_v0.wealth.text,
        ],
        [
            *FORBIDDEN_FINAL_REPORT_CANDIDATE_FINAL_TERMS,
            *FORBIDDEN_FINAL_REPORT_CLIMATE_FINAL_TERMS,
        ],
    )
    checks.append(
        AuditCheck(
            name="wealth_reading_not_candidate_final_mixup",
            passed=not wealth_candidate_final_hits,
            message="wealth_reading_v0 and its report restatement keep candidate-versus-final boundaries."
            if not wealth_candidate_final_hits
            else f"wealth_reading_v0 candidate/final overreach detected: {wealth_candidate_final_hits}",
        )
    )

    wealth_shen_sha_hits = _contains_forbidden_terms(
        [report.final_report_v0.wealth.text],
        FORBIDDEN_WEALTH_SHEN_SHA_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_wealth_not_shen_sha_verdict",
            passed=not wealth_shen_sha_hits,
            message="final_report_v0 wealth text does not turn shen sha auxiliaries into a wealth verdict."
            if not wealth_shen_sha_hits
            else f"final_report_v0 wealth shen sha overreach detected: {wealth_shen_sha_hits}",
        )
    )

    wealth_annual_flow_hits = _contains_forbidden_terms(
        [report.final_report_v0.wealth.text],
        FORBIDDEN_WEALTH_ANNUAL_FLOW_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_wealth_not_annual_flow_verdict",
            passed=not wealth_annual_flow_hits,
            message="final_report_v0 wealth text does not turn annual flow skeleton into a wealth verdict."
            if not wealth_annual_flow_hits
            else f"final_report_v0 wealth annual flow overreach detected: {wealth_annual_flow_hits}",
        )
    )

    career_shen_sha_hits = _contains_forbidden_terms(
        [report.final_report_v0.career.text],
        FORBIDDEN_CAREER_SHEN_SHA_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_career_not_shen_sha_verdict",
            passed=not career_shen_sha_hits,
            message="final_report_v0 career text does not turn shen sha auxiliaries into a career verdict."
            if not career_shen_sha_hits
            else f"final_report_v0 career shen sha overreach detected: {career_shen_sha_hits}",
        )
    )

    career_annual_flow_hits = _contains_forbidden_terms(
        [report.final_report_v0.career.text],
        FORBIDDEN_CAREER_ANNUAL_FLOW_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_career_not_annual_flow_verdict",
            passed=not career_annual_flow_hits,
            message="final_report_v0 career text does not turn annual flow skeleton into a career verdict."
            if not career_annual_flow_hits
            else f"final_report_v0 career annual flow overreach detected: {career_annual_flow_hits}",
        )
    )

    relationship_absolute_hits = _contains_forbidden_terms(
        [
            *_relationship_reading_texts(rules.relationship_reading_v0),
            *_relationship_reading_texts(report.relationship_reading_summary),
            report.final_report_v0.relationship.text,
        ],
        FORBIDDEN_RELATIONSHIP_ABSOLUTE_TERMS,
    )
    checks.append(
        AuditCheck(
            name="relationship_reading_not_absolute_verdict",
            passed=not relationship_absolute_hits,
            message="relationship_reading_v0 remains a controlled relationship tendency layer without event guarantees."
            if not relationship_absolute_hits
            else f"relationship_reading_v0 absolute wording detected: {relationship_absolute_hits}",
        )
    )

    relationship_shen_sha_hits = _contains_forbidden_terms(
        [report.final_report_v0.relationship.text],
        FORBIDDEN_RELATIONSHIP_SHEN_SHA_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_relationship_not_shen_sha_verdict",
            passed=not relationship_shen_sha_hits,
            message="final_report_v0 relationship text does not turn shen sha auxiliaries into a relationship verdict."
            if not relationship_shen_sha_hits
            else f"final_report_v0 relationship shen sha overreach detected: {relationship_shen_sha_hits}",
        )
    )

    relationship_annual_flow_hits = _contains_forbidden_terms(
        [report.final_report_v0.relationship.text],
        FORBIDDEN_RELATIONSHIP_ANNUAL_FLOW_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_relationship_not_annual_flow_verdict",
            passed=not relationship_annual_flow_hits,
            message="final_report_v0 relationship text does not turn annual flow skeleton into a relationship verdict."
            if not relationship_annual_flow_hits
            else f"final_report_v0 relationship annual flow overreach detected: {relationship_annual_flow_hits}",
        )
    )

    final_report_annual_flow_hits = _contains_forbidden_terms(
        _final_report_texts(report.final_report_v0),
        FORBIDDEN_ANNUAL_FLOW_VERDICT_TERMS,
        NEGATED_ANNUAL_FLOW_VERDICT_PATTERNS_V0,
    )
    checks.append(
        AuditCheck(
            name="final_report_annual_flow_not_fortune_verdict",
            passed=not final_report_annual_flow_hits,
            message="final_report_v0 does not turn annual flow skeleton into a verdict layer."
            if not final_report_annual_flow_hits
            else f"final_report_v0 annual flow overreach detected: {final_report_annual_flow_hits}",
        )
    )

    future_five_years_absolute_hits = _contains_forbidden_terms(
        _future_five_years_texts(report.final_report_v0),
        FORBIDDEN_ANNUAL_READING_ABSOLUTE_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_future_five_years_not_absolute_verdict",
            passed=not future_five_years_absolute_hits,
            message="final_report_v0 future_five_years remains a controlled reading without absolute event claims."
            if not future_five_years_absolute_hits
            else f"final_report_v0 future_five_years absolute wording detected: {future_five_years_absolute_hits}",
        )
    )

    future_five_years_neutral_hits = _contains_forbidden_terms(
        _future_five_years_texts(report.final_report_v0),
        FORBIDDEN_ANNUAL_READING_NEUTRAL_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_future_five_years_not_neutral_fallback",
            passed=not future_five_years_neutral_hits,
            message="final_report_v0 future_five_years avoids vague neutral fallback wording."
            if not future_five_years_neutral_hits
            else f"final_report_v0 future_five_years neutral fallback wording detected: {future_five_years_neutral_hits}",
        )
    )

    shen_sha_verdict_hits = _contains_forbidden_terms(
        [
            *_shen_sha_texts(rules.shen_sha_v0),
            *_shen_sha_texts(report.shen_sha_summary),
        ],
        FORBIDDEN_SHEN_SHA_VERDICT_TERMS,
    )
    checks.append(
        AuditCheck(
            name="shen_sha_not_fortune_verdict",
            passed=not shen_sha_verdict_hits,
            message="Shen sha output remains a structured hit list without fortune verdict language."
            if not shen_sha_verdict_hits
            else f"Shen sha verdict wording detected: {shen_sha_verdict_hits}",
        )
    )

    final_report_shen_sha_hits = _contains_forbidden_terms(
        _final_report_texts(report.final_report_v0),
        FORBIDDEN_SHEN_SHA_VERDICT_TERMS,
    )
    checks.append(
        AuditCheck(
            name="final_report_shen_sha_not_fortune_verdict",
            passed=not final_report_shen_sha_hits,
            message="final_report_v0 does not turn shen sha hits into fortune verdicts."
            if not final_report_shen_sha_hits
            else f"final_report_v0 shen sha overreach detected: {final_report_shen_sha_hits}",
        )
    )

    report_boundary_hits = _contains_forbidden_terms(
        [json.dumps(report.model_dump(), ensure_ascii=False)],
        FORBIDDEN_REPORT_BOUNDARY_TERMS,
    )
    checks.append(
        AuditCheck(
            name="report_boundary_terms_absent",
            passed=not report_boundary_hits,
            message="report.json does not contain obvious out-of-scope finalization terms."
            if not report_boundary_hits
            else f"Out-of-scope report terms detected: {report_boundary_hits}",
        )
    )

    luck_cycle_complete = _luck_cycle_complete(chart)
    checks.append(
        AuditCheck(
            name="luck_cycle_structure_complete",
            passed=luck_cycle_complete,
            message="luck_cycle contains basis, direction, start_age, and complete cycles."
            if luck_cycle_complete
            else "luck_cycle structure is incomplete or inconsistent.",
        )
    )

    try:
        input_payload = BaziInput.model_validate(chart.input_snapshot.model_dump())
        recalculated_luck_cycle = calculate_luck_cycle(
            input_payload,
            chart.solar_datetime,
            chart.pillars,
        )
        luck_cycle_consistent = chart.luck_cycle == recalculated_luck_cycle
        luck_cycle_message = "luck_cycle is consistent with the configured basis."
        if not luck_cycle_consistent:
            luck_cycle_message = "luck_cycle conflicts with a recomputed deterministic result."
    except Exception as exc:  # noqa: BLE001
        luck_cycle_consistent = False
        luck_cycle_message = f"luck_cycle recomputation failed: {exc}"
    checks.append(
        AuditCheck(
            name="luck_cycle_consistent_with_basis",
            passed=luck_cycle_consistent,
            message=luck_cycle_message,
        )
    )

    expected_report = build_report(chart, rules)
    wealth_report_restates_rules_only = (
        report.wealth_reading_summary == rules.wealth_reading_v0
        and report.final_report_v0.wealth == expected_report.final_report_v0.wealth
        and rules.wealth_reading_v0.conclusion in report.final_report_v0.wealth.text
    )
    checks.append(
        AuditCheck(
            name="final_report_wealth_restates_rules_only",
            passed=wealth_report_restates_rules_only,
            message="final_report_v0 wealth section is a controlled restatement of wealth_reading_v0."
            if wealth_report_restates_rules_only
            else "final_report_v0 wealth section does not stay within wealth_reading_v0.",
        )
    )
    report_matches_scope = report == expected_report
    checks.append(
        AuditCheck(
            name="report_within_chart_rules_scope",
            passed=report_matches_scope,
            message="report.json stays within the scope defined by chart.json and rules.json."
            if report_matches_scope
            else "report.json contains content that does not match chart.json and rules.json.",
        )
    )

    recalculated_rules = build_rules_output(chart)
    rules_consistent_with_chart = rules == recalculated_rules
    checks.append(
        AuditCheck(
            name="rules_consistent_with_chart",
            passed=rules_consistent_with_chart,
            message="rules.json is consistent with chart.json."
            if rules_consistent_with_chart
            else "rules.json conflicts with recomputed deterministic rule output.",
        )
    )

    report_text = json.dumps(report.model_dump(), ensure_ascii=False)
    forbidden_hits = [term for term in FORBIDDEN_SCHOOL_TERMS if term in report_text]
    checks.append(
        AuditCheck(
            name="foreign_school_terms_absent",
            passed=not forbidden_hits,
            message="No foreign-school terms were found in report.json."
            if not forbidden_hits
            else f"Foreign-school terms detected: {forbidden_hits}",
        )
    )

    return AuditOutput(
        audit_version=AUDIT_VERSION,
        engine_version=chart.engine_version,
        rules_version=rules.rules_version,
        report_version=report.report_version,
        passed=all(check.passed for check in checks),
        checks=checks,
    )
