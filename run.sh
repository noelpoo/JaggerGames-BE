#!/usr/bin/env bash
export PATH=/usr/bin:$PATH
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8

#install requirements
if [[ ! -d "venv" ]]; then
    virtualenv -p python3 venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt


# run test
echo "Micro service starts at $(date)"
python3 app.py



