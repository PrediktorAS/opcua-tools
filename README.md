# opcua-tools
Python/pandas-based tools for OPC UA information models.
OPC UA information models are represented and manipulated in Pandas Dataframes.
There is a parser from NodeSet2 XML files, functions for manipulating/extracting information from information models and a NodeSet2 generator.
There are some general tests here, but most of the testing is indirect through its use in [quarry](https://github.com/PrediktorAS/quarry) and other internal tools.
## Installation
To install the newest version, run this command:
```
pip install opcua-tools
```
## Usage
```python
from opcua_tools.ua_graph import UAGraph

graph = UAGraph.from_path("root/path/to/nodeset2/files")
# or
file_paths = ["path/to/nodeset2/file1.xml", "path/to/nodeset2/file2.xml"]
graph = UAGraph.from_file_list(file_paths)
```

This approach will also work:
```python
import opcua_tools as ot

graph = ot.UAGraph.from_path("root/path/to/nodeset2/files")
```

The `UAGraph` object is responsible to store information about the OPC UA information model.
You will find all the nodes and references in a form of pandas'DataFrames (`graph.nodes`
and `graph.references`).

## Development

### Requirements
The current version of library was mostly developed and tested with Python 3.12.
Create a virtual environment and install the requirements:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
in Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

The repo has some pre-commit hooks introduced. Remember to install them:
```bash
pre-commit install
```

### Running tests
To run the tests, you need to have `pytest` installed. You can install it using pip:
```bash
pip install pytest
```
Then, you can run the tests using the following command:
```bash
pytest tests/
```

### Releasing a new version
1. Create a Pull Request from your feature branch to main with the changes you
    want to release. Remember to update the version in `setup.py` file.
2. Merge the Pull Request.
3. Go to the "Releases" section of the repository - [here](https://github.com/PrediktorAS/opcua-tools/releases).
4. Click on "Draft a new release".
5. Click on the "Choose a tag" button and type the new version number - the one that corresponds with the one
    you wrote in the `setup.py` file, eg. (`v1.1.1`).
6. Click on the "Generate release notes" button. Alternatively, you can write a title and 
    description for the release.
7. Click on the "Publish release" button.
8. An automatic action will be triggered. The new version of the package should be available soon.
    You can find it on [PyPI](https://pypi.org/project/opcua-tools/#history).

## Logging

Throughout the package the python `logging` module is used for logging. The
logging module follows a "bubble up" strategy which means the logging message
will be available to the application using the package. In each file a
NullHandler is added as the Handler for logging. As this is a library (or package)
this is recommended from the authors of the logging package (see. [here](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library)). This means there is
no configuration for logging. If logging to console is desired this must be
setup in the application which uses this package.

There is no configuration needed to connect to this package. Simply setting up
logging within the application which uses this library, will cause the logs
within this package to appear. A basic logging configuration can be found in the
[documentation](https://docs.python.org/3/howto/logging.html) for the logging
module.



## License
The code in this repository is copyrighted to [TGS Prediktor AS](https://prediktor.com), and is licensed under the Apache 2.0 license. \
Exceptions apply to some of the test data and static files for parsing/generation (see document headers for license information).

Authors:
Magnus Bakken, Hans Petter Ladim, Olav Landmark Pedersen, Dawid Makar, Mikaeil Orfanian
