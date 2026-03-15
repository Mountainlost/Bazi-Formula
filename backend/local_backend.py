from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import zipfile


PROJECT_NAME = "bazi-formula"
PACKAGE_NAME = "bazi"
VERSION = "0.3.0"
SUMMARY = "Deterministic and auditable bazi project skeleton for Windows and Python 3.10"
REQUIRES_PYTHON = ">=3.10"
DEPENDENCIES = [
    "lunar_python>=1.4.8,<2",
    "pydantic>=2.7,<3",
    "PyYAML>=6,<7",
    "typer>=0.12,<0.13",
]
OPTIONAL_DEPENDENCIES = {
    "dev": [
        "pytest>=8,<9",
    ]
}
ENTRY_POINTS = {
    "console_scripts": [
        "bazi = bazi.cli:main",
    ]
}

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
PACKAGE_DIR = SRC_DIR / PACKAGE_NAME
DIST_NAME = PROJECT_NAME.replace("-", "_")
DIST_INFO = f"{DIST_NAME}-{VERSION}.dist-info"


def _metadata_text() -> str:
    lines = [
        "Metadata-Version: 2.1",
        f"Name: {PROJECT_NAME}",
        f"Version: {VERSION}",
        f"Summary: {SUMMARY}",
        f"Requires-Python: {REQUIRES_PYTHON}",
    ]
    for requirement in DEPENDENCIES:
        lines.append(f"Requires-Dist: {requirement}")
    for extra_name, extra_requirements in OPTIONAL_DEPENDENCIES.items():
        lines.append(f"Provides-Extra: {extra_name}")
        for requirement in extra_requirements:
            lines.append(f"Requires-Dist: {requirement}; extra == '{extra_name}'")
    return "\n".join(lines) + "\n"


def _wheel_text() -> str:
    return "\n".join(
        [
            "Wheel-Version: 1.0",
            "Generator: backend.local_backend",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        ]
    )


def _entry_points_text() -> str:
    lines: list[str] = []
    for section_name, entries in ENTRY_POINTS.items():
        lines.append(f"[{section_name}]")
        lines.extend(entries)
        lines.append("")
    return "\n".join(lines)


def _record_line(path: str, data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    hash_text = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"{path},sha256={hash_text},{len(data)}"


def _build_wheel_file(
    wheel_directory: str,
    file_map: dict[str, bytes],
) -> str:
    wheel_dir = Path(wheel_directory)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    wheel_name = f"{DIST_NAME}-{VERSION}-py3-none-any.whl"
    wheel_path = wheel_dir / wheel_name

    record_entries = [_record_line(path, data) for path, data in sorted(file_map.items())]
    record_entries.append(f"{DIST_INFO}/RECORD,,")
    record_content = "\n".join(record_entries) + "\n"

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in sorted(file_map.items()):
            archive.writestr(path, data)
        archive.writestr(f"{DIST_INFO}/RECORD", record_content.encode("utf-8"))

    return wheel_name


def _dist_info_file_map() -> dict[str, bytes]:
    return {
        f"{DIST_INFO}/METADATA": _metadata_text().encode("utf-8"),
        f"{DIST_INFO}/WHEEL": _wheel_text().encode("utf-8"),
        f"{DIST_INFO}/entry_points.txt": _entry_points_text().encode("utf-8"),
    }


def _package_file_map() -> dict[str, bytes]:
    file_map = _dist_info_file_map()
    for path in PACKAGE_DIR.rglob("*"):
        if path.is_file():
            relative_path = path.relative_to(SRC_DIR).as_posix()
            file_map[relative_path] = path.read_bytes()
    return file_map


def _editable_file_map() -> dict[str, bytes]:
    file_map = _dist_info_file_map()
    pth_name = f"{DIST_NAME}.pth"
    file_map[pth_name] = f"{SRC_DIR}\n".encode("utf-8")
    return file_map


def build_wheel(
    wheel_directory: str,
    config_settings: dict | None = None,
    metadata_directory: str | None = None,
) -> str:
    return _build_wheel_file(wheel_directory, _package_file_map())


def build_editable(
    wheel_directory: str,
    config_settings: dict | None = None,
    metadata_directory: str | None = None,
) -> str:
    return _build_wheel_file(wheel_directory, _editable_file_map())


def get_requires_for_build_wheel(config_settings: dict | None = None) -> list[str]:
    return []


def get_requires_for_build_editable(config_settings: dict | None = None) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict | None = None,
) -> str:
    target = Path(metadata_directory) / DIST_INFO
    target.mkdir(parents=True, exist_ok=True)
    for relative_path, data in _dist_info_file_map().items():
        name = Path(relative_path).name
        (target / name).write_bytes(data)
    return DIST_INFO


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict | None = None,
) -> str:
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)
