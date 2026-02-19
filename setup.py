from setuptools import find_packages, setup

setup(
    name="tailscale-stats",
    version="0.1.0",
    description="Collect and store Tailscale status statistics to Parquet files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Δ ǀ Ξ ȼ",
    author_email="alec@noser.net",
    url="https://github.com/a1ecbr0wn/tailscale-stats",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.5.0",
        "pyarrow>=10.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ts-status-stats=ts_status_stats.main:main",
        ],
    },
)
