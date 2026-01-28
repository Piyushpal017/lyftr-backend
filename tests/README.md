# Docker & Infrastructure Guide

This directory contains all infrastructure-related files required to
build, run, and test the **Lyftr Backend Service** using Docker.

The goal of this setup is to provide a reproducible and
environment-agnostic way to run the backend application.

------------------------------------------------------------------------

## Contents

-   Dockerfile\
-   docker-compose.yml\
-   Makefile\
-   This README

------------------------------------------------------------------------

## Prerequisites

-   Docker Desktop (Windows / macOS / Linux)

Verify Docker installation:

``` bash
docker --version
docker compose version
```

------------------------------------------------------------------------

## Environment Variables

The application relies on the following environment variables.

  Variable         Description
  ---------------- -----------------------------------------------------
  WEBHOOK_SECRET   Secret key used to validate webhook HMAC signatures
  DATABASE_URL     Database connection string
  LOG_LEVEL        Application log level (INFO, DEBUG, ERROR)

Example values:

``` text
WEBHOOK_SECRET=testsecret
DATABASE_URL=sqlite:///./app.db
LOG_LEVEL=INFO
```

------------------------------------------------------------------------

## Dockerfile Overview

The Dockerfile: - Uses a lightweight Python base image - Installs
dependencies from `requirements.txt` - Copies application source code -
Runs the FastAPI app using Uvicorn

------------------------------------------------------------------------

## Build Docker Image

Run the following command from the project root:

``` bash
docker build -t lyftr-backend -f tests/Dockerfile .
```

------------------------------------------------------------------------

## Run Docker Container

``` bash
docker run -p 8000:8000 \
  -e WEBHOOK_SECRET=testsecret \
  -e DATABASE_URL=sqlite:///./app.db \
  -e LOG_LEVEL=INFO \
  lyftr-backend
```

Application will be available at:

``` text
http://127.0.0.1:8000
```

------------------------------------------------------------------------

## Health Check Endpoints

``` text
GET /health/live
GET /health/ready
```

------------------------------------------------------------------------

## Metrics (Prometheus)

Metrics endpoint:

``` text
GET /metrics
```

------------------------------------------------------------------------

## Webhook Endpoint

``` text
POST /webhook
```

------------------------------------------------------------------------

## Docker Compose Usage

``` bash
docker compose up --build
```

Stop containers:

``` bash
docker compose down
```

------------------------------------------------------------------------

## Notes

-   SQLite used for local testing
-   Configuration is environment-driven
-   Infrastructure files isolated in `tests/` directory

------------------------------------------------------------------------

## Status

Docker build and runtime verified successfully.
