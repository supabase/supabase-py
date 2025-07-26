# DV System

Sistema de gestão empresarial desenvolvido em Django.

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- Node.js 14+ (para assets frontend)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/dvsystem.git
cd dvsystem
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
- Crie um banco PostgreSQL
- Atualize as configurações em `dvsystem/settings.py`

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Colete os arquivos estáticos:
```bash
python manage.py collectstatic
```

8. Execute o servidor:
```bash
python manage.py runserver
```

## Configuração de Produção

1. Gere uma nova SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

2. Configure as variáveis de ambiente:
- DEBUG=False
- SECRET_KEY=sua-chave-secreta
- ALLOWED_HOSTS=seu-dominio.com
- DATABASE_URL=postgres://user:password@localhost:5432/dbname

3. Configure o servidor web (Nginx/Apache)

4. Configure o servidor WSGI (Gunicorn)

## Backup

O sistema possui backup automático configurado para:
- Banco de dados (diariamente)
- Arquivos de mídia (semanalmente)

## Monitoramento

- Logs: `/logs/django.log`
- Monitoramento de erros: Sentry
- Monitoramento de performance: New Relic

## Segurança

- HTTPS configurado
- Headers de segurança ativos
- Rate limiting implementado
- Backup de segurança diário

## Suporte

Para suporte, entre em contato através de:
- Email: suporte@dvsystem.com
- Telefone: (XX) XXXX-XXXX 