@echo off
title ERP DVSYSTEM - Inicializador
color 0A

echo.
echo ===============================================
echo           ERP DVSYSTEM - INICIALIZADOR
echo ===============================================
echo.

REM Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    pause
    exit /b 1
)

REM Verifica se está no diretório correto
if not exist "manage.py" (
    echo [ERRO] Arquivo manage.py nao encontrado!
    echo Execute este script no diretorio raiz do projeto.
    pause
    exit /b 1
)

echo [INFO] Iniciando ERP DVSYSTEM...
echo.

REM Executa o script Python de inicialização
python iniciar_erp.py

echo.
echo [INFO] Encerrando...
pause
