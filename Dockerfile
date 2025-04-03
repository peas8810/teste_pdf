FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libreoffice \
    ghostscript \
    poppler-utils \
    tesseract-ocr \
    python3-pip \
    python3-dev \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p documentos

EXPOSE 8000

CMD ["uvicorn", "app:py", "--host", "0.0.0.0", "--port", "8000"]
