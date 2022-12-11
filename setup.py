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
    version="0.0.81",
    description="OPCUA Tools for Python using Pandas DataFrames",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/PrediktorAS/opcua-tools",
    author="Magnus Bakken",
    author_email="olav.pedersen@prediktor.com",
    license="Apache License 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["opcua_tools"],
    include_package_data=True,
    install_requires=[
        "lxml>=4.6.2",
        "lxml<5.0",
        "xmltodict>=0.12.0",
        "pytest>=6.2.5",
        "pandas>=1.2.2",
        "pandas<1.5.0",
        "scipy>=1.6.1",
        "scipy<2.0",
    ],
)
