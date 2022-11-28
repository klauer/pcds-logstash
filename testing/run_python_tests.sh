#!/bin/bash

SCRIPT_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
cd "${SCRIPT_PATH}" || exit 1

echo -e "\n* Installing test dependencies..."

set -xe

python -m pip install --upgrade pip
python -m pip install --requirement requirements.txt

timeout 100 make test
