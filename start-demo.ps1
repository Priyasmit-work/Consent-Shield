# ConsentShield - one-click demo launcher (run on the presenter's laptop).
# Usage (PowerShell, from the ConsentShield-cookie folder):  .\start-demo.ps1
# Opens two windows: the backend (port 8000) and the frontend (port 3000/5173).
# Chrome opens on THIS machine when you press apply, so the audience sees it
# on your screen / projector.

$root = $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; cd backend; uvicorn app.main:app --port 8000"

Start-Sleep -Seconds 3

Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$root\frontend'; npm run dev"

Write-Host "Backend:  http://localhost:8000/docs"
Write-Host "Frontend: open the Local: URL printed in the second window"
