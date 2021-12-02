# OpenVAS XML Report Converter:

[* I'll look what these all mean later. just pasted from @thegroundzero/openvasreporting (tks)

[![GitHub version](https://badge.fury.io/gh/dudacgf%2Fovrgen.svg)](https://badge.fury.io/gh/dudacgf%2Fovrgen)
[![License](https://img.shields.io/github/license/dudacgf/ovrgen.svg)](https://github.com/dudacgf/ovrgen/blob/master/LICENSE)
[![Docs](https://readthedocs.org/projects/openvas-reporting/badge/?version=latest&style=flat)](https://openvas-reporting.sequr.be)
[![Known Vulnerabilities](https://snyk.io/test/github/dudacgf/ovrgen/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/dudacgf/ovrgen?targetFile=requirements.txt)
[![codecov](https://codecov.io/gh/dudacgf/ovrgen/branch/master/graph/badge.svg)](https://codecov.io/gh/dudacgf/ovrgen)
[![Requirements Status](https://requires.io/github/dudacgf/ovrgen/requirements.svg?branch=master)](https://requires.io/github/dudacgf/ovrgen/requirements/?branch=master)
[![PyPI - Version](https://img.shields.io/pypi/v/OpenVAS-Reporting.svg)](https://pypi.org/project/OpenVAS-Reporting/)
[![PyPI - Format](https://img.shields.io/pypi/format/OpenVAS-Reporting.svg)](https://pypi.org/project/OpenVAS-Reporting/)
*]

A Flask light webpage to help convert [OpenVAS](http://www.openvas.org/) XML into reports. Uses latest [OpenVAS Reporting](https://github.com/TheGroundZero/openvasreporting)

![Page example screenshot](docs/images/ovrgen-clean.png?raw=true)

Convert any OpenVAS XML Report into an Excel worksheet or a Word Document. You can specify filters like which networks are included (or excluded) in the report or which vulnerabilities or which CVES.

## Requirements (maybe others. complete list on requirements.txt)

 - [Python](https://www.python.org/) version 3.9x
 - [Flask](https://flask.palletsprojects.com/en/2.0.x)
 - [Flask-Session](https://flask-session.readthedocs.io/en/latest/)
 - [PyYAML](https://pyyaml.org/wiki/PyYAML)
 - [netaddr](https://netaddr.readthedocs.io/en/latest/api.html)
 - [defusedxml] (https://github.com/tiran/defusedxml)
 
 and, of course
 - [openvasreporting](https://openvas-reporting.sequr.be/en/latest/)

## Installing and running

    # Install Python3 and pip3
    apt(-get) install python3 python3-pip # Debian, Ubuntu
    yum -y install python3 python3-pip    # CentOS
    dnf install python3 python3-pip       # Fedora
    # Clone and Install openvareporting: 
    git clone https://github.com/TheGroundZero/openvasreporting.git
    cd openvasreporting
    pip3 install pip --upgrade
    pip3 install build --upgrade
    python -m build
    pip3 install dist/OpenVAS_Reporting-X.x.x-py3-xxxx-xxx.whl

    # Clone the repo (not bellow openvasreporting, please)
    cd ..
    git clone https://github.com/dudacgf/ovrgen.git
    cd ovrgen
    pip3 install -r requirements.txt
    
    # Run from localhost
    FLASK_APP=ovrgen-site flask run


*This package is not pip ready yet. Maybe never*

## Usage

    # Point your browser to http://localhost:5000 and have fun

## Filters

You can create text files to filter in or out Networks, Regexes or CVEs from the converted report. Take a look at the [openvasreporting](https://github.com/thegroundzero/openvasreporting) to find out how to use them.

After you inserted filters and uploaded your .xml reports, the web page will look like this:

![Page example screenshot](docs/images/ovrgen-screenshot.png?raw=true)

## Ideas

Some of the ideas I still have for future functionality:

 - make it run under apache or nginx 
 - detect if running in the same server as Greenbone Security Assistant to offer convert report directly from gvm using [python-gvm](https://github.com/greenbone/python-gvm).

