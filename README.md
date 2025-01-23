# opcua-tools
Python/pandas-based tools for OPC UA information models.
OPC UA information models are represented and manipulated in Pandas Dataframes.
There is a parser from NodeSet2 XML files, functions for manipulating/extracting information from information models and a NodeSet2 generator.
There are some general tests here, but most of the testing is indirect through its use in [quarry](https://github.com/PrediktorAS/quarry) and other internal tools.
## Installation
To install, run this command:
```
pip install git+https://github.com/PrediktorAS/opcua-tools.git
```
## Usage
Forthcoming... see the test cases.

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
Magnus Bakken, Hans Petter Ladim, Olav Landmark Pedersen, [Dawid Makar](mailto:dawid.makar@tgs.com), Mikaeil Orfanian
