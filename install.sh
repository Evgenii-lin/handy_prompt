#!/bin/bash

echo "--- Download Project ---"
curl -L https://github.com/Evgenii-lin/handy_prompt.zip" | tar -xz
cd *handy*

echo "--- Creating virtual environment ---"
python3 -m venv venv
source venv/bin/activate

echo "--- Installing ---"
pip install --upgrade pip
pip install -r requirements.txt

echo "--- Configuring ---"
python manage.py migrate

echo "--- Launching ---"
python manage.py runserver
