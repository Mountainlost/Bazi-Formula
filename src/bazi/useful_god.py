from __future__ import annotations

from dataclasses import dataclass

from .models import (
    CandidateElement,
    ChartOutput,
    EvidenceNote,
    FinalUsefulGodDecisionBasis,
    FinalUsefulGodOutput,
    ProvisionalConclusions,
    StrengthOutput,
    TenGodsOutput,
)
from .rule_data import load_final_useful_god_rules, load_strength_rules
from .ten_gods import get_stem_element, relation_to_element

ALL_RELATIONS = (
    "same_element",
    "produced_by_day_master",
    "controlled_by_day_master",
    "produces_day_master",
    "controls_day_master",
)


@dataclass
class CandidateEvaluation:
    candidate: CandidateElement
    relation: str
    support_score: int
    priority_score: int
    total_score: int
    candidate_alignment: bool
    month_bias_alignment: bool
    distribution_alignment: bool
    extra_system_required: bool


def _unique_refs(*ref_groups: list[str]) -> list[str]:
    refs: list[str] = []
    for group in ref_groups:
        for ref in group:
            if ref not in refs:
                refs.append(ref)
    return refs


def _month_relation(day_master: str, month_branch: str) -> str:
    rules = load_strength_rules()
    month_element = rules["month_branch_elements"][month_branch]
    day_element = get_stem_element(day_master)
    if day_element == month_element:
        return "same_element"
    for relation in ALL_RELATIONS[1:]:
        if relation_to_element(day_master, relation) == month_element:
            return relation
    raise ValueError(f"Unable to resolve month relation for {day_master=} {month_branch=}.")


def _month_bias_group(month_relation: str) -> str:
    if month_relation in {"same_element", "produces_day_master"}:
        return "month_supports_day_master"
    return "month_weakens_day_master"


def _element_scores(chart: ChartOutput, ten_gods: TenGodsOutput) -> dict[str, int]:
    rules = load_final_useful_god_rules()
    scores = {
        "wood": 0,
        "fire": 0,
        "earth": 0,
        "metal": 0,
        "water": 0,
    }
    visible_weight = int(rules["support_weights"]["visible_stem"])
    hidden_weight = int(rules["support_weights"]["hidden_stem"])

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


def _relation_for_element(day_master: str, element: str) -> str:
    for relation in ALL_RELATIONS:
        if relation_to_element(day_master, relation) == element:
            return relation
    raise ValueError(f"Unable to resolve relation for {day_master=} {element=}.")


def _build_candidate_evaluations(
    chart: ChartOutput,
    strength: StrengthOutput,
    ten_gods: TenGodsOutput,
    provisional_conclusions: ProvisionalConclusions,
) -> tuple[list[CandidateEvaluation], str]:
    rules = load_final_useful_god_rules()
    month_relation = _month_relation(chart.day_master, chart.pillars.month.branch)
    month_bias_group = _month_bias_group(month_relation)
    element_scores = _element_scores(chart, ten_gods)
    priority_rules = rules["candidate_priority_rules"].get(strength.label, {})
    allowed_relations = rules["month_bias_alignment"][strength.label][month_bias_group][
        "allowed_relations"
    ]
    overrepresented_score = int(rules["thresholds"]["overrepresented_score"])
    extra_system_required_relations = set(
        rules["extra_system_required_relations"].get(strength.label, [])
    )

    evaluations: list[CandidateEvaluation] = []
    for candidate in provisional_conclusions.favorable_elements_candidates:
        relation = _relation_for_element(chart.day_master, candidate.element)
        support_score = element_scores[candidate.element]
        priority_score = int(priority_rules.get(relation, 0))
        evaluations.append(
            CandidateEvaluation(
                candidate=candidate,
                relation=relation,
                support_score=support_score,
                priority_score=priority_score,
                total_score=priority_score + support_score,
                candidate_alignment=relation in priority_rules,
                month_bias_alignment=relation in allowed_relations,
                distribution_alignment=support_score < overrepresented_score,
                extra_system_required=relation in extra_system_required_relations,
            )
        )

    evaluations.sort(
        key=lambda item: (
            item.total_score,
            item.priority_score,
            item.support_score,
        ),
        reverse=True,
    )
    return evaluations, month_relation


def build_final_useful_god(
    chart: ChartOutput,
    strength: StrengthOutput,
    ten_gods: TenGodsOutput,
    provisional_conclusions: ProvisionalConclusions,
) -> FinalUsefulGodOutput:
    rules = load_final_useful_god_rules()
    texts = rules["reason_texts"]
    statuses = rules["statuses"]
    thresholds = rules["finalize_allowed_when"]

    if strength.label in set(thresholds["disallow_strength_labels"]):
        blockers = [
            EvidenceNote(
                text=texts["insufficient_balanced"],
                evidence_refs=["E302", "E306"],
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["insufficient"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[
                EvidenceNote(
                    text=texts["controlled_method_note"],
                    evidence_refs=["E306"],
                )
            ],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=False,
                month_bias_alignment=False,
                distribution_alignment=False,
                conflict_detected=False,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(["E302", "E306"]),
        )

    evaluations, month_relation = _build_candidate_evaluations(
        chart,
        strength,
        ten_gods,
        provisional_conclusions,
    )

    if not evaluations:
        blockers = [
            EvidenceNote(
                text=texts["insufficient_no_candidate"],
                evidence_refs=["E301", "E306", "E107"],
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["insufficient"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[
                EvidenceNote(
                    text=texts["controlled_method_note"],
                    evidence_refs=["E306"],
                )
            ],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=False,
                month_bias_alignment=False,
                distribution_alignment=False,
                conflict_detected=False,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(["E301", "E306", "E107"]),
        )

    top = evaluations[0]
    candidate_alignment = top.candidate_alignment
    month_bias_alignment = top.month_bias_alignment
    distribution_alignment = top.distribution_alignment

    if not candidate_alignment:
        blockers = [
            EvidenceNote(
                text=texts["conflict_alignment"].format(element_zh=rules["element_labels"][top.candidate.element]),
                evidence_refs=_unique_refs(top.candidate.evidence_refs, ["E301", "E307"]),
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["blocked"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=False,
                month_bias_alignment=month_bias_alignment,
                distribution_alignment=distribution_alignment,
                conflict_detected=True,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(blockers[0].evidence_refs),
        )

    if not month_bias_alignment:
        blockers = [
            EvidenceNote(
                text=texts["conflict_month_bias"].format(element_zh=rules["element_labels"][top.candidate.element]),
                evidence_refs=_unique_refs(top.candidate.evidence_refs, ["E305", "E307"]),
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["blocked"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=True,
                month_bias_alignment=False,
                distribution_alignment=distribution_alignment,
                conflict_detected=True,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(blockers[0].evidence_refs),
        )

    if not distribution_alignment:
        blockers = [
            EvidenceNote(
                text=texts["conflict_overrepresented"].format(
                    element_zh=rules["element_labels"][top.candidate.element]
                ),
                evidence_refs=_unique_refs(top.candidate.evidence_refs, ["E304", "E307"]),
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["blocked"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=True,
                month_bias_alignment=True,
                distribution_alignment=False,
                conflict_detected=True,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(blockers[0].evidence_refs),
        )

    if top.extra_system_required:
        blockers = [
            EvidenceNote(
                text=texts["insufficient_extra_system"],
                evidence_refs=["E306", "E107"],
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["insufficient"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=True,
                month_bias_alignment=True,
                distribution_alignment=True,
                conflict_detected=False,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(blockers[0].evidence_refs, top.candidate.evidence_refs),
        )

    if top.support_score < int(thresholds["min_support_score"]):
        blockers = [
            EvidenceNote(
                text=texts["insufficient_support"].format(
                    element_zh=rules["element_labels"][top.candidate.element]
                ),
                evidence_refs=_unique_refs(top.candidate.evidence_refs, ["E301", "E306"]),
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["insufficient"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=True,
                month_bias_alignment=True,
                distribution_alignment=True,
                conflict_detected=False,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(blockers[0].evidence_refs),
        )

    second = evaluations[1] if len(evaluations) > 1 else None
    min_primary_gap = int(thresholds["min_primary_gap"])
    if second and (top.total_score - second.total_score) < min_primary_gap:
        blockers = [
            EvidenceNote(
                text=texts["insufficient_tied"],
                evidence_refs=["E303", "E306"],
            )
        ]
        return FinalUsefulGodOutput(
            status=statuses["insufficient"],
            confidence=rules["confidence_rules"]["unresolved_or_blocked"],
            primary_element=None,
            secondary_elements=[],
            reason_chain=[],
            blockers=blockers,
            decision_basis=FinalUsefulGodDecisionBasis(
                strength_label=strength.label,
                candidate_alignment=True,
                month_bias_alignment=True,
                distribution_alignment=True,
                conflict_detected=False,
                allowed_to_finalize=False,
            ),
            evidence_refs=_unique_refs(blockers[0].evidence_refs, top.candidate.evidence_refs),
        )

    reason_chain = [
        EvidenceNote(
            text=texts[f"strength_direction_{strength.label}"],
            evidence_refs=["E301"],
        ),
        EvidenceNote(
            text=texts["month_bias_aligned"],
            evidence_refs=["E305"],
        ),
        EvidenceNote(
            text=texts["candidate_supported"].format(
                element_zh=rules["element_labels"][top.candidate.element]
            ),
            evidence_refs=_unique_refs(top.candidate.evidence_refs, ["E301"]),
        ),
        EvidenceNote(
            text=texts["unique_primary"].format(
                element_zh=rules["element_labels"][top.candidate.element]
            ),
            evidence_refs=["E308"],
        ),
        EvidenceNote(
            text=texts["controlled_method_note"],
            evidence_refs=["E306"],
        ),
    ]

    secondary_elements: list[str] = []
    max_secondary = int(thresholds["max_secondary_elements"])
    for item in evaluations[1:]:
        if len(secondary_elements) >= max_secondary:
            break
        if (
            item.candidate_alignment
            and item.month_bias_alignment
            and item.distribution_alignment
            and not item.extra_system_required
        ):
            secondary_elements.append(item.candidate.element)
            reason_chain.append(
                EvidenceNote(
                    text=texts["secondary_retained"].format(
                        element_zh=rules["element_labels"][item.candidate.element]
                    ),
                    evidence_refs=_unique_refs(item.candidate.evidence_refs, ["E308"]),
                )
            )

    confidence_key = "determined_with_secondary" if secondary_elements else "determined_without_secondary"
    evidence_refs = _unique_refs(
        top.candidate.evidence_refs,
        ["E301", "E305", "E306", "E308"],
        *[note.evidence_refs for note in reason_chain],
    )

    return FinalUsefulGodOutput(
        status=statuses["determined"],
        confidence=rules["confidence_rules"][confidence_key],
        primary_element=top.candidate.element,
        secondary_elements=secondary_elements,
        reason_chain=reason_chain,
        blockers=[],
        decision_basis=FinalUsefulGodDecisionBasis(
            strength_label=strength.label,
            candidate_alignment=True,
            month_bias_alignment=True,
            distribution_alignment=True,
            conflict_detected=False,
            allowed_to_finalize=True,
        ),
        evidence_refs=evidence_refs,
    )
