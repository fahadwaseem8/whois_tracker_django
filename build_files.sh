#!/bin/bash

# Install dependencies (Vercel runs this during the static build phase)
pip install -r requirements.txt

# Collect static files into the build output directory
python manage.py collectstatic --noinput --clear
