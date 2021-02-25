#!/usr/bin/env bash
export PATH=/usr/bin:$PATH
export LC_ALL=en_US.utf-8
export LANG=en_US.utf-8

#install requirements
if [[ ! -d "venv" ]]; then
    virtualenv -p python3 venv
fi
source venv/bin/activate
pip3 install --upgrade pip
pip3 install --upgrade -r requirements.txt


# run test
echo "Micro service starts at $(date)"
python app.py



