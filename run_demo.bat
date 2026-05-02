@echo off
echo.
echo  ================================================
echo   RAG at Scale Demo — Jupyter + PySpark
echo  ================================================
echo.
echo  Starting... (first run downloads ~2GB image once)
echo  After startup, open: http://localhost:8888?token=ragdemo
echo.

docker-compose -f docker-compose-demo.yml up

echo.
echo  To stop:  Ctrl+C  then  docker-compose -f docker-compose-demo.yml down
