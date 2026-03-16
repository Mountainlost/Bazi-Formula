from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FiveElement = Literal["wood", "fire", "earth", "metal", "water"]
StrengthLabel = Literal["weak", "balanced", "strong"]
StrengthSummaryText = Literal["偏弱", "中和", "偏强"]
PatternStatus = Literal["determined", "candidate_only", "insufficient_for_determination"]
PatternKey = Literal[
    "yuebi",
    "yuejie",
    "yueshishen",
    "yueshangguan",
    "yuezhengcai",
    "yuepiancai",
    "yuezhengguan",
    "yueqisha",
    "yuezhengyin",
    "yuepianyin",
]
PatternTransparency = Literal["visible", "hidden_only"]
ClimateStatus = Literal["determined", "candidate_only", "insufficient_for_determination"]
ClimateSeason = Literal["spring", "summer", "autumn", "winter"]
ClimateTendency = Literal["hot", "cold", "dry", "damp"]
ClimateDirection = Literal["warming", "cooling", "moistening", "drying"]
AnnualFlowStatus = Literal["determined", "insufficient_for_determination"]
AnnualReadingStatus = Literal["determined", "insufficient_for_determination"]
AnnualReadingSignal = Literal["favorable", "positive", "mixed", "cautious", "challenging"]
CareerReadingStatus = Literal[
    "determined",
    "candidate_only",
    "insufficient_for_determination",
]
CareerPhase = Literal["active", "steady", "cautious"]
CareerGrowthMode = Literal["steady_build", "leverage_support", "active_breakthrough"]
WealthReadingStatus = Literal[
    "determined",
    "candidate_only",
    "insufficient_for_determination",
]
WealthPhase = Literal["active", "steady", "cautious"]
WealthMode = Literal["steady_accumulation", "leverage_growth", "risk_control"]
WealthRiskControl = Literal[
    "tight_control",
    "balanced_control",
    "measured_expansion",
]
RelationshipReadingStatus = Literal[
    "determined",
    "candidate_only",
    "insufficient_for_determination",
]
RelationshipPhase = Literal["active", "steady", "cautious"]
ShenShaStatus = Literal["determined", "insufficient_for_determination"]
ShenShaKey = Literal[
    "tianyi_guiren",
    "taohua",
    "yima",
    "wenchang",
    "huagai",
]
ShenShaBasisType = Literal["day_stem", "day_branch", "year_branch"]
FinalUsefulGodStatus = Literal[
    "determined",
    "insufficient_for_final_determination",
    "blocked_by_conflict",
]
FinalConfidence = Literal["low", "medium", "high"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BaziInput(StrictModel):
    birth_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    birth_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    birth_place: str = Field(min_length=1)
    gender: Literal["male", "female", "other"]
    calendar_type: Literal["solar", "lunar"]
    timezone: str = Field(min_length=1)
    true_solar_time: bool
    school: Literal["bazi_ziping_v1"]
    question: str | None = None


class CalcNormalizationStep(StrictModel):
    name: Literal["lunar_to_solar", "true_solar_time_adjustment"]
    input_value: str
    output_value: str
    evidence_refs: list[str] = Field(min_length=1)


class CalcBasis(StrictModel):
    calendar_type: Literal["solar"]
    timezone: str
    true_solar_time: bool = False
    real_calendar: bool = True
    month_rule: str
    day_rule: str
    library_name: str
    normalization_steps: list[CalcNormalizationStep] | None = None


class InputSnapshot(StrictModel):
    birth_date: str
    birth_time: str
    birth_place: str
    gender: str
    calendar_type: str
    timezone: str
    true_solar_time: bool
    school: str


class GanzhiPillar(StrictModel):
    stem: str = Field(min_length=1, max_length=1)
    branch: str = Field(min_length=1, max_length=1)
    ganzhi: str = Field(min_length=2, max_length=2)


class Pillars(StrictModel):
    year: GanzhiPillar
    month: GanzhiPillar
    day: GanzhiPillar
    hour: GanzhiPillar


class LuckCycleBasis(StrictModel):
    direction_rule: str
    start_age_rule: str
    jieqi_anchor_rule: str
    library_name: str
    enabled: bool = True


class LuckCycleEntry(StrictModel):
    index: int = Field(ge=1)
    ganzhi: str = Field(min_length=2, max_length=2)
    stem: str = Field(min_length=1, max_length=1)
    branch: str = Field(min_length=1, max_length=1)
    start_age: float
    end_age: float
    start_year: int
    end_year: int
    evidence_refs: list[str] = Field(min_length=1)


class LuckCycleOutput(StrictModel):
    basis: LuckCycleBasis
    direction: Literal["forward", "backward"]
    start_age: float
    start_datetime: str
    cycles: list[LuckCycleEntry] = Field(min_length=8)
    evidence_refs: list[str] = Field(min_length=1)


class CalendarContext(StrictModel):
    calc_basis: CalcBasis
    input_snapshot: InputSnapshot
    solar_datetime: str
    year_ganzhi: str
    month_ganzhi: str
    day_ganzhi: str
    hour_ganzhi: str


class ChartOutput(StrictModel):
    engine_version: str
    school: str
    calc_basis: CalcBasis
    input_snapshot: InputSnapshot
    solar_datetime: str
    pillars: Pillars
    day_master: str = Field(min_length=1, max_length=1)
    luck_cycle: LuckCycleOutput
    status: Literal["ok"] = "ok"


class StemVisibleGod(StrictModel):
    pillar: Literal["year", "month", "day", "hour"]
    stem: str = Field(min_length=1, max_length=1)
    god: str
    is_day_master: bool = False
    evidence_refs: list[str] = Field(min_length=1)


class BranchHiddenGod(StrictModel):
    stem: str = Field(min_length=1, max_length=1)
    god: str
    evidence_refs: list[str] = Field(min_length=1)


class BranchHiddenStems(StrictModel):
    pillar: Literal["year", "month", "day", "hour"]
    branch: str = Field(min_length=1, max_length=1)
    hidden_stems: list[BranchHiddenGod] = Field(min_length=1)


class TenGodsOutput(StrictModel):
    stems_visible: list[StemVisibleGod] = Field(min_length=4)
    branches_hidden: list[BranchHiddenStems] = Field(min_length=4)


class StrengthFactor(StrictModel):
    name: str
    impact: int
    evidence_refs: list[str] = Field(min_length=1)


class StrengthOutput(StrictModel):
    score: int
    label: StrengthLabel
    summary: StrengthSummaryText
    factors: list[StrengthFactor] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class CandidateElement(StrictModel):
    element: FiveElement
    reason: str
    evidence_refs: list[str] = Field(min_length=1)


class EvidenceNote(StrictModel):
    text: str
    evidence_refs: list[str] = Field(min_length=1)


class ProvisionalConclusions(StrictModel):
    favorable_elements_candidates: list[CandidateElement] = Field(default_factory=list)
    unfavorable_elements_candidates: list[CandidateElement] = Field(default_factory=list)
    method: Literal["candidate_only_v0"] = "candidate_only_v0"
    notes: list[EvidenceNote] = Field(min_length=1)


class PatternConclusion(StrictModel):
    pattern_key: PatternKey
    pattern_name: str
    source: Literal["month_branch_main_qi"] = "month_branch_main_qi"
    source_name: Literal["月令主气"] = "月令主气"
    source_stem: str = Field(min_length=1, max_length=1)
    source_god: str
    transparency: PatternTransparency
    evidence_refs: list[str] = Field(min_length=1)


class PatternSystemOutput(StrictModel):
    method: Literal["month_main_qi_pattern_v1"] = "month_main_qi_pattern_v1"
    status: PatternStatus
    candidate_pattern: PatternConclusion | None = None
    final_pattern: PatternConclusion | None = None
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class ClimateSeasonContext(StrictModel):
    month_branch: str = Field(min_length=1, max_length=1)
    season: ClimateSeason
    season_name: str
    baseline_tendencies: list[ClimateTendency] = Field(min_length=1)
    detected_tendencies: list[ClimateTendency] = Field(default_factory=list)
    evidence_refs: list[str] = Field(min_length=1)


class ClimateAdjustment(StrictModel):
    element: FiveElement
    direction: ClimateDirection
    priority: int = Field(ge=1)
    reason: str
    evidence_refs: list[str] = Field(min_length=1)


class ClimateBalanceOutput(StrictModel):
    method: Literal["climate_balance_v0"] = "climate_balance_v0"
    status: ClimateStatus
    season_context: ClimateSeasonContext | None = None
    candidate_adjustments: list[ClimateAdjustment] = Field(default_factory=list)
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class AnnualFlowWindow(StrictModel):
    start_year: int | None = None
    end_year: int | None = None
    preview_year_count: int = Field(ge=1)
    start_year_source: Literal["luck_cycle_first_entry_start_year"] = (
        "luck_cycle_first_entry_start_year"
    )
    sequencing_basis: Literal["birth_year_pillar_plus_solar_year_delta"] = (
        "birth_year_pillar_plus_solar_year_delta"
    )


class AnnualFlowEntry(StrictModel):
    year: int
    ganzhi: str = Field(min_length=2, max_length=2)
    relative_index: int = Field(ge=0)
    evidence_refs: list[str] = Field(min_length=1)


class AnnualFlowOutput(StrictModel):
    method: Literal["annual_flow_v0"] = "annual_flow_v0"
    status: AnnualFlowStatus
    window: AnnualFlowWindow
    entries: list[AnnualFlowEntry] = Field(default_factory=list)
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class AnnualReadingWindow(StrictModel):
    start_year: int | None = None
    end_year: int | None = None
    preview_year_count: int = Field(ge=1)
    reference_year: int
    reference_year_source: Literal["project_reference_year_v0"] = (
        "project_reference_year_v0"
    )
    sequencing_basis: Literal["birth_year_pillar_plus_solar_year_delta"] = (
        "birth_year_pillar_plus_solar_year_delta"
    )


class AnnualReadingEntry(StrictModel):
    year: int
    ganzhi: str = Field(min_length=2, max_length=2)
    career_signal: AnnualReadingSignal
    wealth_signal: AnnualReadingSignal
    relationship_signal: AnnualReadingSignal
    mentor_signal: AnnualReadingSignal
    summary: str
    evidence_refs: list[str] = Field(min_length=1)


class AnnualReadingOutput(StrictModel):
    method: Literal["annual_reading_v0"] = "annual_reading_v0"
    status: AnnualReadingStatus
    window: AnnualReadingWindow
    entries: list[AnnualReadingEntry] = Field(default_factory=list)
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class CareerReadingOutput(StrictModel):
    method: Literal["career_reading_v0"] = "career_reading_v0"
    status: CareerReadingStatus
    base_support: AnnualReadingSignal
    current_phase: CareerPhase
    growth_mode: CareerGrowthMode
    future_tendency: AnnualReadingSignal
    resource_support: AnnualReadingSignal
    conclusion: str
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class WealthReadingOutput(StrictModel):
    method: Literal["wealth_reading_v0"] = "wealth_reading_v0"
    status: WealthReadingStatus
    base_support: AnnualReadingSignal
    current_phase: WealthPhase
    wealth_mode: WealthMode
    future_tendency: AnnualReadingSignal
    resource_support: AnnualReadingSignal
    risk_control: WealthRiskControl
    conclusion: str
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class RelationshipReadingOutput(StrictModel):
    method: Literal["relationship_reading_v0"] = "relationship_reading_v0"
    status: RelationshipReadingStatus
    base_support: AnnualReadingSignal
    partner_support: AnnualReadingSignal
    stability_tendency: AnnualReadingSignal
    current_phase: RelationshipPhase
    future_tendency: AnnualReadingSignal
    conclusion: str
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class ShenShaBasis(StrictModel):
    basis_type: ShenShaBasisType
    basis_value: str = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class ShenShaMatchedPillarRef(StrictModel):
    pillar: Literal["year", "month", "day", "hour"]
    target_type: Literal["branch"]
    target_value: str = Field(min_length=1, max_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class ShenShaHit(StrictModel):
    key: ShenShaKey
    name: str
    basis: ShenShaBasis
    matched_pillar_refs: list[ShenShaMatchedPillarRef] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class ShenShaOutput(StrictModel):
    method: Literal["shen_sha_v0"] = "shen_sha_v0"
    status: ShenShaStatus
    hits: list[ShenShaHit] = Field(default_factory=list)
    notes: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class FinalUsefulGodDecisionBasis(StrictModel):
    method: Literal["controlled_useful_god_v0"] = "controlled_useful_god_v0"
    strength_label: StrengthLabel
    candidate_alignment: bool
    month_bias_alignment: bool
    distribution_alignment: bool
    conflict_detected: bool
    allowed_to_finalize: bool


class FinalUsefulGodOutput(StrictModel):
    status: FinalUsefulGodStatus
    confidence: FinalConfidence
    primary_element: FiveElement | None = None
    secondary_elements: list[FiveElement] = Field(default_factory=list)
    reason_chain: list[EvidenceNote] = Field(default_factory=list)
    blockers: list[EvidenceNote] = Field(default_factory=list)
    decision_basis: FinalUsefulGodDecisionBasis
    evidence_refs: list[str] = Field(min_length=1)


class RulesOutput(StrictModel):
    rules_version: str
    engine_version: str
    based_on_chart_version: str
    status: Literal["ok"] = "ok"
    day_master: str = Field(min_length=1, max_length=1)
    summary: str
    ten_gods: TenGodsOutput
    strength: StrengthOutput
    pattern_system_v1: PatternSystemOutput
    climate_balance_v0: ClimateBalanceOutput
    annual_flow_v0: AnnualFlowOutput
    annual_reading_v0: AnnualReadingOutput
    career_reading_v0: CareerReadingOutput
    wealth_reading_v0: WealthReadingOutput
    relationship_reading_v0: RelationshipReadingOutput
    shen_sha_v0: ShenShaOutput
    provisional_conclusions: ProvisionalConclusions
    final_useful_god_v0: FinalUsefulGodOutput


class ReportSummary(StrictModel):
    text: str
    evidence_refs: list[str] = Field(min_length=1)


class TenGodsSummary(StrictModel):
    day_master: str = Field(min_length=1, max_length=1)
    stems_visible: list[StemVisibleGod] = Field(min_length=4)
    branches_hidden: list[BranchHiddenStems] = Field(min_length=4)
    evidence_refs: list[str] = Field(min_length=1)


class StrengthSummary(StrictModel):
    score: int
    label: StrengthLabel
    summary: StrengthSummaryText
    evidence_refs: list[str] = Field(min_length=1)


class FinalUsefulGodSummary(StrictModel):
    status: FinalUsefulGodStatus
    confidence: FinalConfidence
    primary_element: FiveElement | None = None
    secondary_elements: list[FiveElement] = Field(default_factory=list)
    text: str
    evidence_refs: list[str] = Field(min_length=1)


class FutureFiveYearsEntry(StrictModel):
    year: int
    text: str
    evidence_refs: list[str] = Field(min_length=1)


class FutureFiveYearsOutput(StrictModel):
    overview: ReportSummary
    entries: list[FutureFiveYearsEntry] = Field(default_factory=list)
    evidence_refs: list[str] = Field(min_length=1)


class FinalReportOutput(StrictModel):
    method: Literal["final_report_v0"] = "final_report_v0"
    summary: ReportSummary
    career: ReportSummary
    wealth: ReportSummary
    relationship: ReportSummary
    future_five_years: FutureFiveYearsOutput
    limitations: list[EvidenceNote] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class ReportOutput(StrictModel):
    report_version: str
    engine_version: str
    rules_version: str
    status: Literal["ok"] = "ok"
    summary: ReportSummary
    ten_gods_summary: TenGodsSummary
    strength_summary: StrengthSummary
    pattern_system_summary: PatternSystemOutput
    climate_balance_summary: ClimateBalanceOutput
    annual_flow_summary: AnnualFlowOutput
    annual_reading_summary: AnnualReadingOutput
    career_reading_summary: CareerReadingOutput
    wealth_reading_summary: WealthReadingOutput
    relationship_reading_summary: RelationshipReadingOutput
    shen_sha_summary: ShenShaOutput
    candidate_elements_summary: ProvisionalConclusions
    final_useful_god_summary: FinalUsefulGodSummary
    final_report_v0: FinalReportOutput
    luck_cycle_summary: LuckCycleOutput
    caveats: list[EvidenceNote] = Field(min_length=1)


class AuditCheck(StrictModel):
    name: str
    passed: bool
    message: str


class AuditOutput(StrictModel):
    audit_version: str
    engine_version: str
    rules_version: str
    report_version: str
    passed: bool
    checks: list[AuditCheck] = Field(min_length=1)
