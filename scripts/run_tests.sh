#!/bin/bash

sudo apt-get install libgomp1
pip install tox -U
tox
