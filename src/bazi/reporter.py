from __future__ import annotations

from pathlib import Path

from . import REPORT_VERSION
from .models import (
    AnnualReadingOutput,
    AnnualFlowOutput,
    CareerReadingOutput,
    ChartOutput,
    ClimateBalanceOutput,
    EvidenceNote,
    FinalReportOutput,
    FinalUsefulGodSummary,
    FutureFiveYearsEntry,
    FutureFiveYearsOutput,
    PatternSystemOutput,
    RelationshipReadingOutput,
    ReportOutput,
    ReportSummary,
    RulesOutput,
    ShenShaOutput,
    StrengthSummary,
    TenGodsSummary,
    WealthReadingOutput,
)
from .rule_data import load_final_report_rules


def _append_unique(target: list[str], refs: list[str]) -> None:
    for ref in refs:
        if ref not in target:
            target.append(ref)


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


def _collect_relationship_reading_refs(relationship_reading: RelationshipReadingOutput) -> list[str]:
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


def _collect_candidate_refs(rules: RulesOutput) -> list[str]:
    refs: list[str] = []
    for item in rules.provisional_conclusions.favorable_elements_candidates:
        _append_unique(refs, item.evidence_refs)
    for item in rules.provisional_conclusions.unfavorable_elements_candidates:
        _append_unique(refs, item.evidence_refs)
    for note in rules.provisional_conclusions.notes:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_final_refs(rules: RulesOutput) -> list[str]:
    refs = list(rules.final_useful_god_v0.evidence_refs)
    for note in rules.final_useful_god_v0.reason_chain:
        _append_unique(refs, note.evidence_refs)
    for note in rules.final_useful_god_v0.blockers:
        _append_unique(refs, note.evidence_refs)
    return refs


def _collect_luck_refs(chart: ChartOutput) -> list[str]:
    refs: list[str] = []
    _append_unique(refs, chart.luck_cycle.evidence_refs)
    for cycle in chart.luck_cycle.cycles:
        _append_unique(refs, cycle.evidence_refs)
    return refs


def _format_joined_items(items: list[str]) -> str:
    return "、".join(items)


def _format_elements(elements: list[str], labels: dict[str, str]) -> str:
    return _format_joined_items([labels[element] for element in elements])


def _build_candidate_sentence(rules: RulesOutput, report_rules: dict[str, object]) -> str:
    candidate_rules = report_rules["candidate_texts"]
    element_labels = report_rules["element_labels"]
    favorable = [item.element for item in rules.provisional_conclusions.favorable_elements_candidates]
    unfavorable = [item.element for item in rules.provisional_conclusions.unfavorable_elements_candidates]

    if not favorable and not unfavorable:
        return candidate_rules["empty"]

    parts: list[str] = []
    if favorable:
        parts.append(
            candidate_rules["favorable"].format(
                elements=_format_elements(favorable, element_labels)
            )
        )
    if unfavorable:
        parts.append(
            candidate_rules["unfavorable"].format(
                elements=_format_elements(unfavorable, element_labels)
            )
        )
    return "".join(parts)


def _build_final_useful_god_text(rules: RulesOutput, report_rules: dict[str, object]) -> str:
    final_result = rules.final_useful_god_v0
    element_labels = report_rules["element_labels"]
    final_rules = report_rules["final_useful_god_texts"]

    if final_result.status == "determined" and final_result.primary_element is not None:
        secondary_clause = ""
        if final_result.secondary_elements:
            secondary_clause = f"，{_format_elements(final_result.secondary_elements, element_labels)}为次级辅助"
        return final_rules["determined"].format(
            primary_element=element_labels[final_result.primary_element],
            secondary_clause=secondary_clause,
        )

    return final_rules[final_result.status]


def _build_pattern_sentence(rules: RulesOutput, report_rules: dict[str, object]) -> str:
    pattern = rules.pattern_system_v1
    pattern_rules = report_rules["pattern_texts"]

    if pattern.status == "determined" and pattern.final_pattern is not None:
        return pattern_rules["determined"].format(pattern_name=pattern.final_pattern.pattern_name)
    if pattern.status == "candidate_only" and pattern.candidate_pattern is not None:
        return pattern_rules["candidate_only"].format(
            pattern_name=pattern.candidate_pattern.pattern_name
        )
    return pattern_rules["insufficient_for_determination"]


def _build_climate_sentence(rules: RulesOutput, report_rules: dict[str, object]) -> str:
    climate = rules.climate_balance_v0
    climate_rules = report_rules["climate_texts"]

    if climate.status in {"determined", "candidate_only"} and climate.candidate_adjustments:
        element_labels = report_rules["element_labels"]
        elements = _format_elements(
            [item.element for item in climate.candidate_adjustments],
            element_labels,
        )
        return climate_rules[climate.status].format(elements=elements)
    return climate_rules["insufficient_for_determination"]


def _build_shen_sha_sentence(rules: RulesOutput, report_rules: dict[str, object]) -> str:
    shen_sha = rules.shen_sha_v0
    shen_sha_rules = report_rules["shen_sha_texts"]
    if shen_sha.hits:
        return shen_sha_rules["hit"].format(
            hit_names=_format_joined_items([item.name for item in shen_sha.hits])
        )
    return shen_sha_rules["no_hit"]


def _build_annual_flow_sentence(rules: RulesOutput, report_rules: dict[str, object]) -> str:
    annual_flow = rules.annual_flow_v0
    annual_rules = report_rules["annual_flow_texts"]
    if (
        annual_flow.status == "determined"
        and annual_flow.window.start_year is not None
        and annual_flow.window.end_year is not None
    ):
        return annual_rules["determined"].format(
            start_year=annual_flow.window.start_year,
            end_year=annual_flow.window.end_year,
        )
    return annual_rules["insufficient_for_determination"]


def _format_year_list(years: list[int]) -> str:
    if not years:
        return "当前五年窗口内未单独列出"
    return "、".join(f"{year}年" for year in years)


def _highlight_dimension_years(
    annual_reading: AnnualReadingOutput,
    signal_field: str,
) -> list[int]:
    preferred_years = [
        item.year
        for item in annual_reading.entries
        if getattr(item, signal_field) == "favorable"
    ]
    if preferred_years:
        return preferred_years
    return [
        item.year
        for item in annual_reading.entries
        if getattr(item, signal_field) == "positive"
    ]


def _build_future_five_years(
    rules: RulesOutput,
    report_rules: dict[str, object],
) -> FutureFiveYearsOutput:
    future_rules = report_rules["future_five_years"]
    annual_reading = rules.annual_reading_v0

    entry_summaries: list[FutureFiveYearsEntry] = []
    overview_refs = list(annual_reading.evidence_refs)
    career_years = _highlight_dimension_years(annual_reading, "career_signal")
    wealth_years = _highlight_dimension_years(annual_reading, "wealth_signal")
    relationship_years = _highlight_dimension_years(annual_reading, "relationship_signal")
    mentor_years = _highlight_dimension_years(annual_reading, "mentor_signal")

    overview_parts = [future_rules["overview_prefix"]]
    if career_years:
        overview_parts.append(
            future_rules["career_years_template"].format(
                years=_format_year_list(career_years)
            )
        )
    if wealth_years:
        overview_parts.append(
            future_rules["wealth_years_template"].format(
                years=_format_year_list(wealth_years)
            )
        )
    if mentor_years:
        overview_parts.append(
            future_rules["mentor_years_template"].format(
                years=_format_year_list(mentor_years)
            )
        )
    if relationship_years:
        overview_parts.append(
            future_rules["relationship_years_template"].format(
                years=_format_year_list(relationship_years)
            )
        )
    if not career_years and not wealth_years and not mentor_years and not relationship_years:
        overview_parts.append(future_rules["fallback_template"])

    for item in annual_reading.entries:
        entry_summaries.append(
            FutureFiveYearsEntry(
                year=item.year,
                text=future_rules["entry_template"].format(
                    year=item.year,
                    ganzhi=item.ganzhi,
                    summary=item.summary,
                ),
                evidence_refs=list(item.evidence_refs),
            )
        )
        _append_unique(overview_refs, item.evidence_refs)

    _append_unique(overview_refs, ["E805", "E806", "E807"])
    return FutureFiveYearsOutput(
        overview=ReportSummary(
            text="".join(overview_parts),
            evidence_refs=overview_refs,
        ),
        entries=entry_summaries,
        evidence_refs=overview_refs,
    )


def _build_final_report(rules: RulesOutput) -> FinalReportOutput:
    report_rules = load_final_report_rules()
    strength_rules = report_rules["strength_texts"][rules.strength.label]
    section_prefixes = report_rules["section_prefixes"]

    candidate_sentence = _build_candidate_sentence(rules, report_rules)
    final_sentence = _build_final_useful_god_text(rules, report_rules)
    pattern_sentence = _build_pattern_sentence(rules, report_rules)
    climate_sentence = _build_climate_sentence(rules, report_rules)
    shen_sha_sentence = _build_shen_sha_sentence(rules, report_rules)
    annual_sentence = _build_annual_flow_sentence(rules, report_rules)

    summary_text = (
        f"{section_prefixes['summary']}{strength_rules['summary']}"
        f"{candidate_sentence}{final_sentence}{pattern_sentence}{climate_sentence}"
        f"{shen_sha_sentence}{annual_sentence}"
    )
    summary_refs = list(rules.strength.evidence_refs)
    _append_unique(summary_refs, _collect_candidate_refs(rules))
    _append_unique(summary_refs, _collect_final_refs(rules))
    _append_unique(summary_refs, _collect_pattern_refs(rules.pattern_system_v1))
    _append_unique(summary_refs, _collect_climate_refs(rules.climate_balance_v0))
    _append_unique(summary_refs, _collect_shen_sha_refs(rules.shen_sha_v0))
    _append_unique(summary_refs, _collect_annual_flow_refs(rules.annual_flow_v0))
    _append_unique(summary_refs, _collect_annual_reading_refs(rules.annual_reading_v0))
    _append_unique(summary_refs, ["E801", "E802", "E803"])

    career_text = (
        f"{section_prefixes['career']}{rules.career_reading_v0.conclusion}"
        f"{report_rules['career_limit_note']}"
    )
    career_refs = list(rules.strength.evidence_refs)
    _append_unique(career_refs, _collect_career_reading_refs(rules.career_reading_v0))
    _append_unique(career_refs, ["E802", "E803", "E804", "E810", "E811"])

    wealth_text = (
        f"{section_prefixes['wealth']}{rules.wealth_reading_v0.conclusion}"
        f"{report_rules.get('wealth_limit_note', '当前财运专项为受控版 v0，只基于既有结构化规则做判断，不展开具体金额、投资成败或事件性预测。')}"
    )
    wealth_refs = list(rules.strength.evidence_refs)
    _append_unique(wealth_refs, _collect_wealth_reading_refs(rules.wealth_reading_v0))
    _append_unique(wealth_refs, ["E802", "E803", "E804", "E812", "E813"])

    relationship_text = (
        f"{section_prefixes['relationship']}{rules.relationship_reading_v0.conclusion}"
        f"{report_rules['relationship_limit_note']}"
    )
    relationship_refs = list(rules.strength.evidence_refs)
    _append_unique(relationship_refs, _collect_relationship_reading_refs(rules.relationship_reading_v0))
    _append_unique(relationship_refs, ["E802", "E803", "E804", "E808", "E809"])

    future_five_years = _build_future_five_years(rules, report_rules)

    limitations = [
        EvidenceNote(
            text=item["text"],
            evidence_refs=list(item["evidence_refs"]),
        )
        for item in report_rules["limitations"]
    ]

    final_report_refs: list[str] = []
    _append_unique(final_report_refs, summary_refs)
    _append_unique(final_report_refs, career_refs)
    _append_unique(final_report_refs, wealth_refs)
    _append_unique(final_report_refs, relationship_refs)
    _append_unique(final_report_refs, future_five_years.evidence_refs)
    for note in limitations:
        _append_unique(final_report_refs, note.evidence_refs)

    return FinalReportOutput(
        method=report_rules["method"],
        summary=ReportSummary(text=summary_text, evidence_refs=summary_refs),
        career=ReportSummary(text=career_text, evidence_refs=career_refs),
        wealth=ReportSummary(text=wealth_text, evidence_refs=wealth_refs),
        relationship=ReportSummary(text=relationship_text, evidence_refs=relationship_refs),
        future_five_years=future_five_years,
        limitations=limitations,
        evidence_refs=final_report_refs,
    )


def build_report(chart: ChartOutput, rules: RulesOutput) -> ReportOutput:
    report_rules = load_final_report_rules()
    ten_god_refs: list[str] = []
    for item in rules.ten_gods.stems_visible:
        _append_unique(ten_god_refs, item.evidence_refs)
    for branch_item in rules.ten_gods.branches_hidden:
        for hidden_item in branch_item.hidden_stems:
            _append_unique(ten_god_refs, hidden_item.evidence_refs)

    pattern_refs = _collect_pattern_refs(rules.pattern_system_v1)
    climate_refs = _collect_climate_refs(rules.climate_balance_v0)
    annual_flow_refs = _collect_annual_flow_refs(rules.annual_flow_v0)
    annual_reading_refs = _collect_annual_reading_refs(rules.annual_reading_v0)
    career_reading_refs = _collect_career_reading_refs(rules.career_reading_v0)
    wealth_reading_refs = _collect_wealth_reading_refs(rules.wealth_reading_v0)
    relationship_reading_refs = _collect_relationship_reading_refs(rules.relationship_reading_v0)
    shen_sha_refs = _collect_shen_sha_refs(rules.shen_sha_v0)
    candidate_refs = _collect_candidate_refs(rules)
    final_refs = _collect_final_refs(rules)
    luck_refs = _collect_luck_refs(chart)

    summary_refs = list(ten_god_refs)
    _append_unique(summary_refs, rules.strength.evidence_refs)
    _append_unique(summary_refs, pattern_refs)
    _append_unique(summary_refs, climate_refs)
    _append_unique(summary_refs, annual_flow_refs)
    _append_unique(summary_refs, annual_reading_refs)
    _append_unique(summary_refs, career_reading_refs)
    _append_unique(summary_refs, wealth_reading_refs)
    _append_unique(summary_refs, relationship_reading_refs)
    _append_unique(summary_refs, shen_sha_refs)
    _append_unique(summary_refs, candidate_refs)
    _append_unique(summary_refs, final_refs)
    _append_unique(summary_refs, luck_refs)

    caveats = list(rules.provisional_conclusions.notes)
    for blocker in rules.final_useful_god_v0.blockers:
        if blocker not in caveats:
            caveats.append(blocker)

    final_report_v0 = _build_final_report(rules)

    return ReportOutput(
        report_version=REPORT_VERSION,
        engine_version=chart.engine_version,
        rules_version=rules.rules_version,
        status="ok",
        summary=ReportSummary(
            text=rules.summary,
            evidence_refs=summary_refs,
        ),
        ten_gods_summary=TenGodsSummary(
            day_master=rules.day_master,
            stems_visible=rules.ten_gods.stems_visible,
            branches_hidden=rules.ten_gods.branches_hidden,
            evidence_refs=ten_god_refs,
        ),
        strength_summary=StrengthSummary(
            score=rules.strength.score,
            label=rules.strength.label,
            summary=rules.strength.summary,
            evidence_refs=rules.strength.evidence_refs,
        ),
        pattern_system_summary=rules.pattern_system_v1,
        climate_balance_summary=rules.climate_balance_v0,
        annual_flow_summary=rules.annual_flow_v0,
        annual_reading_summary=rules.annual_reading_v0,
        career_reading_summary=rules.career_reading_v0,
        wealth_reading_summary=rules.wealth_reading_v0,
        relationship_reading_summary=rules.relationship_reading_v0,
        shen_sha_summary=rules.shen_sha_v0,
        candidate_elements_summary=rules.provisional_conclusions,
        final_useful_god_summary=FinalUsefulGodSummary(
            status=rules.final_useful_god_v0.status,
            confidence=rules.final_useful_god_v0.confidence,
            primary_element=rules.final_useful_god_v0.primary_element,
            secondary_elements=rules.final_useful_god_v0.secondary_elements,
            text=_build_final_useful_god_text(rules, report_rules),
            evidence_refs=final_refs,
        ),
        final_report_v0=final_report_v0,
        luck_cycle_summary=chart.luck_cycle,
        caveats=caveats,
    )


def _gender_label(gender: str) -> str:
    return {
        "male": "男",
        "female": "女",
        "other": "其他",
    }.get(gender, gender)


def _calendar_label(calendar_type: str) -> str:
    return {
        "solar": "公历",
        "lunar": "农历",
    }.get(calendar_type, calendar_type)


def _school_label(school: str) -> str:
    return {
        "bazi_ziping_v1": "子平法（bazi_ziping_v1）",
    }.get(school, school)


def _true_solar_time_label(enabled: bool) -> str:
    return "开启" if enabled else "关闭"


def _luck_cycle_preview_lines(chart: ChartOutput) -> list[str]:
    preview_cycles = chart.luck_cycle.cycles[:3]
    if not preview_cycles:
        return ["- 当前未生成可展示的大运骨架。"]

    cycle_text = "；".join(
        (
            f"{cycle.ganzhi}（{cycle.start_age:.1f}-{cycle.end_age:.1f}岁，"
            f"{cycle.start_year}-{cycle.end_year}）"
        )
        for cycle in preview_cycles
    )
    direction_label = "顺行" if chart.luck_cycle.direction == "forward" else "逆行"
    return [
        f"- 方向：{direction_label}",
        f"- 起运年龄：{chart.luck_cycle.start_age:.1f}岁",
        f"- 起运时间：{chart.luck_cycle.start_datetime}",
        f"- 前三步大运：{cycle_text}",
    ]


def export_final_markdown(
    chart: ChartOutput,
    report: ReportOutput,
    output_path: Path,
) -> None:
    input_snapshot = chart.input_snapshot
    final_report = report.final_report_v0

    lines = [
        "# 八字分析报告",
        "",
        "## 基本信息",
        f"- 出生日期：{input_snapshot.birth_date}",
        f"- 出生时间：{input_snapshot.birth_time}",
        f"- 出生地：{input_snapshot.birth_place}",
        f"- 性别：{_gender_label(input_snapshot.gender)}",
        (
            f"- 排盘方式：{_school_label(input_snapshot.school)} / "
            f"{_calendar_label(input_snapshot.calendar_type)} / "
            f"{input_snapshot.timezone} / "
            f"真太阳时{_true_solar_time_label(input_snapshot.true_solar_time)}"
        ),
        (
            f"- 四柱：年柱{chart.pillars.year.ganzhi}，"
            f"月柱{chart.pillars.month.ganzhi}，"
            f"日柱{chart.pillars.day.ganzhi}，"
            f"时柱{chart.pillars.hour.ganzhi}"
        ),
        "",
        "## 核心结论",
        f"- 总结：{final_report.summary.text}",
        f"- 最终用神摘要：{report.final_useful_god_summary.text}",
        "",
        "## 事业",
        final_report.career.text,
        "",
        "## 财运",
        final_report.wealth.text,
        "",
        "## 婚恋",
        final_report.relationship.text,
        "",
        "## 未来五年阅读",
        final_report.future_five_years.overview.text,
        "",
        *[f"- {item.text}" for item in final_report.future_five_years.entries],
        "",
        "## 大运摘要",
        *_luck_cycle_preview_lines(chart),
        "",
        "## 当前系统边界说明",
    ]

    for item in final_report.limitations:
        lines.append(f"- {item.text}")

    lines.extend(
        [
            "",
            "## 证据说明",
            "本报告由本地规则系统根据 chart.json 与 rules.json 受控转述生成。",
            "详细证据请回看 report.json 与 rules.json 中对应字段的 evidence_refs。",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
