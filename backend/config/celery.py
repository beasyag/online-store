import os
from celery import Celery

# Задаем настройки по умолчанию для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('marketflow')

# Читаем настройки из settings.py, где ключи начинаются с CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи (tasks.py) во всех установленных приложениях
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
