@echo off
setlocal enabledelayedexpansion

REM Set the path to the MemGPT virtual environment
set VENV_PATH=X:\AI\MemGPT\memgpt_venv

REM Activate the virtual environment
call "%VENV_PATH%\Scripts\activate"

REM Set your OpenAI API key
set OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

REM Define the directory where your personas are stored
set PROFILE_DIR=X:\AI\MemGPT\MemGPT\MemGPT\memgpt\humans\examples
set PERSONA_DIR=X:\AI\MemGPT\MemGPT\MemGPT\memgpt\personas\examples

:menu
cls
echo Choose a profile:

REM List available personas in the specified directory
set /a count=0
for %%f in ("%PROFILE_DIR%\*.txt") do (
    set /a count+=1
    set "profile[!count!]=%%f"
    echo [!count!] %%~nxf
)

REM Prompt the user to select a persona
set /p selection="Enter the number of the profile to use (0 to exit, '+' to add a new profile): "

REM If the selection is "0," exit the script
if "%selection%"=="0" (
    goto :eof
)

REM If the selection is +, start the profile maker and save the profile
if "%selection%"=="+" (
    echo Making new profile. Hang tight!
    python X:\AI\MemGPT\profilemaker.py
    pause
    goto :menu
)

REM If the selection is empty or not a valid number, prompt the user to make a valid selection
if "%selection%"=="" (
    echo Invalid input. Please enter a valid number.
    pause
    goto :menu
)

REM If the selection is valid, run MemGPT with the selected persona
if !selection! geq 1 if !selection! leq !count! (
    set "selected_profile=!profile[%selection%]!"
) else (
    echo Invalid selection. Please try again.
    pause
    goto :menu
)

cls
echo Choose a persona:

REM List available personas in the specified directory
set /a count=0
for %%f in ("%PERSONA_DIR%\*.txt") do (
    set /a count+=1
    set "persona[!count!]=%%f"
    echo [!count!] %%~nxf
)

REM Prompt the user to select a persona
set /p selection="Enter the number of the persona to use (0 to exit): "

REM If the selection is "0," exit the script
if "%selection%"=="0" (
    goto :eof
)

REM If the selection is empty or not a valid number, prompt the user to make a valid selection
if "%selection%"=="" (
    echo Invalid input. Please enter a valid number.
    pause
    goto :menu
)

REM If the selection is valid, run MemGPT with the selected persona
if !selection! geq 1 if !selection! leq !count! (
    set "selected_persona=!persona[%selection%]!"
) else (
    echo Invalid selection. Please try again.
    pause
    goto :menu
)

python X:\AI\MemGPT\MemGPT\MemGPT\main.py --human "!selected_profile!" --persona "!selected_persona!"

:eof