from setuptools import find_packages, setup


setup(
    name="bazi-formula",
    version="0.3.0",
    description="Deterministic and auditable bazi project skeleton for Windows and Python 3.10",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "lunar_python>=1.4.8,<2",
        "pydantic>=2.7,<3",
        "PyYAML>=6,<7",
        "typer>=0.12,<0.13",
    ],
    extras_require={
        "dev": ["pytest>=8,<9"],
    },
    entry_points={
        "console_scripts": [
            "bazi=bazi.cli:main",
        ]
    },
)
