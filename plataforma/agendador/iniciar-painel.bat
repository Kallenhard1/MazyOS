@echo off
REM Inicia o painel MarioLucash. Sobe duas pastas (agendador -> plataforma -> raiz)
REM e roda o app a partir da raiz do projeto, como manda o README.
cd /d "%~dp0..\.."
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
echo Painel em http://127.0.0.1:5000   (feche esta janela para parar)
python plataforma\app.py
