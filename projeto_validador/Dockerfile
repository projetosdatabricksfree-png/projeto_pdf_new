FROM python:3.11-slim

# System dependencies for PDF/image analysis
RUN apt-get update && apt-get install -y \
    libvips-dev \
    ghostscript \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create upload volume directory
RUN mkdir -p /volumes/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
