FROM python:3.10-slim

WORKDIR /app

COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ .

EXPOSE 8050

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8050", "app:server"]
