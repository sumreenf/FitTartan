# Runs seed.py from this folder using `python` on your PATH (activate a venv first if you use one).
# In PowerShell, paths with spaces MUST be quoted, e.g.:
#   & "C:\Users\you\Desktop\CMU Spring 2026\Hackathon\.venv\Scripts\python.exe" .\seed.py
Set-Location $PSScriptRoot
python seed.py
exit $LASTEXITCODE
