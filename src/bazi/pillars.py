from __future__ import annotations

from .calendar_engine import build_calendar_context
from .models import BaziInput, CalendarContext, GanzhiPillar, Pillars


def _split_ganzhi(ganzhi: str) -> GanzhiPillar:
    if len(ganzhi) != 2:
        raise ValueError(f"Invalid ganzhi value: {ganzhi}")
    return GanzhiPillar(
        stem=ganzhi[0],
        branch=ganzhi[1],
        ganzhi=ganzhi,
    )


def calculate_pillars(context: CalendarContext) -> Pillars:
    return Pillars(
        year=_split_ganzhi(context.year_ganzhi),
        month=_split_ganzhi(context.month_ganzhi),
        day=_split_ganzhi(context.day_ganzhi),
        hour=_split_ganzhi(context.hour_ganzhi),
    )


def calculate_chart_context(data: BaziInput) -> CalendarContext:
    return build_calendar_context(data)


def extract_day_master(pillars: Pillars) -> str:
    return pillars.day.stem
