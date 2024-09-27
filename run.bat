SET mypath=%~dp0
call %mypath%venv\Scripts\activate
python %mypath%main.py
pause