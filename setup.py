import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="opcua-tools",
    version="0.0.23",
    description="OPCUA Tools for Python using Pandas DataFrames",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/mbapred/opcua-tools",
    author="Magnus Bakken",
    author_email="mba@prediktor.com",
    license="Apache License 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["opcua_tools"],
    include_package_data=True,
    install_requires=[
        "lxml>=4.6.2", "lxml<5.0",
        "pandas>=1.2.2", "pandas<2.0",
        "scipy>=1.6.1", "scipy<2.0",
    ]
)