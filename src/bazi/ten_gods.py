from __future__ import annotations

from typing import Literal

from .models import (
    BranchHiddenGod,
    BranchHiddenStems,
    ChartOutput,
    StemVisibleGod,
    TenGodsOutput,
)
from .rule_data import load_hidden_stem_rules, load_ten_god_rules

SUPPORT_RELATIONS = {"same_element", "produces_day_master"}
DRAIN_RELATIONS = {
    "controls_day_master",
    "produced_by_day_master",
    "controlled_by_day_master",
}


def _stem_metadata(stem: str) -> dict[str, str]:
    rules = load_ten_god_rules()
    metadata = rules.get("stems", {}).get(stem)
    if not isinstance(metadata, dict):
        raise ValueError(f"Unknown stem mapping: {stem}")
    return metadata


def get_stem_element(stem: str) -> str:
    return _stem_metadata(stem)["element"]


def get_stem_polarity(stem: str) -> str:
    return _stem_metadata(stem)["polarity"]


def _element_rules() -> dict[str, dict[str, str]]:
    rules = load_ten_god_rules()
    elements = rules.get("elements")
    if not isinstance(elements, dict):
        raise ValueError("十神映射.yaml must define an 'elements' mapping.")
    return elements


def relation_category(day_master_stem: str, other_stem: str) -> str:
    day_element = get_stem_element(day_master_stem)
    other_element = get_stem_element(other_stem)
    element_rules = _element_rules()

    if day_element == other_element:
        return "same_element"
    if element_rules[day_element]["generates"] == other_element:
        return "produced_by_day_master"
    if element_rules[day_element]["controls"] == other_element:
        return "controlled_by_day_master"
    if element_rules[other_element]["generates"] == day_element:
        return "produces_day_master"
    if element_rules[other_element]["controls"] == day_element:
        return "controls_day_master"
    raise ValueError(f"Unable to determine relation between {day_master_stem} and {other_stem}.")


def god_name(day_master_stem: str, other_stem: str) -> str:
    relation = relation_category(day_master_stem, other_stem)
    polarity_key: Literal["same_polarity", "opposite_polarity"]
    if get_stem_polarity(day_master_stem) == get_stem_polarity(other_stem):
        polarity_key = "same_polarity"
    else:
        polarity_key = "opposite_polarity"
    rules = load_ten_god_rules()
    return rules["ten_gods"][relation][polarity_key]


def relation_to_element(day_master_stem: str, relation: str) -> str:
    day_element = get_stem_element(day_master_stem)
    element_rules = _element_rules()
    if relation == "same_element":
        return day_element
    if relation == "produced_by_day_master":
        return element_rules[day_element]["generates"]
    if relation == "controlled_by_day_master":
        return element_rules[day_element]["controls"]
    if relation == "produces_day_master":
        for element_name, mapping in element_rules.items():
            if mapping["generates"] == day_element:
                return element_name
    if relation == "controls_day_master":
        for element_name, mapping in element_rules.items():
            if mapping["controls"] == day_element:
                return element_name
    raise ValueError(f"Unsupported relation for element derivation: {relation}")


def is_support_relation(relation: str) -> bool:
    return relation in SUPPORT_RELATIONS


def is_drain_relation(relation: str) -> bool:
    return relation in DRAIN_RELATIONS


def branch_hidden_stems(branch: str) -> list[str]:
    mapping = load_hidden_stem_rules()
    hidden_stems = mapping.get(branch)
    if not isinstance(hidden_stems, list):
        raise ValueError(f"Unknown branch hidden stem mapping: {branch}")
    return hidden_stems


def calculate_ten_gods(chart: ChartOutput) -> TenGodsOutput:
    day_master = chart.day_master
    stems_visible = [
        StemVisibleGod(
            pillar="year",
            stem=chart.pillars.year.stem,
            god=god_name(day_master, chart.pillars.year.stem),
            is_day_master=False,
            evidence_refs=["E106", "E105"],
        ),
        StemVisibleGod(
            pillar="month",
            stem=chart.pillars.month.stem,
            god=god_name(day_master, chart.pillars.month.stem),
            is_day_master=False,
            evidence_refs=["E106", "E105"],
        ),
        StemVisibleGod(
            pillar="day",
            stem=chart.pillars.day.stem,
            god="day_master",
            is_day_master=True,
            evidence_refs=["E106"],
        ),
        StemVisibleGod(
            pillar="hour",
            stem=chart.pillars.hour.stem,
            god=god_name(day_master, chart.pillars.hour.stem),
            is_day_master=False,
            evidence_refs=["E106", "E105"],
        ),
    ]

    branches_hidden = []
    branch_inputs = [
        ("year", chart.pillars.year.branch),
        ("month", chart.pillars.month.branch),
        ("day", chart.pillars.day.branch),
        ("hour", chart.pillars.hour.branch),
    ]
    for pillar_name, branch in branch_inputs:
        hidden_entries = [
            BranchHiddenGod(
                stem=stem,
                god=god_name(day_master, stem),
                evidence_refs=["E106", "E104"],
            )
            for stem in branch_hidden_stems(branch)
        ]
        branches_hidden.append(
            BranchHiddenStems(
                pillar=pillar_name,
                branch=branch,
                hidden_stems=hidden_entries,
            )
        )

    return TenGodsOutput(
        stems_visible=stems_visible,
        branches_hidden=branches_hidden,
    )
