#!/bin/bash

echo "Clean up"

# package build artefacts
rm -rvf *.egg-info dist/ build/

# linter and test outputs
rm -rvf .mypy_cache test_output

# coverage report
rm -vf ./.coverage ./coverage.svg
rm -rvf htmlcov