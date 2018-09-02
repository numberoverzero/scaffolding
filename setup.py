import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "requirements.txt"), "r") as f:
    requirements = [
        line.strip()
        for line in f.readlines()
        if line.strip()
    ]

if __name__ == "__main__":
    setup(
        name="scaffolding",
        version="1.0",
        author="Joe Cross",
        url="https://github.com/numberoverzero/scaffolding",
        include_package_data=True,
        packages=find_packages(exclude=("docs", "examples", "scripts", "tests")),
        install_requires=requirements,
    )
