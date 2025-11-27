#!/bin/bash

# PGAIView License Generator
# Wrapper script that calls the Python version

cd "$(dirname "$0")"
python3 generate_license_new.py "$@"

