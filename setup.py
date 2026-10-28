from setuptools import setup, find_packages

setup(
    name="evocore",
    version="0.3.0",
    packages=find_packages(include=["evocore*"]),
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "evocore = evocore.cli:main",
        ],
    },
)
