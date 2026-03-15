from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
from typing import Any

from importlib.metadata import version
from lunar_python import Lunar, LunarYear, Solar
import yaml

from .models import BaziInput, CalcBasis, CalcNormalizationStep, CalendarContext, InputSnapshot

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_NORMALIZATION_CONFIG = REPO_ROOT / "configs" / "input_normalization.yaml"
SUPPORTED_INPUT_SCOPE = "wide_input_v0"
LIBRARY_NAME = "lunar_python"
MONTH_RULE = "jieqi"
DAY_RULE = "sect_2"


class UnsupportedCalcInputError(ValueError):
    pass


@lru_cache(maxsize=1)
def _load_input_normalization_config() -> dict[str, Any]:
    with INPUT_NORMALIZATION_CONFIG.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("configs/input_normalization.yaml must contain a mapping object.")
    return data


def _supported_year_range() -> tuple[int, int]:
    config = _load_input_normalization_config()
    raw_range = config.get("supported_year_range", {})
    min_year = int(raw_range.get("min", 1900))
    max_year = int(raw_range.get("max", 2099))
    return min_year, max_year


def _validate_year_range(date_value: str) -> None:
    year = int(date_value[:4])
    min_year, max_year = _supported_year_range()
    if min_year <= year <= max_year:
        return
    raise UnsupportedCalcInputError(
        f"{SUPPORTED_INPUT_SCOPE} supports years {min_year}-{max_year}; got {year}."
    )


def _supported_timezones() -> dict[str, dict[str, Any]]:
    config = _load_input_normalization_config()
    timezones = config.get("supported_timezones", {})
    if not isinstance(timezones, dict):
        raise ValueError("configs/input_normalization.yaml must define supported_timezones.")
    return timezones


def _birth_place_map() -> dict[str, dict[str, Any]]:
    config = _load_input_normalization_config()
    raw_places = config.get("true_solar_time", {}).get("supported_birth_places", {})
    if not isinstance(raw_places, dict):
        raise ValueError(
            "configs/input_normalization.yaml must define true_solar_time.supported_birth_places."
        )
    return raw_places


def _get_timezone_config(timezone_name: str) -> dict[str, Any]:
    supported = _supported_timezones()
    timezone_config = supported.get(timezone_name)
    if timezone_config is not None:
        return timezone_config

    supported_names = ", ".join(sorted(supported))
    raise UnsupportedCalcInputError(
        f"Unsupported timezone '{timezone_name}'. {SUPPORTED_INPUT_SCOPE} supports only: {supported_names}."
    )


def _get_birth_place_config(birth_place: str) -> dict[str, Any]:
    place_config = _birth_place_map().get(birth_place)
    if place_config is not None:
        return place_config

    supported_names = ", ".join(sorted(_birth_place_map()))
    raise UnsupportedCalcInputError(
        "true_solar_time=true requires birth_place to use a configured longitude whitelist. "
        f"Supported places: {supported_names}."
    )


def _get_fixed_timezone(timezone_name: str) -> timezone:
    timezone_config = _get_timezone_config(timezone_name)
    offset_minutes = int(timezone_config["utc_offset_minutes"])
    return timezone(timedelta(minutes=offset_minutes))


def _localize(naive_datetime: datetime, timezone_name: str) -> datetime:
    return naive_datetime.replace(tzinfo=_get_fixed_timezone(timezone_name))


def _to_isoformat(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _round_to_second(dt: datetime) -> datetime:
    if dt.microsecond >= 500_000:
        dt += timedelta(seconds=1)
    return dt.replace(microsecond=0)


def _build_lunar_to_solar_step(
    input_datetime: datetime,
    output_datetime: datetime,
) -> CalcNormalizationStep:
    return CalcNormalizationStep(
        name="lunar_to_solar",
        input_value=_to_isoformat(input_datetime),
        output_value=_to_isoformat(output_datetime),
        evidence_refs=["E211"],
    )


def _build_true_solar_time_step(
    input_datetime: datetime,
    output_datetime: datetime,
) -> CalcNormalizationStep:
    return CalcNormalizationStep(
        name="true_solar_time_adjustment",
        input_value=_to_isoformat(input_datetime),
        output_value=_to_isoformat(output_datetime),
        evidence_refs=["E213", "E214"],
    )


def _parse_birth_datetime(data: BaziInput) -> datetime:
    _validate_year_range(data.birth_date)
    try:
        return datetime.strptime(
            f"{data.birth_date} {data.birth_time}",
            "%Y-%m-%d %H:%M",
        )
    except ValueError as exc:
        raise UnsupportedCalcInputError(f"Invalid birth_date/birth_time: {exc}") from exc


def _convert_lunar_to_solar(data: BaziInput, base_datetime: datetime) -> tuple[datetime, CalcNormalizationStep]:
    lunar_year = base_datetime.year
    lunar_month = base_datetime.month
    lunar_day = base_datetime.day
    leap_month = LunarYear.fromYear(lunar_year).getLeapMonth()
    if leap_month == lunar_month:
        raise UnsupportedCalcInputError(
            "lunar input is ambiguous for leap-month years because this repository does not "
            "accept an explicit leap-month marker in birth_date."
        )

    try:
        solar = Lunar.fromYmdHms(
            lunar_year,
            lunar_month,
            lunar_day,
            base_datetime.hour,
            base_datetime.minute,
            base_datetime.second,
        ).getSolar()
    except Exception as exc:  # noqa: BLE001
        raise UnsupportedCalcInputError(f"Unsupported lunar input: {exc}") from exc

    solar_datetime = datetime(
        solar.getYear(),
        solar.getMonth(),
        solar.getDay(),
        solar.getHour(),
        solar.getMinute(),
        solar.getSecond(),
    )
    input_local = _localize(base_datetime, data.timezone)
    output_local = _localize(solar_datetime, data.timezone)
    return solar_datetime, _build_lunar_to_solar_step(input_local, output_local)


def _equation_of_time_minutes(day_of_year: int) -> float:
    base_angle = 2 * pi * (day_of_year - 81) / 364
    return 9.87 * sin(2 * base_angle) - 7.53 * cos(base_angle) - 1.5 * sin(base_angle)


def _apply_true_solar_time(data: BaziInput, solar_datetime: datetime) -> tuple[datetime, CalcNormalizationStep]:
    place_config = _get_birth_place_config(data.birth_place)
    if place_config["timezone"] != data.timezone:
        raise UnsupportedCalcInputError(
            f"birth_place '{data.birth_place}' is mapped to timezone "
            f"'{place_config['timezone']}', not '{data.timezone}'."
        )

    timezone_config = _get_timezone_config(data.timezone)
    longitude = float(place_config["longitude"])
    standard_meridian = float(timezone_config["standard_meridian"])
    longitude_minutes = 4 * (longitude - standard_meridian)
    equation_of_time = _equation_of_time_minutes(solar_datetime.timetuple().tm_yday)
    correction_seconds = round((longitude_minutes + equation_of_time) * 60)
    corrected_datetime = _round_to_second(
        solar_datetime + timedelta(seconds=correction_seconds)
    )
    return corrected_datetime, _build_true_solar_time_step(solar_datetime, corrected_datetime)


def parse_solar_datetime(data: BaziInput) -> tuple[datetime, list[CalcNormalizationStep] | None]:
    if data.calendar_type not in {"solar", "lunar"}:
        raise UnsupportedCalcInputError(
            f"Unsupported calendar_type '{data.calendar_type}'."
        )
    _get_timezone_config(data.timezone)

    base_datetime = _parse_birth_datetime(data)
    normalization_steps: list[CalcNormalizationStep] = []
    solar_datetime = base_datetime
    if data.calendar_type == "lunar":
        solar_datetime, lunar_step = _convert_lunar_to_solar(data, base_datetime)
        normalization_steps.append(lunar_step)

    localized_solar_datetime = _localize(solar_datetime, data.timezone)
    if data.true_solar_time:
        localized_solar_datetime, true_solar_step = _apply_true_solar_time(
            data,
            localized_solar_datetime,
        )
        normalization_steps.append(true_solar_step)

    return localized_solar_datetime, normalization_steps or None


def build_calendar_context(data: BaziInput) -> CalendarContext:
    solar_datetime, normalization_steps = parse_solar_datetime(data)
    solar = Solar.fromYmdHms(
        solar_datetime.year,
        solar_datetime.month,
        solar_datetime.day,
        solar_datetime.hour,
        solar_datetime.minute,
        solar_datetime.second,
    )
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()
    eight_char.setSect(2)

    return CalendarContext(
        calc_basis=CalcBasis(
            calendar_type="solar",
            timezone=data.timezone,
            true_solar_time=data.true_solar_time,
            real_calendar=True,
            month_rule=MONTH_RULE,
            day_rule=DAY_RULE,
            library_name=LIBRARY_NAME,
            normalization_steps=normalization_steps,
        ),
        input_snapshot=InputSnapshot(
            birth_date=data.birth_date,
            birth_time=data.birth_time,
            birth_place=data.birth_place,
            gender=data.gender,
            calendar_type=data.calendar_type,
            timezone=data.timezone,
            true_solar_time=data.true_solar_time,
            school=data.school,
        ),
        solar_datetime=_to_isoformat(solar_datetime),
        year_ganzhi=eight_char.getYear(),
        month_ganzhi=eight_char.getMonth(),
        day_ganzhi=eight_char.getDay(),
        hour_ganzhi=eight_char.getTime(),
    )


def get_library_name() -> str:
    return LIBRARY_NAME


def get_library_version() -> str:
    return version(LIBRARY_NAME)
