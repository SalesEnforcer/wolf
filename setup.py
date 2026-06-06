from setuptools import setup, find_packages

setup(
    name="wolf-agent",
    version="1.0.0-beta",
    description="Wolf - Google Maps SMB Lead Generator (Zero-Cost Edition)",
    author="Wolf Agent",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.40.0",
        "undetected-playwright>=0.0.6",
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
        "typer>=0.9.0",
        "textual>=0.41.0",
    ],
    entry_points={
        "console_scripts": [
            "wolf=wolf.cli:app",
        ],
    },
    python_requires=">=3.11",
)
