from __future__ import annotations

from . import RULES_VERSION
from .models import (
    CareerReadingOutput,
    AnnualFlowEntry,
    AnnualFlowOutput,
    AnnualFlowWindow,
    AnnualReadingEntry,
    AnnualReadingOutput,
    AnnualReadingWindow,
    CandidateElement,
    ChartOutput,
    ClimateAdjustment,
    ClimateBalanceOutput,
    ClimateSeasonContext,
    EvidenceNote,
    FinalUsefulGodOutput,
    PatternConclusion,
    PatternSystemOutput,
    ProvisionalConclusions,
    RelationshipReadingOutput,
    RulesOutput,
    ShenShaBasis,
    ShenShaHit,
    ShenShaMatchedPillarRef,
    ShenShaOutput,
    StrengthOutput,
    TenGodsOutput,
    WealthReadingOutput,
)
from .rule_data import (
    load_annual_flow_rules,
    load_annual_reading_rules,
    load_candidate_rules,
    load_career_reading_rules,
    load_climate_rules,
    load_pattern_rules,
    load_relationship_reading_rules,
    load_shen_sha_rules,
    load_strength_rules,
    load_wealth_reading_rules,
)
from .strength import judge_strength
from .ten_gods import calculate_ten_gods, get_stem_element, relation_to_element
from .useful_god import build_final_useful_god


def _month_relation(day_master: str, month_branch: str) -> str:
    rules = load_strength_rules()
    month_element = rules["month_branch_elements"][month_branch]
    day_element = get_stem_element(day_master)
    if day_element == month_element:
        return "same_element"
    for relation in (
        "produced_by_day_master",
        "controlled_by_day_master",
        "produces_day_master",
        "controls_day_master",
    ):
        if relation_to_element(day_master, relation) == month_element:
            return relation
    raise ValueError(f"Unable to resolve month relation for {day_master=} {month_branch=}.")


def _element_scores(chart: ChartOutput, ten_gods: TenGodsOutput) -> dict[str, int]:
    rules = load_candidate_rules()
    scores: dict[str, int] = {element: 0 for element in rules["element_labels"]}
    visible_weight = int(rules["weights"]["visible_stem"])
    hidden_weight = int(rules["weights"]["hidden_stem"])

    for stem in (
        chart.pillars.year.stem,
        chart.pillars.month.stem,
        chart.pillars.day.stem,
        chart.pillars.hour.stem,
    ):
        scores[get_stem_element(stem)] += visible_weight

    for branch_item in ten_gods.branches_hidden:
        for hidden_item in branch_item.hidden_stems:
            scores[get_stem_element(hidden_item.stem)] += hidden_weight

    return scores


def _climate_element_scores(chart: ChartOutput, ten_gods: TenGodsOutput) -> dict[str, int]:
    rules = load_climate_rules()
    scores: dict[str, int] = {element: 0 for element in rules["element_labels"]}
    visible_weight = int(rules["weights"]["visible_stem"])
    hidden_weight = int(rules["weights"]["hidden_stem"])

    for stem in (
        chart.pillars.year.stem,
        chart.pillars.month.stem,
        chart.pillars.day.stem,
        chart.pillars.hour.stem,
    ):
        scores[get_stem_element(stem)] += visible_weight

    for branch_item in ten_gods.branches_hidden:
        for hidden_item in branch_item.hidden_stems:
            scores[get_stem_element(hidden_item.stem)] += hidden_weight

    return scores


def _append_reason(base: str, extra: str) -> str:
    if not extra:
        return base
    return f"{base} {extra}"


def _append_unique(target: list[str], refs: list[str]) -> None:
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


def _collect_final_refs(final_output: FinalUsefulGodOutput) -> list[str]:
    refs = list(final_output.evidence_refs)
    for item in final_output.reason_chain:
        _append_unique(refs, item.evidence_refs)
    for item in final_output.blockers:
        _append_unique(refs, item.evidence_refs)
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


def _shift_cycle_value(sequence: list[str], start_value: str, offset: int) -> str:
    if start_value not in sequence:
        raise ValueError(f"Unsupported cycle anchor value: {start_value}")
    start_index = sequence.index(start_value)
    return sequence[(start_index + offset) % len(sequence)]


def _build_candidates(
    *,
    label: str,
    is_favorable: bool,
    day_master: str,
    summary_text: str,
    month_relation: str,
    element_scores: dict[str, int],
) -> list[CandidateElement]:
    rules = load_candidate_rules()
    label_rules = rules["labels"][label]
    templates_key = "favorable_templates" if is_favorable else "unfavorable_templates"
    relations_key = "favorable_relations" if is_favorable else "unfavorable_relations"
    templates = label_rules[templates_key]
    relations = label_rules[relations_key]
    max_candidates = int(label_rules["max_candidates"])
    overrepresented_score = int(rules["thresholds"]["overrepresented_score"])
    underrepresented_score = int(rules["thresholds"]["underrepresented_score"])
    element_labels = rules["element_labels"]
    fragments = rules["reason_fragments"]

    candidates: list[CandidateElement] = []
    month_supports = month_relation in {"same_element", "produces_day_master"}
    month_weakens = month_relation in {
        "produced_by_day_master",
        "controlled_by_day_master",
        "controls_day_master",
    }

    for relation in relations:
        if len(candidates) >= max_candidates:
            break

        element = relation_to_element(day_master, relation)
        element_score = element_scores[element]
        if is_favorable and element_score >= overrepresented_score:
            continue

        reason = templates[relation].format(
            summary=summary_text,
            element_zh=element_labels[element],
        )
        refs = list(label_rules["evidence_refs"])

        if label == "strong" and month_supports and is_favorable:
            reason = _append_reason(reason, fragments["month_supports_day_master"])
            if "E205" not in refs:
                refs.append("E205")
        if label == "weak" and month_weakens and is_favorable:
            reason = _append_reason(reason, fragments["month_weakens_day_master"])
            if "E205" not in refs:
                refs.append("E205")
        if is_favorable and element_score <= underrepresented_score:
            reason = _append_reason(
                reason,
                fragments["element_underrepresented"].format(
                    element_zh=element_labels[element]
                ),
            )
            if "E206" not in refs:
                refs.append("E206")
        if not is_favorable and element_score >= overrepresented_score:
            reason = _append_reason(
                reason,
                fragments["element_overrepresented"].format(
                    element_zh=element_labels[element]
                ),
            )
            if "E206" not in refs:
                refs.append("E206")

        candidates.append(
            CandidateElement(
                element=element,
                reason=reason,
                evidence_refs=refs,
            )
        )

    return candidates


def _build_provisional_conclusions(
    chart: ChartOutput,
    strength: StrengthOutput,
    ten_gods: TenGodsOutput,
) -> ProvisionalConclusions:
    rules = load_candidate_rules()
    method = rules["method"]
    fragments = rules["reason_fragments"]
    month_relation = _month_relation(chart.day_master, chart.pillars.month.branch)
    element_scores = _element_scores(chart, ten_gods)

    if strength.label == "balanced":
        notes = [
            EvidenceNote(
                text=fragments["balanced_note"],
                evidence_refs=["E201", "E204"],
            ),
            EvidenceNote(
                text=fragments["candidate_only_note"],
                evidence_refs=["E201", "E107"],
            ),
        ]
        return ProvisionalConclusions(
            favorable_elements_candidates=[],
            unfavorable_elements_candidates=[],
            method=method,
            notes=notes,
        )

    favorable = _build_candidates(
        label=strength.label,
        is_favorable=True,
        day_master=chart.day_master,
        summary_text=strength.summary,
        month_relation=month_relation,
        element_scores=element_scores,
    )
    unfavorable = _build_candidates(
        label=strength.label,
        is_favorable=False,
        day_master=chart.day_master,
        summary_text=strength.summary,
        month_relation=month_relation,
        element_scores=element_scores,
    )

    notes = [
        EvidenceNote(
            text=fragments["candidate_only_note"],
            evidence_refs=["E201", "E107"],
        )
    ]
    if not favorable and not unfavorable:
        notes.append(
            EvidenceNote(
                text="当前结构下候选证据不足，暂保守留空。",
                evidence_refs=["E201", "E107"],
            )
        )

    return ProvisionalConclusions(
        favorable_elements_candidates=favorable,
        unfavorable_elements_candidates=unfavorable,
        method=method,
        notes=notes,
    )


def _build_pattern_system(ten_gods: TenGodsOutput) -> PatternSystemOutput:
    rules = load_pattern_rules()
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E405"],
        )
    ]

    month_branch = next(
        (item for item in ten_gods.branches_hidden if item.pillar == "month"),
        None,
    )
    if month_branch is None or not month_branch.hidden_stems:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return PatternSystemOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            candidate_pattern=None,
            final_pattern=None,
            notes=notes,
            evidence_refs=evidence_refs,
        )

    month_main_qi = month_branch.hidden_stems[0]
    mapping = rules["pattern_map"].get(month_main_qi.god)
    if not isinstance(mapping, dict):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return PatternSystemOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            candidate_pattern=None,
            final_pattern=None,
            notes=notes,
            evidence_refs=evidence_refs,
        )

    visible_support = [
        item
        for item in ten_gods.stems_visible
        if not item.is_day_master and item.god == month_main_qi.god
    ]
    candidate_refs = list(month_main_qi.evidence_refs)
    _append_unique(candidate_refs, ["E401", "E402"])

    if visible_support:
        for item in visible_support:
            _append_unique(candidate_refs, item.evidence_refs)
        _append_unique(candidate_refs, ["E403"])
        transparency = "visible"
        status = "determined"
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["determined"].format(
                    god=month_main_qi.god,
                    pattern_name=mapping["pattern_name"],
                ),
                evidence_refs=["E403"],
            )
        )
    else:
        _append_unique(candidate_refs, ["E404"])
        transparency = "hidden_only"
        status = "candidate_only"
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["candidate_only"].format(
                    god=month_main_qi.god,
                    pattern_name=mapping["pattern_name"],
                ),
                evidence_refs=["E404"],
            )
        )

    candidate_pattern = PatternConclusion(
        pattern_key=mapping["pattern_key"],
        pattern_name=mapping["pattern_name"],
        source_stem=month_main_qi.stem,
        source_god=month_main_qi.god,
        transparency=transparency,
        evidence_refs=candidate_refs,
    )
    final_pattern = (
        candidate_pattern.model_copy(deep=True)
        if status == "determined"
        else None
    )

    evidence_refs = list(candidate_refs)
    for note in notes:
        _append_unique(evidence_refs, note.evidence_refs)

    return PatternSystemOutput(
        method=rules["method"],
        status=status,
        candidate_pattern=candidate_pattern,
        final_pattern=final_pattern,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _detect_climate_tendencies(
    bias_scores: dict[str, int],
    thresholds: dict[str, int],
) -> list[str]:
    detected: list[str] = []

    if (
        bias_scores["cold"] >= thresholds["cold"]
        and bias_scores["cold"] - bias_scores["hot"] >= thresholds["min_gap"]
    ):
        detected.append("cold")
    elif (
        bias_scores["hot"] >= thresholds["hot"]
        and bias_scores["hot"] - bias_scores["cold"] >= thresholds["min_gap"]
    ):
        detected.append("hot")

    if (
        bias_scores["dry"] >= thresholds["dry"]
        and bias_scores["dry"] - bias_scores["damp"] >= thresholds["min_gap"]
    ):
        detected.append("dry")
    elif (
        bias_scores["damp"] >= thresholds["damp"]
        and bias_scores["damp"] - bias_scores["dry"] >= thresholds["min_gap"]
    ):
        detected.append("damp")

    return detected


def _build_climate_balance(chart: ChartOutput, ten_gods: TenGodsOutput) -> ClimateBalanceOutput:
    rules = load_climate_rules()
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E507"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["candidate_boundary_note"],
            evidence_refs=["E506"],
        ),
    ]

    season_config = rules["seasons"].get(chart.pillars.month.branch)
    if not isinstance(season_config, dict):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E505", "E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return ClimateBalanceOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            season_context=None,
            candidate_adjustments=[],
            notes=notes,
            evidence_refs=evidence_refs,
        )

    element_scores = _climate_element_scores(chart, ten_gods)
    bias_scores = {
        tendency: sum(element_scores[element] for element in elements)
        for tendency, elements in rules["bias_groups"].items()
    }
    thresholds = {key: int(value) for key, value in rules["thresholds"].items()}
    detected_tendencies = _detect_climate_tendencies(bias_scores, thresholds)

    season_context_refs = ["E501"]
    if detected_tendencies:
        _append_unique(season_context_refs, ["E503"])

    season_context = ClimateSeasonContext(
        month_branch=chart.pillars.month.branch,
        season=season_config["season"],
        season_name=season_config["season_name"],
        baseline_tendencies=season_config["baseline_tendencies"],
        detected_tendencies=detected_tendencies,
        evidence_refs=season_context_refs,
    )

    tendency_labels = rules["tendency_labels"]
    direction_labels = rules["direction_labels"]
    element_labels = rules["element_labels"]
    baseline_text = "、".join(
        tendency_labels[item] for item in season_config["baseline_tendencies"]
    )

    supported_adjustments = 0
    candidate_adjustments: list[ClimateAdjustment] = []
    for item in season_config["default_adjustments"]:
        direction = item["direction"]
        element = item["element"]
        reason = rules["reason_texts"]["adjustment"].format(
            month_branch=chart.pillars.month.branch,
            season_name=season_config["season_name"],
            tendencies=baseline_text,
            element_name=element_labels[element],
            direction_name=direction_labels[direction],
        )
        adjustment_refs = ["E501", "E502"]
        supported = any(
            tendency in detected_tendencies
            for tendency in rules["support_map"][direction]
        )
        if supported:
            supported_adjustments += 1
            reason = _append_reason(
                reason,
                rules["reason_texts"]["bias_support"].format(
                    direction_name=direction_labels[direction]
                ),
            )
            _append_unique(adjustment_refs, ["E503"])

        candidate_adjustments.append(
            ClimateAdjustment(
                element=element,
                direction=direction,
                priority=int(item["priority"]),
                reason=reason,
                evidence_refs=adjustment_refs,
            )
        )

    if not candidate_adjustments:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E505", "E107"],
            )
        )
        evidence_refs = list(season_context.evidence_refs)
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return ClimateBalanceOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            season_context=season_context,
            candidate_adjustments=[],
            notes=notes,
            evidence_refs=evidence_refs,
        )

    if (
        detected_tendencies
        and supported_adjustments >= thresholds["determined_min_supported_adjustments"]
    ):
        status = "determined"
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["determined"],
                evidence_refs=["E504"],
            )
        )
    else:
        status = "candidate_only"
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["candidate_only"],
                evidence_refs=["E505"],
            )
        )

    evidence_refs = list(season_context.evidence_refs)
    for item in candidate_adjustments:
        _append_unique(evidence_refs, item.evidence_refs)
    for note in notes:
        _append_unique(evidence_refs, note.evidence_refs)

    return ClimateBalanceOutput(
        method=rules["method"],
        status=status,
        season_context=season_context,
        candidate_adjustments=candidate_adjustments,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _build_annual_flow(chart: ChartOutput) -> AnnualFlowOutput:
    rules = load_annual_flow_rules()
    preview_year_count = int(rules["preview_year_count"])
    window = AnnualFlowWindow(
        start_year=None,
        end_year=None,
        preview_year_count=preview_year_count,
        start_year_source=rules["start_year_source"],
        sequencing_basis=rules["sequencing_basis"],
    )
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E704"],
        )
    ]

    if not chart.luck_cycle.cycles:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return AnnualFlowOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            window=window,
            entries=[],
            notes=notes,
            evidence_refs=evidence_refs,
        )

    try:
        birth_year = int(chart.solar_datetime[:4])
        start_year = int(chart.luck_cycle.cycles[0].start_year)
        end_year = start_year + preview_year_count - 1
        window = AnnualFlowWindow(
            start_year=start_year,
            end_year=end_year,
            preview_year_count=preview_year_count,
            start_year_source=rules["start_year_source"],
            sequencing_basis=rules["sequencing_basis"],
        )
        stem_cycle = list(rules["heavenly_stems"])
        branch_cycle = list(rules["earthly_branches"])
        entries = [
            AnnualFlowEntry(
                year=year,
                ganzhi=(
                    f"{_shift_cycle_value(stem_cycle, chart.pillars.year.stem, year - birth_year)}"
                    f"{_shift_cycle_value(branch_cycle, chart.pillars.year.branch, year - birth_year)}"
                ),
                relative_index=relative_index,
                evidence_refs=["E701", "E702"],
            )
            for relative_index, year in enumerate(range(start_year, end_year + 1))
        ]
    except (TypeError, ValueError):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return AnnualFlowOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            window=window,
            entries=[],
            notes=notes,
            evidence_refs=evidence_refs,
        )

    notes.append(
        EvidenceNote(
            text=rules["reason_texts"]["determined"],
            evidence_refs=["E703"],
        )
    )
    evidence_refs: list[str] = []
    for entry in entries:
        _append_unique(evidence_refs, entry.evidence_refs)
    for note in notes:
        _append_unique(evidence_refs, note.evidence_refs)

    return AnnualFlowOutput(
        method=rules["method"],
        status="determined",
        window=window,
        entries=entries,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _resolve_year_ganzhi(chart: ChartOutput, year: int) -> str:
    rules = load_annual_flow_rules()
    birth_year = int(chart.solar_datetime[:4])
    stem_cycle = list(rules["heavenly_stems"])
    branch_cycle = list(rules["earthly_branches"])
    return (
        f"{_shift_cycle_value(stem_cycle, chart.pillars.year.stem, year - birth_year)}"
        f"{_shift_cycle_value(branch_cycle, chart.pillars.year.branch, year - birth_year)}"
    )


def _latest_luck_cycle_for_year(chart: ChartOutput, year: int):
    eligible_cycles = [cycle for cycle in chart.luck_cycle.cycles if cycle.start_year <= year]
    if not eligible_cycles:
        return None
    return eligible_cycles[-1]


ANNUAL_READING_SIGNAL_RANKS = {
    "challenging": -2,
    "cautious": -1,
    "mixed": 0,
    "positive": 1,
    "favorable": 2,
}


def _signal_from_score(
    score: int,
    favorable_min: int,
    positive_min: int,
    cautious_max: int,
    challenging_max: int,
) -> str:
    if score >= favorable_min:
        return "favorable"
    if score >= positive_min:
        return "positive"
    if score <= challenging_max:
        return "challenging"
    if score <= cautious_max:
        return "cautious"
    return "mixed"


def _year_signal_score(
    *,
    year_elements: tuple[str, str],
    final_primary: str | None,
    final_secondary: set[str],
    candidate_favorable: set[str],
    candidate_unfavorable: set[str],
    climate_candidates: set[str],
    active_cycle_elements: set[str],
    weights: dict[str, int],
    include_climate: bool,
) -> int:
    score = 0
    for element in year_elements:
        if final_primary is not None and element == final_primary:
            score += weights["final_primary"]
        elif element in final_secondary:
            score += weights["final_secondary"]
        elif element in candidate_favorable:
            score += weights["candidate_favorable"]

        if element in candidate_unfavorable:
            score += weights["candidate_unfavorable"]

    if include_climate and set(year_elements).intersection(climate_candidates):
        score += weights["climate_candidate"]

    supportive_context = set(candidate_favorable)
    if final_primary is not None:
        supportive_context.add(final_primary)
    supportive_context.update(final_secondary)
    if supportive_context.intersection(set(year_elements)).intersection(active_cycle_elements):
        score += weights["luck_cycle_supportive_alignment"]

    return score


def _mentor_signal(year_branch: str, mentor_targets: set[str], natal_mentor_hit: bool) -> str:
    if year_branch in mentor_targets:
        return "favorable"
    if natal_mentor_hit:
        return "positive"
    return "cautious"


def _overall_reading_signal(signals: list[str], thresholds: dict[str, int]) -> str:
    score = sum(ANNUAL_READING_SIGNAL_RANKS[signal] for signal in signals)
    return _signal_from_score(
        score,
        thresholds["overall_favorable_min"],
        thresholds["overall_positive_min"],
        thresholds["overall_cautious_max"],
        thresholds["overall_challenging_max"],
    )


def _build_annual_reading_summary(
    signal_texts: dict[str, dict[str, str]],
    *,
    overall_signal: str,
    career_signal: str,
    wealth_signal: str,
    relationship_signal: str,
    mentor_signal: str,
) -> str:
    return "".join(
        [
            signal_texts["overall"][overall_signal],
            signal_texts["career"][career_signal],
            signal_texts["wealth"][wealth_signal],
            signal_texts["relationship"][relationship_signal],
            signal_texts["mentor"][mentor_signal],
        ]
    )


def _build_annual_reading(
    chart: ChartOutput,
    provisional_conclusions: ProvisionalConclusions,
    final_useful_god_v0: FinalUsefulGodOutput,
    climate_balance_v0: ClimateBalanceOutput,
    shen_sha_v0: ShenShaOutput,
) -> AnnualReadingOutput:
    rules = load_annual_reading_rules()
    strength_rules = load_strength_rules()
    shen_sha_rules = load_shen_sha_rules()

    preview_year_count = int(rules["preview_year_count"])
    reference_year = int(rules["reference_year"])
    window = AnnualReadingWindow(
        start_year=None,
        end_year=None,
        preview_year_count=preview_year_count,
        reference_year=reference_year,
        reference_year_source=rules["reference_year_source"],
        sequencing_basis=rules["sequencing_basis"],
    )
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["fixed_reference_year"],
            evidence_refs=["E901"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E906"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["mentor_scope_note"],
            evidence_refs=["E904"],
        ),
    ]

    if not chart.luck_cycle.cycles:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return AnnualReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            window=window,
            entries=[],
            notes=notes,
            evidence_refs=evidence_refs,
        )

    try:
        start_year = reference_year
        end_year = reference_year + preview_year_count - 1
        window = AnnualReadingWindow(
            start_year=start_year,
            end_year=end_year,
            preview_year_count=preview_year_count,
            reference_year=reference_year,
            reference_year_source=rules["reference_year_source"],
            sequencing_basis=rules["sequencing_basis"],
        )

        weights = {key: int(value) for key, value in rules["score_weights"].items()}
        thresholds = {key: int(value) for key, value in rules["thresholds"].items()}
        branch_elements = strength_rules["month_branch_elements"]
        candidate_favorable = {
            item.element for item in provisional_conclusions.favorable_elements_candidates
        }
        candidate_unfavorable = {
            item.element for item in provisional_conclusions.unfavorable_elements_candidates
        }
        climate_candidates = {
            item.element for item in climate_balance_v0.candidate_adjustments
        }
        final_primary = final_useful_god_v0.primary_element
        final_secondary = set(final_useful_god_v0.secondary_elements)
        mentor_key = rules["mentor_rules"]["shen_sha_key"]
        mentor_rule = shen_sha_rules["rules"].get(mentor_key)
        if not isinstance(mentor_rule, dict):
            raise ValueError("annual_reading_v0 mentor rule is unavailable.")
        mentor_basis_value = _shen_sha_basis_value(chart, mentor_rule["basis"])
        mentor_targets = mentor_rule["mapping"].get(mentor_basis_value, [])
        if not isinstance(mentor_targets, list):
            mentor_targets = []
        mentor_targets_set = set(mentor_targets)
        natal_mentor_hit = any(hit.key == mentor_key for hit in shen_sha_v0.hits)
        signal_texts = rules["signal_texts"]

        entries: list[AnnualReadingEntry] = []
        for year in range(start_year, end_year + 1):
            ganzhi = _resolve_year_ganzhi(chart, year)
            year_stem = ganzhi[0]
            year_branch = ganzhi[1]
            year_elements = (
                get_stem_element(year_stem),
                branch_elements[year_branch],
            )
            active_cycle = _latest_luck_cycle_for_year(chart, year)
            active_cycle_elements: set[str] = set()
            active_cycle_refs: list[str] = []
            if active_cycle is not None:
                active_cycle_elements = {
                    get_stem_element(active_cycle.stem),
                    branch_elements[active_cycle.branch],
                }
                _append_unique(active_cycle_refs, active_cycle.evidence_refs)
                _append_unique(active_cycle_refs, chart.luck_cycle.evidence_refs)

            career_score = _year_signal_score(
                year_elements=year_elements,
                final_primary=final_primary,
                final_secondary=final_secondary,
                candidate_favorable=candidate_favorable,
                candidate_unfavorable=candidate_unfavorable,
                climate_candidates=climate_candidates,
                active_cycle_elements=active_cycle_elements,
                weights=weights,
                include_climate=True,
            )
            wealth_score = _year_signal_score(
                year_elements=year_elements,
                final_primary=final_primary,
                final_secondary=final_secondary,
                candidate_favorable=candidate_favorable,
                candidate_unfavorable=candidate_unfavorable,
                climate_candidates=climate_candidates,
                active_cycle_elements=active_cycle_elements,
                weights=weights,
                include_climate=True,
            )
            relationship_score = _year_signal_score(
                year_elements=year_elements,
                final_primary=final_primary,
                final_secondary=final_secondary,
                candidate_favorable=candidate_favorable,
                candidate_unfavorable=candidate_unfavorable,
                climate_candidates=set(),
                active_cycle_elements=active_cycle_elements,
                weights=weights,
                include_climate=False,
            )

            career_signal = _signal_from_score(
                career_score,
                thresholds["career_favorable_min"],
                thresholds["career_positive_min"],
                thresholds["career_cautious_max"],
                thresholds["career_challenging_max"],
            )
            wealth_signal = _signal_from_score(
                wealth_score,
                thresholds["wealth_favorable_min"],
                thresholds["wealth_positive_min"],
                thresholds["wealth_cautious_max"],
                thresholds["wealth_challenging_max"],
            )
            relationship_signal = _signal_from_score(
                relationship_score,
                thresholds["relationship_favorable_min"],
                thresholds["relationship_positive_min"],
                thresholds["relationship_cautious_max"],
                thresholds["relationship_challenging_max"],
            )
            mentor_signal = _mentor_signal(
                year_branch,
                mentor_targets_set,
                natal_mentor_hit,
            )
            overall_signal = _overall_reading_signal(
                [career_signal, wealth_signal, relationship_signal, mentor_signal],
                thresholds,
            )
            summary = _build_annual_reading_summary(
                signal_texts,
                overall_signal=overall_signal,
                career_signal=career_signal,
                wealth_signal=wealth_signal,
                relationship_signal=relationship_signal,
                mentor_signal=mentor_signal,
            )

            entry_refs = ["E701", "E702", "E903", "E905", "E908"]
            _append_unique(entry_refs, _collect_final_refs(final_useful_god_v0))
            _append_unique(entry_refs, _collect_provisional_refs(provisional_conclusions))
            _append_unique(entry_refs, _collect_climate_refs(climate_balance_v0))
            _append_unique(entry_refs, active_cycle_refs)
            if mentor_signal in {"favorable", "positive"}:
                _append_unique(entry_refs, _collect_shen_sha_refs(shen_sha_v0))
                _append_unique(entry_refs, ["E904"])
            if active_cycle_refs:
                _append_unique(entry_refs, ["E907"])

            entries.append(
                AnnualReadingEntry(
                    year=year,
                    ganzhi=ganzhi,
                    career_signal=career_signal,
                    wealth_signal=wealth_signal,
                    relationship_signal=relationship_signal,
                    mentor_signal=mentor_signal,
                    summary=summary,
                    evidence_refs=entry_refs,
                )
            )
    except (TypeError, ValueError):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return AnnualReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            window=window,
            entries=[],
            notes=notes,
            evidence_refs=evidence_refs,
        )

    notes.append(
        EvidenceNote(
            text=rules["reason_texts"]["determined"],
            evidence_refs=["E902", "E903", "E907", "E908"],
        )
    )
    evidence_refs: list[str] = []
    for entry in entries:
        _append_unique(evidence_refs, entry.evidence_refs)
    for note in notes:
        _append_unique(evidence_refs, note.evidence_refs)

    return AnnualReadingOutput(
        method=rules["method"],
        status="determined",
        window=window,
        entries=entries,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _relationship_gods_for_gender(gender: str, rules: dict[str, object]) -> set[str]:
    relationship_gods = rules["relationship_gods_by_gender"].get(gender)
    if not isinstance(relationship_gods, list) or not relationship_gods:
        raise ValueError("relationship_reading_v0 requires a supported gender mapping.")
    return set(relationship_gods)


def _career_god_snapshot(
    ten_gods: TenGodsOutput,
    category_gods: dict[str, set[str]],
) -> tuple[dict[str, dict[str, list[object]]], set[str], set[str], list[str]]:
    snapshot: dict[str, dict[str, list[object]]] = {
        key: {"visible": [], "hidden": []} for key in category_gods
    }
    elements: set[str] = set()
    day_branch_categories: set[str] = set()
    refs: list[str] = []

    for item in ten_gods.stems_visible:
        for category, gods in category_gods.items():
            if item.god in gods:
                snapshot[category]["visible"].append(item)
                elements.add(get_stem_element(item.stem))
                _append_unique(refs, item.evidence_refs)

    for branch_item in ten_gods.branches_hidden:
        for hidden_item in branch_item.hidden_stems:
            for category, gods in category_gods.items():
                if hidden_item.god in gods:
                    snapshot[category]["hidden"].append(hidden_item)
                    elements.add(get_stem_element(hidden_item.stem))
                    _append_unique(refs, hidden_item.evidence_refs)
                    if branch_item.pillar == "day":
                        day_branch_categories.add(category)

    return snapshot, elements, day_branch_categories, refs


def _career_growth_mode(
    current_phase: str,
    future_tendency: str,
    resource_support: str,
    rules: dict[str, object],
) -> str:
    growth_mode_rules = rules["growth_mode_rules"]
    active_breakthrough_phases = set(growth_mode_rules["active_breakthrough_phases"])
    leverage_support_resource_signals = set(
        growth_mode_rules["leverage_support_resource_signals"]
    )
    leverage_support_future_signals = set(
        growth_mode_rules["leverage_support_future_signals"]
    )

    if current_phase in active_breakthrough_phases and future_tendency in leverage_support_future_signals:
        return "active_breakthrough"
    if (
        resource_support in leverage_support_resource_signals
        and future_tendency in leverage_support_future_signals
    ):
        return "leverage_support"
    return "steady_build"


def _build_career_conclusion(
    signal_texts: dict[str, dict[str, str]],
    *,
    base_support: str,
    current_phase: str,
    growth_mode: str,
    future_tendency: str,
    resource_support: str,
) -> str:
    return "".join(
        [
            signal_texts["base_support"][base_support],
            signal_texts["current_phase"][current_phase],
            signal_texts["growth_mode"][growth_mode],
            signal_texts["future_tendency"][future_tendency],
            signal_texts["resource_support"][resource_support],
        ]
    )


def _build_career_reading(
    chart: ChartOutput,
    ten_gods: TenGodsOutput,
    strength: StrengthOutput,
    provisional_conclusions: ProvisionalConclusions,
    final_useful_god_v0: FinalUsefulGodOutput,
    pattern_system_v1: PatternSystemOutput,
    climate_balance_v0: ClimateBalanceOutput,
    annual_reading_v0: AnnualReadingOutput,
    shen_sha_v0: ShenShaOutput,
) -> CareerReadingOutput:
    rules = load_career_reading_rules()
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E1101", "E1102"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["shen_sha_auxiliary_note"],
            evidence_refs=["E1105"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["future_window_note"],
            evidence_refs=["E1104", "E1106"],
        ),
    ]

    if annual_reading_v0.status != "determined" or not annual_reading_v0.entries:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return CareerReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            base_support="cautious",
            current_phase="cautious",
            growth_mode="steady_build",
            future_tendency="cautious",
            resource_support="cautious",
            conclusion="不足以判断。",
            notes=notes,
            evidence_refs=evidence_refs,
        )

    try:
        category_gods = {
            key: set(value) for key, value in rules["career_support_gods"].items()
        }
        (
            snapshot,
            career_elements,
            day_branch_categories,
            career_star_refs,
        ) = _career_god_snapshot(ten_gods, category_gods)
        weights = {key: int(value) for key, value in rules["score_weights"].items()}
        thresholds = {key: int(value) for key, value in rules["thresholds"].items()}
        signal_texts = rules["signal_texts"]
        phase_mapping = rules["phase_mapping"]
        related_shen_sha_keys = set(rules["related_shen_sha_keys"])

        supportive_elements = {
            item.element for item in provisional_conclusions.favorable_elements_candidates
        }
        if final_useful_god_v0.primary_element is not None:
            supportive_elements.add(final_useful_god_v0.primary_element)
        supportive_elements.update(final_useful_god_v0.secondary_elements)
        unfavorable_elements = {
            item.element for item in provisional_conclusions.unfavorable_elements_candidates
        }

        base_support_score = (
            len(snapshot["core"]["visible"]) * weights["base_core_visible"]
            + len(snapshot["core"]["hidden"]) * weights["base_core_hidden"]
            + len(snapshot["resource"]["visible"]) * weights["base_resource_visible"]
            + len(snapshot["resource"]["hidden"]) * weights["base_resource_hidden"]
            + len(snapshot["output"]["visible"]) * weights["base_output_visible"]
            + len(snapshot["output"]["hidden"]) * weights["base_output_hidden"]
            + len(snapshot["wealth"]["visible"]) * weights["base_wealth_visible"]
            + len(snapshot["wealth"]["hidden"]) * weights["base_wealth_hidden"]
        )
        if day_branch_categories:
            base_support_score += weights["base_day_branch_bonus"]
        if career_elements.intersection(supportive_elements):
            base_support_score += weights["base_supportive_alignment"]
        if career_elements.intersection(unfavorable_elements):
            base_support_score += weights["base_unfavorable_alignment_penalty"]
        elif strength.label == "weak" and not career_elements.intersection(supportive_elements):
            base_support_score += weights["base_weak_unaligned_penalty"]

        pattern_god = None
        if pattern_system_v1.final_pattern is not None:
            pattern_god = pattern_system_v1.final_pattern.source_god
        elif pattern_system_v1.candidate_pattern is not None:
            pattern_god = pattern_system_v1.candidate_pattern.source_god
        if pattern_god is not None and any(
            pattern_god in gods for gods in category_gods.values()
        ):
            base_support_score += weights["base_pattern_bonus"]

        climate_elements = {
            item.element for item in climate_balance_v0.candidate_adjustments
        }
        if climate_elements.intersection(supportive_elements):
            base_support_score += weights["base_climate_support_bonus"]

        base_support = _signal_from_score(
            base_support_score,
            thresholds["base_support_favorable_min"],
            thresholds["base_support_positive_min"],
            thresholds["base_support_cautious_max"],
            thresholds["base_support_challenging_max"],
        )

        current_entry = annual_reading_v0.entries[0]
        current_phase = phase_mapping[current_entry.career_signal]

        resource_support_score = 0
        if snapshot["resource"]["visible"]:
            resource_support_score += weights["resource_visible_presence"]
        if snapshot["resource"]["hidden"]:
            resource_support_score += weights["resource_hidden_presence"]
        if snapshot["core"]["visible"]:
            resource_support_score += weights["resource_core_visible_presence"]
        if current_entry.mentor_signal == "favorable":
            resource_support_score += weights["resource_current_mentor_favorable"]
        elif current_entry.mentor_signal == "positive":
            resource_support_score += weights["resource_current_mentor_positive"]
        if current_entry.career_signal == "favorable":
            resource_support_score += weights["resource_current_career_favorable"]
        elif current_entry.career_signal == "positive":
            resource_support_score += weights["resource_current_career_positive"]
        elif current_entry.career_signal == "cautious":
            resource_support_score += weights["resource_current_career_cautious"]
        elif current_entry.career_signal == "challenging":
            resource_support_score += weights["resource_current_career_challenging"]

        shen_sha_hit_keys = {item.key for item in shen_sha_v0.hits}
        if "tianyi_guiren" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            resource_support_score += weights["resource_tianyi_auxiliary"]
        if "wenchang" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            resource_support_score += weights["resource_wenchang_auxiliary"]

        resource_support = _signal_from_score(
            resource_support_score,
            thresholds["resource_support_favorable_min"],
            thresholds["resource_support_positive_min"],
            thresholds["resource_support_cautious_max"],
            thresholds["resource_support_challenging_max"],
        )

        career_signals = [item.career_signal for item in annual_reading_v0.entries]
        future_score = sum(weights[f"future_{signal}_year"] for signal in career_signals)
        if base_support in {"favorable", "positive"}:
            future_score += weights["future_base_support_bonus"]

        future_tendency = _signal_from_score(
            future_score,
            thresholds["future_favorable_min"],
            thresholds["future_positive_min"],
            thresholds["future_cautious_max"],
            thresholds["future_challenging_max"],
        )
        growth_mode = _career_growth_mode(
            current_phase,
            future_tendency,
            resource_support,
            rules,
        )

        conclusion = _build_career_conclusion(
            signal_texts,
            base_support=base_support,
            current_phase=current_phase,
            growth_mode=growth_mode,
            future_tendency=future_tendency,
            resource_support=resource_support,
        )

        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["determined"],
                evidence_refs=["E1103", "E1104", "E1106", "E1107"],
            )
        )

        evidence_refs: list[str] = ["E1101", "E1102", "E1103", "E1104", "E1105", "E1106", "E1107"]
        _append_unique(evidence_refs, career_star_refs)
        _append_unique(evidence_refs, _collect_provisional_refs(provisional_conclusions))
        _append_unique(evidence_refs, _collect_final_refs(final_useful_god_v0))
        _append_unique(evidence_refs, pattern_system_v1.evidence_refs)
        _append_unique(evidence_refs, climate_balance_v0.evidence_refs)
        _append_unique(evidence_refs, _collect_shen_sha_refs(shen_sha_v0))
        _append_unique(evidence_refs, annual_reading_v0.evidence_refs)
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
    except (KeyError, TypeError, ValueError):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return CareerReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            base_support="cautious",
            current_phase="cautious",
            growth_mode="steady_build",
            future_tendency="cautious",
            resource_support="cautious",
            conclusion="不足以判断。",
            notes=notes,
            evidence_refs=evidence_refs,
        )

    return CareerReadingOutput(
        method=rules["method"],
        status="determined",
        base_support=base_support,
        current_phase=current_phase,
        growth_mode=growth_mode,
        future_tendency=future_tendency,
        resource_support=resource_support,
        conclusion=conclusion,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _wealth_mode(
    current_phase: str,
    future_tendency: str,
    resource_support: str,
    risk_control: str,
    rules: dict[str, object],
) -> str:
    mode_rules = rules["wealth_mode_rules"]
    leverage_growth_future_signals = set(mode_rules["leverage_growth_future_signals"])
    leverage_growth_resource_signals = set(
        mode_rules["leverage_growth_resource_signals"]
    )
    risk_control_levels = set(mode_rules["risk_control_levels"])
    steady_accumulation_phases = set(mode_rules["steady_accumulation_phases"])

    if (
        future_tendency in leverage_growth_future_signals
        and resource_support in leverage_growth_resource_signals
        and risk_control not in risk_control_levels
    ):
        return "leverage_growth"
    if current_phase in steady_accumulation_phases:
        return "steady_accumulation"
    if risk_control in risk_control_levels:
        return "risk_control"
    return "steady_accumulation"


def _build_wealth_conclusion(
    signal_texts: dict[str, dict[str, str]],
    *,
    base_support: str,
    current_phase: str,
    wealth_mode: str,
    future_tendency: str,
    resource_support: str,
    risk_control: str,
) -> str:
    return "".join(
        [
            signal_texts["base_support"][base_support],
            signal_texts["current_phase"][current_phase],
            signal_texts["wealth_mode"][wealth_mode],
            signal_texts["future_tendency"][future_tendency],
            signal_texts["resource_support"][resource_support],
            signal_texts["risk_control"][risk_control],
        ]
    )


def _build_wealth_reading(
    ten_gods: TenGodsOutput,
    strength: StrengthOutput,
    provisional_conclusions: ProvisionalConclusions,
    final_useful_god_v0: FinalUsefulGodOutput,
    pattern_system_v1: PatternSystemOutput,
    climate_balance_v0: ClimateBalanceOutput,
    annual_reading_v0: AnnualReadingOutput,
    shen_sha_v0: ShenShaOutput,
) -> WealthReadingOutput:
    rules = load_wealth_reading_rules()
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E1201", "E1202"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["shen_sha_auxiliary_note"],
            evidence_refs=["E1205"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["future_window_note"],
            evidence_refs=["E1204", "E1206"],
        ),
    ]

    if annual_reading_v0.status != "determined" or not annual_reading_v0.entries:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return WealthReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            base_support="cautious",
            current_phase="cautious",
            wealth_mode="steady_accumulation",
            future_tendency="cautious",
            resource_support="cautious",
            risk_control="tight_control",
            conclusion="不足以判断。",
            notes=notes,
            evidence_refs=evidence_refs,
        )

    try:
        category_gods = {
            key: set(value) for key, value in rules["wealth_support_gods"].items()
        }
        (
            snapshot,
            wealth_elements,
            day_branch_categories,
            wealth_star_refs,
        ) = _career_god_snapshot(ten_gods, category_gods)
        weights = {key: int(value) for key, value in rules["score_weights"].items()}
        thresholds = {key: int(value) for key, value in rules["thresholds"].items()}
        signal_texts = rules["signal_texts"]
        phase_mapping = rules["phase_mapping"]
        related_shen_sha_keys = set(rules["related_shen_sha_keys"])

        supportive_elements = {
            item.element for item in provisional_conclusions.favorable_elements_candidates
        }
        if final_useful_god_v0.primary_element is not None:
            supportive_elements.add(final_useful_god_v0.primary_element)
        supportive_elements.update(final_useful_god_v0.secondary_elements)
        unfavorable_elements = {
            item.element for item in provisional_conclusions.unfavorable_elements_candidates
        }

        base_support_score = (
            len(snapshot["wealth"]["visible"]) * weights["base_wealth_visible"]
            + len(snapshot["wealth"]["hidden"]) * weights["base_wealth_hidden"]
            + len(snapshot["output"]["visible"]) * weights["base_output_visible"]
            + len(snapshot["output"]["hidden"]) * weights["base_output_hidden"]
            + len(snapshot["resource"]["visible"]) * weights["base_resource_visible"]
            + len(snapshot["resource"]["hidden"]) * weights["base_resource_hidden"]
        )
        if day_branch_categories.intersection({"wealth", "output"}):
            base_support_score += weights["base_day_branch_bonus"]
        if wealth_elements.intersection(supportive_elements):
            base_support_score += weights["base_supportive_alignment"]
        if wealth_elements.intersection(unfavorable_elements):
            base_support_score += weights["base_unfavorable_alignment_penalty"]
        elif strength.label == "weak" and not wealth_elements.intersection(supportive_elements):
            base_support_score += weights["base_weak_unaligned_penalty"]

        pattern_god = None
        if pattern_system_v1.final_pattern is not None:
            pattern_god = pattern_system_v1.final_pattern.source_god
        elif pattern_system_v1.candidate_pattern is not None:
            pattern_god = pattern_system_v1.candidate_pattern.source_god
        if pattern_god is not None and any(
            pattern_god in gods for gods in category_gods.values()
        ):
            base_support_score += weights["base_pattern_bonus"]

        climate_elements = {
            item.element for item in climate_balance_v0.candidate_adjustments
        }
        if climate_elements.intersection(supportive_elements):
            base_support_score += weights["base_climate_support_bonus"]

        base_support = _signal_from_score(
            base_support_score,
            thresholds["base_support_favorable_min"],
            thresholds["base_support_positive_min"],
            thresholds["base_support_cautious_max"],
            thresholds["base_support_challenging_max"],
        )

        current_entry = annual_reading_v0.entries[0]
        current_phase = phase_mapping[current_entry.wealth_signal]

        resource_support_score = 0
        if snapshot["resource"]["visible"]:
            resource_support_score += weights["resource_visible_presence"]
        if snapshot["resource"]["hidden"]:
            resource_support_score += weights["resource_hidden_presence"]
        if snapshot["wealth"]["visible"]:
            resource_support_score += weights["resource_wealth_visible_presence"]
        if current_entry.mentor_signal == "favorable":
            resource_support_score += weights["resource_current_mentor_favorable"]
        elif current_entry.mentor_signal == "positive":
            resource_support_score += weights["resource_current_mentor_positive"]
        if current_entry.wealth_signal == "favorable":
            resource_support_score += weights["resource_current_wealth_favorable"]
        elif current_entry.wealth_signal == "positive":
            resource_support_score += weights["resource_current_wealth_positive"]
        elif current_entry.wealth_signal == "cautious":
            resource_support_score += weights["resource_current_wealth_cautious"]
        elif current_entry.wealth_signal == "challenging":
            resource_support_score += weights["resource_current_wealth_challenging"]

        shen_sha_hit_keys = {item.key for item in shen_sha_v0.hits}
        if "tianyi_guiren" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            resource_support_score += weights["resource_tianyi_auxiliary"]
        if "wenchang" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            resource_support_score += weights["resource_wenchang_auxiliary"]
        if "yima" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            resource_support_score += weights["resource_yima_auxiliary"]

        resource_support = _signal_from_score(
            resource_support_score,
            thresholds["resource_support_favorable_min"],
            thresholds["resource_support_positive_min"],
            thresholds["resource_support_cautious_max"],
            thresholds["resource_support_challenging_max"],
        )

        wealth_signals = [item.wealth_signal for item in annual_reading_v0.entries]
        future_score = sum(weights[f"future_{signal}_year"] for signal in wealth_signals)
        if base_support in {"favorable", "positive"}:
            future_score += weights["future_base_support_bonus"]
        future_tendency = _signal_from_score(
            future_score,
            thresholds["future_favorable_min"],
            thresholds["future_positive_min"],
            thresholds["future_cautious_max"],
            thresholds["future_challenging_max"],
        )

        risk_control_score = 0
        if strength.label == "weak":
            risk_control_score += weights["risk_strength_weak"]
        elif strength.label == "balanced":
            risk_control_score += weights["risk_strength_balanced"]
        if current_entry.wealth_signal == "cautious":
            risk_control_score += weights["risk_current_wealth_cautious"]
        elif current_entry.wealth_signal == "challenging":
            risk_control_score += weights["risk_current_wealth_challenging"]
        elif current_entry.wealth_signal == "positive":
            risk_control_score += weights["risk_current_wealth_positive"]
        elif current_entry.wealth_signal == "favorable":
            risk_control_score += weights["risk_current_wealth_favorable"]
        if wealth_elements.intersection(unfavorable_elements):
            risk_control_score += weights["risk_unfavorable_alignment"]
        if resource_support in {"positive", "favorable"}:
            risk_control_score += weights["risk_resource_support_relief"]
        if future_tendency in {"positive", "favorable"}:
            risk_control_score += weights["risk_future_support_relief"]
        if base_support == "challenging":
            risk_control_score += weights["risk_base_support_challenging"]
        elif base_support == "cautious":
            risk_control_score += weights["risk_base_support_cautious"]

        if risk_control_score >= thresholds["risk_tight_control_min"]:
            risk_control = "tight_control"
        elif risk_control_score <= thresholds["risk_measured_expansion_max"]:
            risk_control = "measured_expansion"
        else:
            risk_control = "balanced_control"

        wealth_mode = _wealth_mode(
            current_phase,
            future_tendency,
            resource_support,
            risk_control,
            rules,
        )

        conclusion = _build_wealth_conclusion(
            signal_texts,
            base_support=base_support,
            current_phase=current_phase,
            wealth_mode=wealth_mode,
            future_tendency=future_tendency,
            resource_support=resource_support,
            risk_control=risk_control,
        )

        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["determined"],
                evidence_refs=["E1203", "E1204", "E1206", "E1207", "E1208"],
            )
        )

        evidence_refs: list[str] = [
            "E1201",
            "E1202",
            "E1203",
            "E1204",
            "E1205",
            "E1206",
            "E1207",
            "E1208",
        ]
        _append_unique(evidence_refs, wealth_star_refs)
        _append_unique(evidence_refs, _collect_provisional_refs(provisional_conclusions))
        _append_unique(evidence_refs, _collect_final_refs(final_useful_god_v0))
        _append_unique(evidence_refs, _collect_climate_refs(climate_balance_v0))
        _append_unique(evidence_refs, _collect_shen_sha_refs(shen_sha_v0))
        _append_unique(evidence_refs, annual_reading_v0.evidence_refs)
        if pattern_system_v1.candidate_pattern is not None:
            _append_unique(evidence_refs, pattern_system_v1.candidate_pattern.evidence_refs)
        if pattern_system_v1.final_pattern is not None:
            _append_unique(evidence_refs, pattern_system_v1.final_pattern.evidence_refs)
        _append_unique(evidence_refs, pattern_system_v1.evidence_refs)
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
    except (KeyError, TypeError, ValueError):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return WealthReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            base_support="cautious",
            current_phase="cautious",
            wealth_mode="steady_accumulation",
            future_tendency="cautious",
            resource_support="cautious",
            risk_control="tight_control",
            conclusion="不足以判断。",
            notes=notes,
            evidence_refs=evidence_refs,
        )

    return WealthReadingOutput(
        method=rules["method"],
        status="determined",
        base_support=base_support,
        current_phase=current_phase,
        wealth_mode=wealth_mode,
        future_tendency=future_tendency,
        resource_support=resource_support,
        risk_control=risk_control,
        conclusion=conclusion,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _relationship_star_snapshot(
    ten_gods: TenGodsOutput,
    relationship_gods: set[str],
) -> tuple[list[object], list[object], list[object], set[str], list[str]]:
    visible_matches = [
        item for item in ten_gods.stems_visible if item.god in relationship_gods
    ]
    hidden_matches: list[object] = []
    day_branch_matches: list[object] = []
    elements: set[str] = set()
    refs: list[str] = []

    for item in visible_matches:
        elements.add(get_stem_element(item.stem))
        _append_unique(refs, item.evidence_refs)

    for branch_item in ten_gods.branches_hidden:
        branch_matches = [
            item for item in branch_item.hidden_stems if item.god in relationship_gods
        ]
        hidden_matches.extend(branch_matches)
        if branch_item.pillar == "day":
            day_branch_matches.extend(branch_matches)
        for item in branch_matches:
            elements.add(get_stem_element(item.stem))
            _append_unique(refs, item.evidence_refs)

    return visible_matches, hidden_matches, day_branch_matches, elements, refs


def _weighted_relationship_signal_total(
    signals: list[str],
    weights: dict[str, int],
    prefix: str,
) -> int:
    return sum(weights[f"{prefix}_{signal}_year"] for signal in signals)


def _build_relationship_conclusion(
    signal_texts: dict[str, dict[str, str]],
    *,
    base_support: str,
    partner_support: str,
    stability_tendency: str,
    current_phase: str,
    future_tendency: str,
) -> str:
    return "".join(
        [
            signal_texts["base_support"][base_support],
            signal_texts["partner_support"][partner_support],
            signal_texts["stability_tendency"][stability_tendency],
            signal_texts["current_phase"][current_phase],
            signal_texts["future_tendency"][future_tendency],
        ]
    )


def _build_relationship_reading(
    chart: ChartOutput,
    ten_gods: TenGodsOutput,
    strength: StrengthOutput,
    provisional_conclusions: ProvisionalConclusions,
    final_useful_god_v0: FinalUsefulGodOutput,
    annual_reading_v0: AnnualReadingOutput,
    shen_sha_v0: ShenShaOutput,
) -> RelationshipReadingOutput:
    rules = load_relationship_reading_rules()
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["gender_mapping_note"],
            evidence_refs=["E1001", "E1002"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["shen_sha_auxiliary_note"],
            evidence_refs=["E1005"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["future_window_note"],
            evidence_refs=["E1004", "E1006"],
        ),
    ]

    if annual_reading_v0.status != "determined" or not annual_reading_v0.entries:
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs: list[str] = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return RelationshipReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            base_support="cautious",
            partner_support="cautious",
            stability_tendency="cautious",
            current_phase="cautious",
            future_tendency="cautious",
            conclusion="不足以判断。",
            notes=notes,
            evidence_refs=evidence_refs,
        )

    try:
        relationship_gods = _relationship_gods_for_gender(chart.input_snapshot.gender, rules)
        (
            visible_matches,
            hidden_matches,
            day_branch_matches,
            relationship_elements,
            relationship_star_refs,
        ) = _relationship_star_snapshot(ten_gods, relationship_gods)
        weights = {key: int(value) for key, value in rules["score_weights"].items()}
        thresholds = {key: int(value) for key, value in rules["thresholds"].items()}
        signal_texts = rules["signal_texts"]
        phase_mapping = rules["phase_mapping"]
        related_shen_sha_keys = set(rules["related_shen_sha_keys"])

        supportive_elements = {
            item.element for item in provisional_conclusions.favorable_elements_candidates
        }
        if final_useful_god_v0.primary_element is not None:
            supportive_elements.add(final_useful_god_v0.primary_element)
        supportive_elements.update(final_useful_god_v0.secondary_elements)
        unfavorable_elements = {
            item.element for item in provisional_conclusions.unfavorable_elements_candidates
        }

        base_support_score = (
            len(visible_matches) * weights["base_visible_star"]
            + len(hidden_matches) * weights["base_hidden_star"]
        )
        if day_branch_matches:
            base_support_score += weights["base_day_branch_bonus"]
        if relationship_elements.intersection(supportive_elements):
            base_support_score += weights["base_supportive_alignment"]
        if relationship_elements.intersection(unfavorable_elements):
            base_support_score += weights["base_unfavorable_alignment_penalty"]
        elif strength.label == "weak" and not relationship_elements.intersection(supportive_elements):
            base_support_score += weights["base_weak_unaligned_penalty"]

        base_support = _signal_from_score(
            base_support_score,
            thresholds["base_support_favorable_min"],
            thresholds["base_support_positive_min"],
            thresholds["base_support_cautious_max"],
            thresholds["base_support_challenging_max"],
        )

        current_entry = annual_reading_v0.entries[0]
        current_phase = phase_mapping[current_entry.relationship_signal]

        partner_support_score = 0
        if visible_matches:
            partner_support_score += weights["partner_visible_presence"]
        if hidden_matches:
            partner_support_score += weights["partner_hidden_presence"]
        if current_entry.mentor_signal == "favorable":
            partner_support_score += weights["partner_current_mentor_favorable"]
        elif current_entry.mentor_signal == "positive":
            partner_support_score += weights["partner_current_mentor_positive"]
        if current_entry.relationship_signal == "favorable":
            partner_support_score += weights["partner_current_relationship_favorable"]
        elif current_entry.relationship_signal == "positive":
            partner_support_score += weights["partner_current_relationship_positive"]
        elif current_entry.relationship_signal == "cautious":
            partner_support_score += weights["partner_current_relationship_cautious"]
        elif current_entry.relationship_signal == "challenging":
            partner_support_score += weights["partner_current_relationship_challenging"]

        shen_sha_hit_keys = {item.key for item in shen_sha_v0.hits}
        if "tianyi_guiren" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            partner_support_score += weights["partner_tianyi_auxiliary"]
        if "taohua" in shen_sha_hit_keys.intersection(related_shen_sha_keys):
            partner_support_score += weights["partner_taohua_auxiliary"]

        partner_support = _signal_from_score(
            partner_support_score,
            thresholds["partner_support_favorable_min"],
            thresholds["partner_support_positive_min"],
            thresholds["partner_support_cautious_max"],
            thresholds["partner_support_challenging_max"],
        )

        relationship_signals = [
            item.relationship_signal for item in annual_reading_v0.entries
        ]
        future_score = _weighted_relationship_signal_total(
            relationship_signals,
            weights,
            "future",
        )
        future_tendency = _signal_from_score(
            future_score,
            thresholds["future_favorable_min"],
            thresholds["future_positive_min"],
            thresholds["future_cautious_max"],
            thresholds["future_challenging_max"],
        )

        stability_score = _weighted_relationship_signal_total(
            relationship_signals,
            weights,
            "stability",
        )
        if base_support in {"favorable", "positive"}:
            stability_score += weights["stability_base_support_bonus"]
        if current_phase == "cautious":
            stability_score += weights["stability_current_phase_cautious_penalty"]

        stability_tendency = _signal_from_score(
            stability_score,
            thresholds["stability_favorable_min"],
            thresholds["stability_positive_min"],
            thresholds["stability_cautious_max"],
            thresholds["stability_challenging_max"],
        )

        conclusion = _build_relationship_conclusion(
            signal_texts,
            base_support=base_support,
            partner_support=partner_support,
            stability_tendency=stability_tendency,
            current_phase=current_phase,
            future_tendency=future_tendency,
        )

        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["determined"],
                evidence_refs=["E1003", "E1004", "E1006", "E1007"],
            )
        )

        evidence_refs: list[str] = ["E1002", "E1003", "E1004", "E1005", "E1006", "E1007"]
        _append_unique(evidence_refs, relationship_star_refs)
        _append_unique(evidence_refs, _collect_provisional_refs(provisional_conclusions))
        _append_unique(evidence_refs, _collect_final_refs(final_useful_god_v0))
        _append_unique(evidence_refs, _collect_shen_sha_refs(shen_sha_v0))
        _append_unique(evidence_refs, annual_reading_v0.evidence_refs)
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
    except (KeyError, TypeError, ValueError):
        notes.append(
            EvidenceNote(
                text=rules["reason_texts"]["insufficient"],
                evidence_refs=["E107"],
            )
        )
        evidence_refs = []
        for note in notes:
            _append_unique(evidence_refs, note.evidence_refs)
        return RelationshipReadingOutput(
            method=rules["method"],
            status="insufficient_for_determination",
            base_support="cautious",
            partner_support="cautious",
            stability_tendency="cautious",
            current_phase="cautious",
            future_tendency="cautious",
            conclusion="不足以判断。",
            notes=notes,
            evidence_refs=evidence_refs,
        )

    return RelationshipReadingOutput(
        method=rules["method"],
        status="determined",
        base_support=base_support,
        partner_support=partner_support,
        stability_tendency=stability_tendency,
        current_phase=current_phase,
        future_tendency=future_tendency,
        conclusion=conclusion,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def _shen_sha_basis_value(chart: ChartOutput, basis_type: str) -> str | None:
    if basis_type == "day_stem":
        return chart.day_master
    if basis_type == "day_branch":
        return chart.pillars.day.branch
    if basis_type == "year_branch":
        return chart.pillars.year.branch
    return None


def _build_shen_sha(chart: ChartOutput) -> ShenShaOutput:
    rules = load_shen_sha_rules()
    notes = [
        EvidenceNote(
            text=rules["reason_texts"]["scope_note"],
            evidence_refs=["E601"],
        ),
        EvidenceNote(
            text=rules["reason_texts"]["structural_note"],
            evidence_refs=["E605"],
        ),
    ]

    pillar_branches = [
        ("year", chart.pillars.year.branch),
        ("month", chart.pillars.month.branch),
        ("day", chart.pillars.day.branch),
        ("hour", chart.pillars.hour.branch),
    ]
    hits: list[ShenShaHit] = []

    for key in rules["selected_keys"]:
        config = rules["rules"].get(key)
        if not isinstance(config, dict):
            notes.append(
                EvidenceNote(
                    text=rules["reason_texts"]["insufficient"],
                    evidence_refs=["E107"],
                )
            )
            evidence_refs: list[str] = []
            for note in notes:
                _append_unique(evidence_refs, note.evidence_refs)
            return ShenShaOutput(
                method=rules["method"],
                status="insufficient_for_determination",
                hits=[],
                notes=notes,
                evidence_refs=evidence_refs,
            )

        basis_type = config["basis"]
        basis_value = _shen_sha_basis_value(chart, basis_type)
        targets = config["mapping"].get(basis_value) if basis_value is not None else None
        if basis_value is None or not isinstance(targets, list):
            notes.append(
                EvidenceNote(
                    text=rules["reason_texts"]["insufficient"],
                    evidence_refs=["E602", "E107"],
                )
            )
            evidence_refs = []
            for note in notes:
                _append_unique(evidence_refs, note.evidence_refs)
            return ShenShaOutput(
                method=rules["method"],
                status="insufficient_for_determination",
                hits=[],
                notes=notes,
                evidence_refs=evidence_refs,
            )

        basis = ShenShaBasis(
            basis_type=basis_type,
            basis_value=basis_value,
            evidence_refs=["E602"],
        )
        matched_pillar_refs: list[ShenShaMatchedPillarRef] = []
        for pillar_name, branch in pillar_branches:
            if branch in targets:
                matched_pillar_refs.append(
                    ShenShaMatchedPillarRef(
                        pillar=pillar_name,
                        target_type="branch",
                        target_value=branch,
                        evidence_refs=["E603"],
                    )
                )

        if matched_pillar_refs:
            hit_refs = list(basis.evidence_refs)
            for matched in matched_pillar_refs:
                _append_unique(hit_refs, matched.evidence_refs)
            hits.append(
                ShenShaHit(
                    key=key,
                    name=config["name"],
                    basis=basis,
                    matched_pillar_refs=matched_pillar_refs,
                    evidence_refs=hit_refs,
                )
            )

    notes.append(
        EvidenceNote(
            text=rules["reason_texts"]["determined"] if hits else rules["reason_texts"]["no_hit"],
            evidence_refs=["E604"],
        )
    )
    evidence_refs: list[str] = []
    for hit in hits:
        _append_unique(evidence_refs, hit.evidence_refs)
        _append_unique(evidence_refs, hit.basis.evidence_refs)
        for matched in hit.matched_pillar_refs:
            _append_unique(evidence_refs, matched.evidence_refs)
    for note in notes:
        _append_unique(evidence_refs, note.evidence_refs)

    return ShenShaOutput(
        method=rules["method"],
        status="determined",
        hits=hits,
        notes=notes,
        evidence_refs=evidence_refs,
    )


def build_rules_output(chart: ChartOutput) -> RulesOutput:
    ten_gods = calculate_ten_gods(chart)
    strength = judge_strength(chart, ten_gods)
    pattern_system_v1 = _build_pattern_system(ten_gods)
    climate_balance_v0 = _build_climate_balance(chart, ten_gods)
    annual_flow_v0 = _build_annual_flow(chart)
    provisional_conclusions = _build_provisional_conclusions(chart, strength, ten_gods)
    final_useful_god_v0 = build_final_useful_god(
        chart,
        strength,
        ten_gods,
        provisional_conclusions,
    )
    shen_sha_v0 = _build_shen_sha(chart)
    annual_reading_v0 = _build_annual_reading(
        chart,
        provisional_conclusions,
        final_useful_god_v0,
        climate_balance_v0,
        shen_sha_v0,
    )
    career_reading_v0 = _build_career_reading(
        chart,
        ten_gods,
        strength,
        provisional_conclusions,
        final_useful_god_v0,
        pattern_system_v1,
        climate_balance_v0,
        annual_reading_v0,
        shen_sha_v0,
    )
    wealth_reading_v0 = _build_wealth_reading(
        ten_gods,
        strength,
        provisional_conclusions,
        final_useful_god_v0,
        pattern_system_v1,
        climate_balance_v0,
        annual_reading_v0,
        shen_sha_v0,
    )
    relationship_reading_v0 = _build_relationship_reading(
        chart,
        ten_gods,
        strength,
        provisional_conclusions,
        final_useful_god_v0,
        annual_reading_v0,
        shen_sha_v0,
    )

    pattern_name = "不足以判断"
    if pattern_system_v1.final_pattern is not None:
        pattern_name = pattern_system_v1.final_pattern.pattern_name
    elif pattern_system_v1.candidate_pattern is not None:
        pattern_name = pattern_system_v1.candidate_pattern.pattern_name

    climate_context = "不足以判断"
    if climate_balance_v0.season_context is not None:
        climate_context = climate_balance_v0.season_context.season_name
    annual_window = "不足以判断"
    if annual_flow_v0.window.start_year is not None and annual_flow_v0.window.end_year is not None:
        annual_window = f"{annual_flow_v0.window.start_year}-{annual_flow_v0.window.end_year}"
    shen_sha_hit_count = len(shen_sha_v0.hits)

    summary = (
        f"日主{chart.day_master}；十神已完成明透与藏干映射；"
        f"基础旺衰评分 v0 结果为 {strength.label}/{strength.summary}；"
        f"月令主气格识别 v1 状态为 {pattern_system_v1.status}/{pattern_name}；"
        f"调候受控版 v0 状态为 {climate_balance_v0.status}/{climate_context}季；"
        f"流年骨架 v0 状态为 {annual_flow_v0.status}/{annual_window}；"
        f"神煞受控版 v0 状态为 {shen_sha_v0.status}/{shen_sha_hit_count}项命中；"
        f"事业专项受控版 v0 状态为 {career_reading_v0.status}/{career_reading_v0.current_phase}/{career_reading_v0.growth_mode}；"
        f"财运专项受控版 v0 状态为 {wealth_reading_v0.status}/{wealth_reading_v0.current_phase}/{wealth_reading_v0.wealth_mode}；"
        f"婚恋专项受控版 v0 状态为 {relationship_reading_v0.status}/{relationship_reading_v0.current_phase}；"
        f"候选用神方法为 {provisional_conclusions.method}；"
        f"最终用神受控版 v0 状态为 {final_useful_god_v0.status}。"
    )

    return RulesOutput(
        rules_version=RULES_VERSION,
        engine_version=chart.engine_version,
        based_on_chart_version=chart.engine_version,
        status="ok",
        day_master=chart.day_master,
        summary=summary,
        ten_gods=ten_gods,
        strength=strength,
        pattern_system_v1=pattern_system_v1,
        climate_balance_v0=climate_balance_v0,
        annual_flow_v0=annual_flow_v0,
        annual_reading_v0=annual_reading_v0,
        career_reading_v0=career_reading_v0,
        wealth_reading_v0=wealth_reading_v0,
        relationship_reading_v0=relationship_reading_v0,
        shen_sha_v0=shen_sha_v0,
        provisional_conclusions=provisional_conclusions,
        final_useful_god_v0=final_useful_god_v0,
    )
