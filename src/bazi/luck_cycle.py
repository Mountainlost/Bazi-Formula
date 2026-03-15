from __future__ import annotations

from datetime import datetime

from lunar_python import Solar

from .calendar_engine import UnsupportedCalcInputError
from .models import BaziInput, LuckCycleBasis, LuckCycleEntry, LuckCycleOutput, Pillars
from .ten_gods import get_stem_polarity

LIBRARY_NAME = "lunar_python"
DIRECTION_RULE = "year_stem_polarity_with_gender: yang_male_or_yin_female_forward_else_backward"
START_AGE_RULE = "sect_1_conversion: 3_days_1_year, 1_day_4_months, 1_shichen_10_days"
JIEQI_ANCHOR_RULE = "forward_next_jie_backward_previous_jie"
YUN_SECT = 1


def _gender_to_yun_flag(gender: str) -> int:
    if gender == "male":
        return 1
    if gender == "female":
        return 0
    raise UnsupportedCalcInputError("luck_cycle requires gender to be male or female in this phase.")


def _expected_direction(year_stem: str, gender: str) -> str:
    polarity = get_stem_polarity(year_stem)
    is_forward = (polarity == "yang" and gender == "male") or (
        polarity == "yin" and gender == "female"
    )
    return "forward" if is_forward else "backward"


def _decimal_age(years: int, months: int, days: int, hours: int) -> float:
    value = years + (months / 12) + (days / 365) + (hours / (24 * 365))
    return round(value, 1)


def calculate_luck_cycle(
    data: BaziInput,
    solar_datetime: str,
    pillars: Pillars,
) -> LuckCycleOutput:
    birth_dt = datetime.fromisoformat(solar_datetime)
    birth_tzinfo = birth_dt.tzinfo
    solar = Solar.fromYmdHms(
        birth_dt.year,
        birth_dt.month,
        birth_dt.day,
        birth_dt.hour,
        birth_dt.minute,
        birth_dt.second,
    )
    eight_char = solar.getLunar().getEightChar()
    yun = eight_char.getYun(_gender_to_yun_flag(data.gender), YUN_SECT)

    direction = "forward" if yun.isForward() else "backward"
    expected_direction = _expected_direction(pillars.year.stem, data.gender)
    if direction != expected_direction:
        raise ValueError("luck_cycle direction is inconsistent with the configured direction rule.")

    start_age = _decimal_age(
        yun.getStartYear(),
        yun.getStartMonth(),
        yun.getStartDay(),
        yun.getStartHour(),
    )
    start_datetime = datetime.strptime(
        yun.getStartSolar().toYmdHms(),
        "%Y-%m-%d %H:%M:%S",
    ).replace(tzinfo=birth_tzinfo).isoformat(timespec="seconds")

    dayun_entries = yun.getDaYun(11)
    cycles: list[LuckCycleEntry] = []
    for item in dayun_entries[1:11]:
        ganzhi = item.getGanZhi()
        cycles.append(
            LuckCycleEntry(
                index=item.getIndex(),
                ganzhi=ganzhi,
                stem=ganzhi[0],
                branch=ganzhi[1],
                start_age=round(start_age + ((item.getIndex() - 1) * 10), 1),
                end_age=round(start_age + (item.getIndex() * 10), 1),
                start_year=int(item.getStartYear()),
                end_year=int(item.getStartYear()) + 10,
                evidence_refs=["E207", "E209"],
            )
        )

    return LuckCycleOutput(
        basis=LuckCycleBasis(
            direction_rule=DIRECTION_RULE,
            start_age_rule=START_AGE_RULE,
            jieqi_anchor_rule=JIEQI_ANCHOR_RULE,
            library_name=LIBRARY_NAME,
            enabled=True,
        ),
        direction=direction,
        start_age=start_age,
        start_datetime=start_datetime,
        cycles=cycles,
        evidence_refs=["E207", "E208", "E209"],
    )
