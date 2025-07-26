@echo off
REM Inicia o app Edge como PWA apontando para o ERP
start "ERP" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge_proxy.exe"  --profile-directory=Default --app-id=iplbeaognhfojdbeljdcgcjjehenhepl --app-url=http://127.0.0.1:8000/login/?next=/ --app-launch-source=4
REM Inicia o servidor Django
python manage.py runserver
pause
