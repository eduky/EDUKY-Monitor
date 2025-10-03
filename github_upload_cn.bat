@echo off
title FAKA Monitor GitHub Upload Tool
powershell -ExecutionPolicy Bypass -File "%~dp0upload_to_github_cn.ps1"
pause