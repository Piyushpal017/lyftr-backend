FROM python:3.10-slim

# env basics
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (sqlite needs none extra)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code
COPY . .

# default envs (override via docker run)
ENV LOG_LEVEL=INFO
ENV DATABASE_URL=sqlite:///./app.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
