# Copyright 2021 Prediktor AS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pathlib

from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="opcua-tools",
    version="1.7.2",
    description="OPCUA Tools for Python using Pandas DataFrames",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/PrediktorAS/opcua-tools",
    author="TGS Prediktor AS",
    author_email="dawid.makar@tgs.com",
    license="Apache License 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    packages=["opcua_tools", "opcua_tools.validator", "opcua_tools.json_parser"],
    include_package_data=True,
    install_requires=[
        "lxml>=5.3.0",
        "lxml<6.0",
        "xmltodict>=0.14.2",
        "pandas>=2.0.0",
        "pandas<2.2.0",
        "scipy>=1.14.1",
        "scipy<2.0",
    ],
)
