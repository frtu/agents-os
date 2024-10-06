# Project - workflows-python

## About

Root folder to trigger resilient & durable workflow using [Temporal](https://temporal.io/) for [python](https://learn.temporal.io/getting_started/python/hello_world_in_python/)

## Instalation for Poetry command

[Install poetry](https://github.com/python-poetry/install.python-poetry.org?tab=readme-ov-file#usage)

```
curl -sSL https://install.python-poetry.org | python3 -
```

Check installation using `poetry --version`

## Workflow projects

### Create your new project (ONCE)

* Run `poetry new <PROJECT_NAME>`. Recommend to suffix your `PROJECT_NAME` with `-workflow` or `activity`
* Edit your `<PROJECT_NAME>/pyproject.toml` by adding `description` & `README.md`
* Add [temporalio](https://pypi.org/project/temporalio/) package to `pyproject.toml` :

```
temporalio = "^1.7.1"
```

### Install project

* Run `poetry config virtualenvs.in-project` to check `virtualenvs.create = true`. List [all configuration here](https://python-poetry.org/docs/configuration/#listing-the-current-configuration)
* Run `poetry install`

See more with https://medium.com/@mronakjain94/comprehensive-guide-to-installing-poetry-on-ubuntu-and-managing-python-projects-949b49ef4f76

### Develop your service

* Copy file `_templates_/run_worker.py` into your project
* [Build your python project](https://learn.temporal.io/getting_started/python/hello_world_in_python/)

### Start service

* Activate using `source $(poetry env info --path)/bin/activate`. [Manage environment using this link](https://python-poetry.org/docs/managing-environments/)
* Start service using `poetry run python run_worker.py`

## About

## Release notes

### 0.0.1-SNAPSHOT - Current version

* Initial version