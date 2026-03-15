from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .calendar_engine import UnsupportedCalcInputError
from .judge_engine import build_rules_output
from .luck_cycle import calculate_luck_cycle
from .models import AuditOutput, BaziInput, ChartOutput, ReportOutput, RulesOutput
from .pillars import calculate_chart_context, calculate_pillars, extract_day_master
from .reporter import build_report, export_final_markdown
from .verifier import audit_outputs


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run_calc(input_path: Path, output_path: Path) -> ChartOutput:
    from . import ENGINE_VERSION

    raw = _read_json(input_path)
    payload = BaziInput.model_validate(raw)
    context = calculate_chart_context(payload)
    pillars = calculate_pillars(context)
    luck_cycle = calculate_luck_cycle(payload, context.solar_datetime, pillars)

    chart = ChartOutput(
        engine_version=ENGINE_VERSION,
        school=payload.school,
        calc_basis=context.calc_basis,
        input_snapshot=context.input_snapshot,
        solar_datetime=context.solar_datetime,
        pillars=pillars,
        day_master=extract_day_master(pillars),
        luck_cycle=luck_cycle,
        status="ok",
    )
    _write_json(output_path, chart.model_dump(exclude_none=True))
    return chart


def run_judge(chart_path: Path, output_path: Path) -> RulesOutput:
    chart = ChartOutput.model_validate(_read_json(chart_path))
    rules = build_rules_output(chart)
    _write_json(output_path, rules.model_dump())
    return rules


def run_report(chart_path: Path, rules_path: Path, output_path: Path) -> ReportOutput:
    chart = ChartOutput.model_validate(_read_json(chart_path))
    rules = RulesOutput.model_validate(_read_json(rules_path))
    if chart.engine_version != rules.engine_version:
        raise ValueError("chart.json and rules.json must share the same engine_version.")
    report = build_report(chart, rules)
    _write_json(output_path, report.model_dump())
    export_final_markdown(chart, report, output_path.parent / "最终报告.md")
    return report


def run_audit(
    chart_path: Path,
    rules_path: Path,
    report_path: Path,
    output_path: Path,
) -> AuditOutput:
    chart_raw = _read_json(chart_path)
    rules_raw = _read_json(rules_path)
    report_raw = _read_json(report_path)
    audit = audit_outputs(
        chart_raw=chart_raw,
        rules_raw=rules_raw,
        report_raw=report_raw,
        chart_exists=chart_path.exists(),
        rules_exists=rules_path.exists(),
        report_exists=report_path.exists(),
    )
    _write_json(output_path, audit.model_dump())
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic bazi skeleton CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    calc_parser = subparsers.add_parser("calc", help="Generate chart.json from input JSON.")
    calc_parser.add_argument("--input", dest="input_path", required=True)
    calc_parser.add_argument("--output", dest="output_path", default="输出结果/chart.json")

    judge_parser = subparsers.add_parser("judge", help="Generate rules.json from chart.json.")
    judge_parser.add_argument("--chart", dest="chart_path", required=True)
    judge_parser.add_argument("--output", dest="output_path", default="输出结果/rules.json")

    report_parser = subparsers.add_parser(
        "report",
        help="Generate report.json from chart.json and rules.json.",
    )
    report_parser.add_argument("--chart", dest="chart_path", required=True)
    report_parser.add_argument("--rules", dest="rules_path", required=True)
    report_parser.add_argument("--output", dest="output_path", default="输出结果/report.json")

    audit_parser = subparsers.add_parser(
        "audit",
        help="Generate audit.json from chart.json, rules.json, and report.json.",
    )
    audit_parser.add_argument("--chart", dest="chart_path", required=True)
    audit_parser.add_argument("--rules", dest="rules_path", required=True)
    audit_parser.add_argument("--report", dest="report_path", required=True)
    audit_parser.add_argument("--output", dest="output_path", default="输出结果/audit.json")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "calc":
            run_calc(Path(args.input_path), Path(args.output_path))
            print(f"Wrote {args.output_path}")
            return 0
        if args.command == "judge":
            run_judge(Path(args.chart_path), Path(args.output_path))
            print(f"Wrote {args.output_path}")
            return 0
        if args.command == "report":
            run_report(Path(args.chart_path), Path(args.rules_path), Path(args.output_path))
            print(f"Wrote {args.output_path}")
            return 0
        if args.command == "audit":
            run_audit(
                Path(args.chart_path),
                Path(args.rules_path),
                Path(args.report_path),
                Path(args.output_path),
            )
            print(f"Wrote {args.output_path}")
            return 0
    except UnsupportedCalcInputError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
