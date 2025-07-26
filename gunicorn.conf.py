import multiprocessing
import os

# Configurações básicas
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2

# Configurações de logging
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de performance
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# Configurações de SSL (se necessário)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Configurações de processo
daemon = False
pidfile = "gunicorn.pid"
umask = 0o022
user = None
group = None
tmp_upload_dir = None

# Configurações de worker
preload_app = True
reload = False
reload_extra_files = []
reload_engine = "auto"

# Configurações de proxy
proxy_protocol = False
proxy_allow_ips = "*"

# Configurações de buffer
buffer_size = 4096

# Configurações de timeout
timeout = 30
graceful_timeout = 30
keepalive = 2

# Configurações de worker
worker_tmp_dir = None
worker_class = "gevent"
worker_connections = 1000
worker_max_requests = 1000
worker_max_requests_jitter = 50

# Configurações de logging
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'


def on_starting(server):
    """Função executada quando o servidor inicia."""
    pass


def on_exit(server):
    """Função executada quando o servidor é encerrado."""
    pass


def worker_int(worker):
    """Função executada quando um worker é interrompido."""
    worker.log.info("worker received INT or QUIT signal")


def worker_abort(worker):
    """Função executada quando um worker é abortado."""
    worker.log.info("worker received SIGABRT signal")
