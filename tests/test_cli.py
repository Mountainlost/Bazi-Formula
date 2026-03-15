import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    src_path = str(ROOT / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = src_path if not existing else os.pathsep.join([src_path, existing])
    return env


def _write_input(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_cli_help_lists_commands() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "bazi.cli", "--help"],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    assert result.returncode == 0, result.stderr
    for command_name in ("calc", "judge", "report", "audit"):
        assert command_name in result.stdout


def test_calc_command_creates_chart_with_luck_cycle(tmp_path: Path) -> None:
    sample_input = json.loads((USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"))
    input_path = tmp_path / "user_001.json"
    chart_path = tmp_path / "chart.json"
    _write_input(input_path, sample_input)

    result = subprocess.run(
        [sys.executable, "-m", "bazi.cli", "calc", "--input", str(input_path), "--output", str(chart_path)],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    assert result.returncode == 0, result.stderr
    chart = json.loads(chart_path.read_text(encoding="utf-8"))
    assert chart["engine_version"] == "bazi-engine-real-calc-py310-v2"
    assert chart["status"] == "ok"
    assert chart["pillars"]["year"]["ganzhi"] == "乙亥"
    assert chart["pillars"]["month"]["ganzhi"] == "丁亥"
    assert chart["pillars"]["day"]["ganzhi"] == "辛亥"
    assert chart["pillars"]["hour"]["ganzhi"] == "甲午"
    assert chart["luck_cycle"]["direction"] == "backward"
    assert chart["luck_cycle"]["start_age"] == 2.8
    assert [item["ganzhi"] for item in chart["luck_cycle"]["cycles"][:3]] == ["丙戌", "乙酉", "甲申"]


def test_calc_supports_lunar_input_v0(tmp_path: Path) -> None:
    sample_input = json.loads((USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"))
    sample_input["calendar_type"] = "lunar"
    sample_input["birth_date"] = "1998-06-21"
    input_path = tmp_path / "user_lunar.json"
    chart_path = tmp_path / "chart_lunar.json"
    _write_input(input_path, sample_input)

    result = subprocess.run(
        [sys.executable, "-m", "bazi.cli", "calc", "--input", str(input_path), "--output", str(chart_path)],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    assert result.returncode == 0, result.stderr
    chart = json.loads(chart_path.read_text(encoding="utf-8"))
    assert chart["input_snapshot"]["calendar_type"] == "lunar"
    assert chart["solar_datetime"] == "1998-08-12T12:30:00+08:00"
    assert chart["pillars"]["year"]["ganzhi"] == "戊寅"
    assert chart["pillars"]["month"]["ganzhi"] == "庚申"
    assert chart["pillars"]["day"]["ganzhi"] == "辛卯"
    assert chart["pillars"]["hour"]["ganzhi"] == "甲午"
    assert chart["calc_basis"]["normalization_steps"][0]["name"] == "lunar_to_solar"


def test_calc_supports_true_solar_time_v0(tmp_path: Path) -> None:
    standard_input = json.loads((USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"))
    standard_input["birth_place"] = "Urumqi"
    standard_input["birth_time"] = "23:30"

    true_solar_input = dict(standard_input)
    true_solar_input["true_solar_time"] = True

    standard_input_path = tmp_path / "user_standard.json"
    true_solar_input_path = tmp_path / "user_true_solar.json"
    standard_chart_path = tmp_path / "chart_standard.json"
    true_solar_chart_path = tmp_path / "chart_true_solar.json"
    _write_input(standard_input_path, standard_input)
    _write_input(true_solar_input_path, true_solar_input)

    standard_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bazi.cli",
            "calc",
            "--input",
            str(standard_input_path),
            "--output",
            str(standard_chart_path),
        ],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    true_solar_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bazi.cli",
            "calc",
            "--input",
            str(true_solar_input_path),
            "--output",
            str(true_solar_chart_path),
        ],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    assert standard_result.returncode == 0, standard_result.stderr
    assert true_solar_result.returncode == 0, true_solar_result.stderr

    standard_chart = json.loads(standard_chart_path.read_text(encoding="utf-8"))
    true_solar_chart = json.loads(true_solar_chart_path.read_text(encoding="utf-8"))
    assert standard_chart["solar_datetime"] == "1995-11-16T23:30:00+08:00"
    assert true_solar_chart["solar_datetime"] == "1995-11-16T21:34:59+08:00"
    assert true_solar_chart["calc_basis"]["true_solar_time"] is True
    assert true_solar_chart["calc_basis"]["normalization_steps"][0]["name"] == "true_solar_time_adjustment"
    assert standard_chart["pillars"]["hour"]["ganzhi"] != true_solar_chart["pillars"]["hour"]["ganzhi"]


def test_calc_supports_non_shanghai_timezone_v0(tmp_path: Path) -> None:
    sample_input = json.loads((USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"))
    sample_input["birth_place"] = "Tokyo"
    sample_input["timezone"] = "Asia/Tokyo"
    input_path = tmp_path / "user_tokyo.json"
    chart_path = tmp_path / "chart_tokyo.json"
    _write_input(input_path, sample_input)

    result = subprocess.run(
        [sys.executable, "-m", "bazi.cli", "calc", "--input", str(input_path), "--output", str(chart_path)],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    assert result.returncode == 0, result.stderr
    chart = json.loads(chart_path.read_text(encoding="utf-8"))
    assert chart["calc_basis"]["timezone"] == "Asia/Tokyo"
    assert chart["solar_datetime"].endswith("+09:00")
    assert chart["luck_cycle"]["start_datetime"].endswith("+09:00")


def test_calc_rejects_unsupported_timezone(tmp_path: Path) -> None:
    sample_input = json.loads((USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"))
    sample_input["timezone"] = "Europe/London"
    input_path = tmp_path / "user_unsupported_timezone.json"
    _write_input(input_path, sample_input)

    result = subprocess.run(
        [sys.executable, "-m", "bazi.cli", "calc", "--input", str(input_path)],
        cwd=ROOT,
        env=_subprocess_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    assert result.returncode == 1
    assert "Unsupported timezone 'Europe/London'" in result.stderr
