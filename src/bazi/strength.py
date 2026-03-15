from __future__ import annotations

from .models import ChartOutput, StrengthFactor, StrengthOutput, TenGodsOutput
from .rule_data import load_strength_rules
from .ten_gods import (
    SUPPORT_RELATIONS,
    branch_hidden_stems,
    get_stem_element,
    is_drain_relation,
    is_support_relation,
    relation_category,
    relation_to_element,
)


def _month_relation(day_master: str, month_branch: str) -> str:
    rules = load_strength_rules()
    month_element = rules["month_branch_elements"][month_branch]
    day_element = get_stem_element(day_master)
    if day_element == month_element:
        return "same_element"
    if relation_to_element(day_master, "produced_by_day_master") == month_element:
        return "produced_by_day_master"
    if relation_to_element(day_master, "controlled_by_day_master") == month_element:
        return "controlled_by_day_master"
    if relation_to_element(day_master, "produces_day_master") == month_element:
        return "produces_day_master"
    if relation_to_element(day_master, "controls_day_master") == month_element:
        return "controls_day_master"
    raise ValueError(f"Unable to match month relation for {day_master=} {month_branch=}.")


def _unique_refs(factors: list[StrengthFactor]) -> list[str]:
    refs: list[str] = []
    for factor in factors:
        for ref in factor.evidence_refs:
            if ref not in refs:
                refs.append(ref)
    return refs


def judge_strength(chart: ChartOutput, ten_gods: TenGodsOutput) -> StrengthOutput:
    rules = load_strength_rules()
    strength_v0 = rules["strength_v0"]
    day_master = chart.day_master

    month_relation = _month_relation(day_master, chart.pillars.month.branch)
    month_impact = strength_v0["month_relation_impacts"][month_relation]

    visible_support_count = sum(
        1
        for item in ten_gods.stems_visible
        if not item.is_day_master and is_support_relation(relation_category(day_master, item.stem))
    )
    visible_drain_count = sum(
        1
        for item in ten_gods.stems_visible
        if not item.is_day_master and is_drain_relation(relation_category(day_master, item.stem))
    )
    hidden_support_count = sum(
        1
        for branch_item in ten_gods.branches_hidden
        for hidden_item in branch_item.hidden_stems
        if is_support_relation(relation_category(day_master, hidden_item.stem))
    )

    visible_support_impact = visible_support_count * strength_v0["visible_support_per_stem"]
    visible_drain_impact = visible_drain_count * strength_v0["visible_drain_per_stem"]
    hidden_support_impact = hidden_support_count * strength_v0["hidden_support_per_stem"]

    factors = [
        StrengthFactor(
            name=f"month_branch_{month_relation}",
            impact=month_impact,
            evidence_refs=["E101"],
        ),
        StrengthFactor(
            name="visible_support_stems",
            impact=visible_support_impact,
            evidence_refs=["E102", "E105"],
        ),
        StrengthFactor(
            name="hidden_root_support",
            impact=hidden_support_impact,
            evidence_refs=["E104"],
        ),
        StrengthFactor(
            name="visible_drain_and_control",
            impact=visible_drain_impact,
            evidence_refs=["E103", "E105"],
        ),
    ]

    score = sum(item.impact for item in factors)
    thresholds = strength_v0["thresholds"]
    if score <= thresholds["weak_max"]:
        label = "weak"
    elif score <= thresholds["balanced_max"]:
        label = "balanced"
    else:
        label = "strong"

    summaries = strength_v0["summaries"]
    return StrengthOutput(
        score=score,
        label=label,
        summary=summaries[label],
        factors=factors,
        evidence_refs=_unique_refs(factors),
    )
