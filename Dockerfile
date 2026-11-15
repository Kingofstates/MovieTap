# Room 206 - Cinema & Anime Streaming Container
FROM python:3.11-slim

# Install system dependencies including FFmpeg for on-the-fly muxing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# Default port (Render assigns $PORT at runtime)
ENV PORT=8000
ENV HOST=0.0.0.0
EXPOSE 8000

CMD ["python", "run.py"]
