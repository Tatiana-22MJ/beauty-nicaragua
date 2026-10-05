"""Configuración de gunicorn.

Lee el puerto directo del entorno con Python: no depende de que una shell
expanda $PORT, así funciona igual en Docker, Procfile, Railway o Render.
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = 4
timeout = 60
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
