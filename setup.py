from setuptools import setup, find_packages

setup(
    name="enclose-engine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pulp",
    ],
    entry_points={
        "console_scripts": [
            "enclose-engine=enclose_engine.cli:main",
        ],
    },
)
