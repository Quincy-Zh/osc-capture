@echo off

rd /S /Q dist
del /F /Q osc-capture.7z

pyinstaller -n osc-capture ^
--add-data src\icon.png:. ^
--add-data drv:.\drv ^
--add-binary .\bin\*:. ^
--hidden-import instruments ^
--hidden-import pyvisa_py ^
--hidden-import pyserial ^
--clean ^
--noconfirm ^
-i .\src\icon.ico ^
-w .\src\main.py

7z a dist\osc-capture.7z .\dist\osc-capture\* -mx

echo Done!