#!/bin/bash

# Vercel uses a uv-managed Python — override with --break-system-packages
pip install --break-system-packages -r requirements.txt

# Collect static files into the build output directory
export DJANGO_SETTINGS_MODULE=config.settings
python manage.py collectstatic --noinput --clear
