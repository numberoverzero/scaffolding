from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="scaffolding",
        version="1.0",
        author="Joe Cross",
        url="https://github.com/numberoverzero/scaffolding",
        include_package_data=True,
        packages=find_packages(exclude=("docs", "examples", "scripts", "tests")),
        install_requires=[
            "alembic~=1.0",
            "argon2_cffi~=18.0",
            "bloop~=2.2",
            "cryptography~=2.3",
            "falcon~=1.0",
            "pendulum~=2.0",
        ],
    )
