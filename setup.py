"""Setup script for Context Engine"""
from setuptools import setup, find_packages
from pathlib import Path

# Read requirements from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
with open(requirements_file) as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#") and not line.startswith("--")
    ]

# Separate dev requirements
dev_requirements = [
    req for req in requirements if any(pkg in req for pkg in ["pytest", "black", "flake8", "mypy"])
]
install_requirements = [req for req in requirements if req not in dev_requirements]

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
with open(readme_file, encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="context-engine",
    version="0.1.0",
    description="Lightweight, intelligent context awareness for AI workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Claude 2.0",
    author_email="noreply@anthropic.com",
    url="https://github.com/RMSTrucks/context-engine",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=install_requirements,
    extras_require={
        "dev": dev_requirements,
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "context-engine=mcp_servers.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="context-awareness mcp ai assistant vision audio transcription",
    project_urls={
        "Bug Reports": "https://github.com/RMSTrucks/context-engine/issues",
        "Source": "https://github.com/RMSTrucks/context-engine",
    },
)
