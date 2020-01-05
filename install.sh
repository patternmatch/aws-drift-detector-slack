#!/usr/bin/env bash

if [ ! -d "venv" ]; then
    virtualenv venv
fi

source venv/bin/activate

pip install -r requirements-dev.txt
