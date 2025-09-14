@echo off
cd "C:\Users\Acer Lite\.jenkins\workspace\HireHub_Jobportal"
call venv\Scripts\activate
start "" python app.py
start http://127.0.0.1:5000

