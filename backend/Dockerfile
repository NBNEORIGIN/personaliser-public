FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# system libs required by cairosvg/pango and fonts for deterministic text
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    ca-certificates \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY backend/app /app/app
COPY backend/data /app/data
COPY backend/tests /app/tests

# Copy fonts and assets
COPY fonts /app/../fonts
COPY assets /app/../assets

EXPOSE 8000
# Debug: Test Python and show environment
CMD ["sh", "-c", "echo 'Container started' && echo 'PORT='$PORT && python --version && ls -la /app && python -c 'import sys; print(sys.path)' && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
