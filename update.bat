@echo off
set /p msg="📝 Enter Commit Message: "

echo.
echo 📤 Uploading to GitHub...

:: Menjalankan urutan perintah Git
git add .
git commit -m "%msg%"
git push

echo.
echo ✅ SUCCESS: Code is now live on GitHub!
echo.
pause