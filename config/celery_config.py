from .settings import settings

broker_url = f"amqp://{settings.RABBITMQ_USERNAME}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
result_backend = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Asia/Kolkata'
enable_utc = True

result_persistent = True
result_expires = 3600

worker_hijack_root_logger = False
worker_prefetch_multiplier = 1
task_acks_late = True

task_ignore_result = False
task_store_eager_result = True

task_track_started = True
task_send_sent_event = True

worker_concurrency = 4