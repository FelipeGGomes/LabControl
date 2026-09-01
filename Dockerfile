FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libcairo2-dev \
    pkg-config \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

# Convert requirements.txt from UTF-16LE to UTF-8 if necessary, and remove Windows-specific packages
RUN if grep -q -P '\x00' requirements.txt; then iconv -f UTF-16LE -t UTF-8 requirements.txt > req_utf8.txt && mv req_utf8.txt requirements.txt; fi && \
    sed -i '/pywin32/d' requirements.txt && \
    sed -i '/pythonnet/d' requirements.txt && \
    sed -i '/pywebview/d' requirements.txt && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
