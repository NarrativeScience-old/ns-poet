# ns-poet
[![](https://img.shields.io/pypi/v/ns_poet.svg)](https://pypi.org/pypi/ns_poet/) [![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

Manage Poetry packages in a monorepo

Features:

- Generate Poetry package manifests
- Run a command in all packages

Table of Contents:

- [Installation](#installation)
- [Guide](#guide)
- [Development](#development)

## Installation

ns-poet requires Python 3.6 or above.

```bash
pip install ns-poet
# or
poetry add ns-poet
```

## Guide

<!-- Subsections explaining how to use the package -->

## Development

To develop ns-poet, install dependencies and enable the pre-commit hook:

```bash
pip install pre-commit poetry
poetry install
pre-commit install -t pre-commit -t pre-push
```

To run tests:

```bash
poetry run pytest
```
