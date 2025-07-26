import os

import django
from django.apps import apps
from django.conf import settings
from django.db import connection
from django.db.models import Count

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
django.setup()

print("===== DIAGNÓSTICO COMPLETO DO SISTEMA DJANGO =====\n")

# 1. Listar todos os apps e modelos
print("--- Apps e Modelos ---")
for app_config in apps.get_app_configs():
    print(f"App: {app_config.label}")
    for model in app_config.get_models():
        print(f"  - Modelo: {model.__name__}")
print()

# 2. Contar registros em cada tabela
print("--- Quantidade de registros em cada tabela ---")
for model in apps.get_models():
    try:
        count = model.objects.count()
        print(f"{model._meta.db_table}: {count} registros")
    except Exception as e:
        print(f"{model._meta.db_table}: ERRO ({e})")
print()

# 3. Verificar integridade de FKs (dados órfãos)
print("--- Integridade de Foreign Keys (FKs) ---")
for model in apps.get_models():
    for field in model._meta.fields:
        if field.is_relation and field.related_model is not None and not field.auto_created:
            try:
                total = model.objects.exclude(**{f"{field.name}__isnull": True}).count()
                orfaos = (
                    model.objects.filter(**{f"{field.name}__isnull": False})
                    .exclude(**{f"{field.name}__in": field.related_model.objects.all()})
                    .count()
                )
                if orfaos > 0:
                    print(f"{model.__name__}.{field.name}: {orfaos} registros órfãos de {total}")
            except Exception as e:
                print(f"{model.__name__}.{field.name}: ERRO ({e})")
print()

# 4. Migrações pendentes
print("--- Migrações pendentes ---")
from io import StringIO

from django.core.management import call_command

out = StringIO()
call_command("showmigrations", "--plan", stdout=out)
print(out.getvalue())

# 5. Dados duplicados em campos únicos
print("--- Dados duplicados em campos únicos ---")
for model in apps.get_models():
    unique_fields = [f.name for f in model._meta.fields if f.unique and not f.primary_key]
    for field_name in unique_fields:
        try:
            duplicates = model.objects.values(field_name).annotate(c=Count(field_name)).filter(c__gt=1)
            for dup in duplicates:
                print(f'{model.__name__}.{field_name}: valor duplicado {dup[field_name]} ({dup["c"]} vezes)')
        except Exception as e:
            print(f"{model.__name__}.{field_name}: ERRO ({e})")
print()

# 6. Banco de dados ativo
print("--- Banco de dados ativo ---")
db_engine = settings.DATABASES["default"]["ENGINE"]
db_name = settings.DATABASES["default"]["NAME"]
print(f"ENGINE: {db_engine}")
print(f"NAME: {db_name}")
print()

# 7. Listar arquivos de banco presentes no projeto
print("--- Arquivos de banco encontrados no projeto ---")
for file in os.listdir(settings.BASE_DIR):
    if file.endswith(".sqlite3") or file.endswith(".db") or "backup" in file:
        print(f"- {file}")
print()

# 8. Modo DEBUG
print("--- Modo DEBUG ---")
print(f"DEBUG: {settings.DEBUG}")
print()

# 9. Últimos 10 erros do log (se houver)
print("--- Últimos 10 erros do log (django.log) ---")
log_path = os.path.join(settings.BASE_DIR, "logs", "django.log")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        errors = [l for l in lines if "ERROR" in l or "CRITICAL" in l]
        for l in errors[-10:]:
            print(l.strip())
else:
    print("Arquivo de log não encontrado.")
print()

print("===== FIM DO DIAGNÓSTICO =====")
