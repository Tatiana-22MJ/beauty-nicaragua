web: gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 3 --threads 2 --timeout 60 app:app
worker: celery -A tasks worker --loglevel=info
