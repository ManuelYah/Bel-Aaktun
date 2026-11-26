FROM python:3.12-slim
WORKDIR /e2e
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["pytest", "-v", "--html=reports/reporte.html", "--self-contained-html"]
