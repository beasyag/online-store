from celery import shared_task
import time

@shared_task
def process_order_notifications(order_id, user_email):
    """
    Пример фоновой задачи: отправка уведомлений о заказе.
    В реальном проекте здесь будет интеграция с email-сервисом.
    """
    # Имитируем долгую работу (например, отправку письма)
    time.sleep(3)
    
    print(f"[CELERY] Письмо с чеком для заказа #{order_id} успешно отправлено на {user_email}!")
    
    return f"Заказ {order_id} обработан"
