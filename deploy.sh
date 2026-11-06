#!/bin/bash

# Остановка скрипта при ошибке
set -e

echo "Обновление проекта"
git pull origin master

echo "Активация виртуального окружения"
source .venv/bin/activate

echo "Установка библиотек Python"
pip install -r requirements.txt

echo "Установка библиотек Node.js"
npm ci

echo "Пересборка ноды"
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

echo "Пересборка статики"
python3 manage.py collectstatic --noinput

echo "Обновление полей бд"
python3 manage.py migrate --noinput

echo "Перезапуск юнита"
systemctl restart star-burger.service

echo "Обновление конфигурации nginx"
systemctl reload nginx.service

echo "Обновление проекта завершено"
