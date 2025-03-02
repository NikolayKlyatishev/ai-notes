#!/usr/bin/env python
"""
Настройка для установки пакета через pip.
"""
from setuptools import setup, find_packages
import os

# Чтение requirements.txt
with open('backend/requirements.txt') as f:
    requirements = f.read().splitlines()

# Чтение README_USAGE.md для long_description
with open('README_USAGE.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="ai-notes",
    version="0.1.0",
    description="Система автоматической фиксации разговоров",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/ai-notes",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    entry_points={
        "console_scripts": [
            "ai-notes-recorder=backend.recorder:main",
            "ai-notes-webapp=backend.web_app:run_web_app",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["frontend/templates/*.html", "frontend/static/css/*.css"],
    },
) 