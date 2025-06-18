@echo off
echo ============================================
echo     🚀 Setup do Projeto de IA - Gradio
echo ============================================

REM Verifica se a pasta do ambiente virtual já existe
IF NOT EXIST "venv\" (
    echo [1/4] A criar ambiente virtual...
    python -m venv venv
)

echo [2/4] A ativar o ambiente virtual...
call venv\Scripts\activate

echo [3/4] A instalar dependências...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] A iniciar o projeto...
python main.py

pause