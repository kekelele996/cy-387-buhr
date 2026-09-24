#!/bin/sh
set -e

# 启动前自动应用迁移（含演示合同种子数据）
python manage.py migrate --noinput

exec gunicorn app.wsgi:application --bind 0.0.0.0:8000
