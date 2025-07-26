import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import django
import psutil
import requests
from django.conf import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("monitor.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
django.setup()


def check_disk_usage():
    """Verifica o uso do disco."""
    try:
        disk = psutil.disk_usage("/")
        usage_percent = disk.percent
        if usage_percent > 90:
            logger.warning(f"Uso do disco crítico: {usage_percent}%")
        return usage_percent
    except Exception as e:
        logger.error(f"Erro ao verificar uso do disco: {e}")
        return None


def check_memory_usage():
    """Verifica o uso de memória."""
    try:
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        if usage_percent > 90:
            logger.warning(f"Uso de memória crítico: {usage_percent}%")
        return usage_percent
    except Exception as e:
        logger.error(f"Erro ao verificar uso de memória: {e}")
        return None


def check_cpu_usage():
    """Verifica o uso da CPU."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            logger.warning(f"Uso da CPU crítico: {cpu_percent}%")
        return cpu_percent
    except Exception as e:
        logger.error(f"Erro ao verificar uso da CPU: {e}")
        return None


def check_database_connection():
    """Verifica a conexão com o banco de dados."""
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Erro na conexão com o banco de dados: {e}")
        return False


def check_redis_connection():
    """Verifica a conexão com o Redis."""
    try:
        import redis

        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        return True
    except Exception as e:
        logger.error(f"Erro na conexão com o Redis: {e}")
        return False


def check_celery_workers():
    """Verifica o status dos workers do Celery."""
    try:
        from celery.app.control import Control

        app = Control()
        active_workers = app.inspect().active()
        if not active_workers:
            logger.warning("Nenhum worker do Celery ativo")
        return bool(active_workers)
    except Exception as e:
        logger.error(f"Erro ao verificar workers do Celery: {e}")
        return False


def check_application_health():
    """Verifica a saúde geral da aplicação."""
    try:
        response = requests.get("http://localhost:8000/health/")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erro ao verificar saúde da aplicação: {e}")
        return False


def send_alert(message, level="warning"):
    """Envia alerta para o sistema de monitoramento."""
    try:
        # Aqui você pode implementar o envio de alertas para seu sistema preferido
        # Por exemplo, email, Slack, Telegram, etc.
        logger.warning(f"ALERTA: {message}")
    except Exception as e:
        logger.error(f"Erro ao enviar alerta: {e}")


def main():
    """Função principal de monitoramento."""
    logger.info("Iniciando monitoramento do sistema...")

    # Verificar recursos do sistema
    disk_usage = check_disk_usage()
    memory_usage = check_memory_usage()
    cpu_usage = check_cpu_usage()

    # Verificar serviços
    db_ok = check_database_connection()
    redis_ok = check_redis_connection()
    celery_ok = check_celery_workers()
    app_ok = check_application_health()

    # Gerar relatório
    report = {
        "timestamp": datetime.now().isoformat(),
        "disk_usage": disk_usage,
        "memory_usage": memory_usage,
        "cpu_usage": cpu_usage,
        "database_ok": db_ok,
        "redis_ok": redis_ok,
        "celery_ok": celery_ok,
        "application_ok": app_ok,
    }

    # Enviar alertas se necessário
    if not all([db_ok, redis_ok, celery_ok, app_ok]):
        send_alert("Um ou mais serviços estão com problemas")

    logger.info(f"Relatório de monitoramento: {report}")


if __name__ == "__main__":
    main()
