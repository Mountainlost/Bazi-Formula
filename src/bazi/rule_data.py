from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "规则映射"


@lru_cache(maxsize=None)
def load_yaml_mapping(file_name: str) -> Any:
    path = RULES_DIR / file_name
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=None)
def load_ten_god_rules() -> dict[str, Any]:
    data = load_yaml_mapping("十神映射.yaml")
    if not isinstance(data, dict):
        raise ValueError("十神映射.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_hidden_stem_rules() -> dict[str, list[str]]:
    data = load_yaml_mapping("地支藏干.yaml")
    branches = data.get("branches", {}) if isinstance(data, dict) else {}
    if not isinstance(branches, dict):
        raise ValueError("地支藏干.yaml must define a 'branches' mapping.")
    return branches


@lru_cache(maxsize=None)
def load_strength_rules() -> dict[str, Any]:
    data = load_yaml_mapping("月令权重.yaml")
    if not isinstance(data, dict):
        raise ValueError("月令权重.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_candidate_rules() -> dict[str, Any]:
    data = load_yaml_mapping("候选用神规则.yaml")
    if not isinstance(data, dict):
        raise ValueError("候选用神规则.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_final_useful_god_rules() -> dict[str, Any]:
    data = load_yaml_mapping("最终用神规则.yaml")
    if not isinstance(data, dict):
        raise ValueError("最终用神规则.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_pattern_rules() -> dict[str, Any]:
    data = load_yaml_mapping("pattern_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("pattern_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_climate_rules() -> dict[str, Any]:
    data = load_yaml_mapping("climate_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("climate_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_annual_flow_rules() -> dict[str, Any]:
    data = load_yaml_mapping("annual_flow_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("annual_flow_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_annual_reading_rules() -> dict[str, Any]:
    data = load_yaml_mapping("annual_reading_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("annual_reading_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_career_reading_rules() -> dict[str, Any]:
    data = load_yaml_mapping("career_reading_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("career_reading_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_relationship_reading_rules() -> dict[str, Any]:
    data = load_yaml_mapping("relationship_reading_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("relationship_reading_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_wealth_reading_rules() -> dict[str, Any]:
    data = load_yaml_mapping("wealth_reading_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("wealth_reading_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_final_report_rules() -> dict[str, Any]:
    data = load_yaml_mapping("final_report_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("final_report_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_shen_sha_rules() -> dict[str, Any]:
    data = load_yaml_mapping("shen_sha_rules.yaml")
    if not isinstance(data, dict):
        raise ValueError("shen_sha_rules.yaml must contain a mapping object.")
    return data


@lru_cache(maxsize=None)
def load_evidence_registry() -> list[dict[str, Any]]:
    data = load_yaml_mapping("evidence_registry.yaml")
    if not isinstance(data, list):
        raise ValueError("evidence_registry.yaml must contain a list.")
    return data


@lru_cache(maxsize=None)
def load_enabled_evidence_ids() -> set[str]:
    return {
        item["id"]
        for item in load_evidence_registry()
        if isinstance(item, dict) and item.get("enabled") and "id" in item
    }
