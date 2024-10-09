@echo off
rem This batch file should be located in the root directory of the project.

rem Set environment variables for paths
set "PROJECT_DIR=%~dp0"
set "PYTHON_SCRIPT=%PROJECT_DIR%Sentence_Queuer.py"

rem Start the Python script
start python "%PYTHON_SCRIPT%"

rem Exit the batch file
exit