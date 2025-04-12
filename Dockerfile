FROM python:3.10-slim

# Evita interacción durante instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Establece directorio de trabajo
WORKDIR /app

# Copia los archivos al contenedor
COPY . /app

# Actualiza e instala Tesseract con idiomas seleccionados
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-bul \
    tesseract-ocr-ces \
    tesseract-ocr-chi-sim \
    tesseract-ocr-dan \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    tesseract-ocr-est \
    tesseract-ocr-fin \
    tesseract-ocr-fra \
    tesseract-ocr-ell \
    tesseract-ocr-hin \
    tesseract-ocr-hrv \
    tesseract-ocr-hun \
    tesseract-ocr-isl \
    tesseract-ocr-ita \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-lav \
    tesseract-ocr-lit \
    tesseract-ocr-mlt \
    tesseract-ocr-nld \
    tesseract-ocr-pol \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    tesseract-ocr-ron \
    tesseract-ocr-slv \
    tesseract-ocr-slk \
    tesseract-ocr-spa \
    tesseract-ocr-swe \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto para Flask o Gunicorn
EXPOSE 5000

# Comando para ejecutar la app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
#CMD ["python", "app.py"]
