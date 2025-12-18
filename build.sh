#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo "📦 Collecting static files..."
python manage.py collectstatic --no-input

echo "🗄️  Running migrations..."
python manage.py migrate

echo "🚀 Running production setup..."
python manage.py setup_production

echo "🌐 Updating domain..."
python manage.py update_domain

echo "✅ Build completed successfully!"