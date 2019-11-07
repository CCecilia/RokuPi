# RokuPi
A pip package for helping with Roku development.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [Python3.X](https://www.python.org/downloads/)
* [Pip](https://pip.pypa.io/en/stable/installing/)


### Installing

A step by step series of examples that tell you how to get a development env running

Clone Repo

```shell script
git clone https://github.com/CCecilia/RokuPi.git
```

Create Virtualenv

```shell script
python3 -m venv {path/to/rokuPi}
```

Make rokuPi your current working directory

```shell script
cd {path/to/rokuPi}
```

Activate Virtual environment, you should see (rokuPi) after

```shell script
source bin/activate
```

Install dependencies

```shell script
pip install -r requirements.txt
```

Install rokuPi as pip module

```shell script
pip install --editable .
```

## Running the tests

```shell script
python3 -m unittest
```

### And coding style tests

All coding styles should strictly follow [PEP8](https://www.python.org/dev/peps/pep-0008/) guidelines.

## Built With

* [Click](https://palletsprojects.com/p/click/) - The cli framework used

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Christian Cecilia** - *Initial work* - [GH](https://github.com/CCecilia/)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
