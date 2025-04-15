import os
from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import io
from werkzeug.utils import secure_filename

# Configuración de Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Configuración de Flask-Mail para enviar correos
app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
app.config['MAIL_PORT'] = os.environ.get("MAIL_PORT", 587)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME")

# Inicializar Flask-Mail
mail = Mail(app)

#Crear upload/ si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Token secreto para control de acceso
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "Levies_24_token")

# Tesseract path (asegúrate de que esté instalado correctamente en tu contenedor o entorno)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Idiomas de Tesseract
TESSERACT_LANGUAGES = [
    "ara", "bul", "ces", "chi-sim", "dan", "deu", "eng", "est", "fin", "fra", "ell",
    "hin", "hrv", "hun", "isl", "ita", "jpn", "kor", "lav", "lit", "mlt", "nld", "pol", 
    "por", "rus", "ron", "slv", "slk", "spa", "swe"
]

# Función para verificar si el archivo es de tipo imagen
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Preprocesamiento de la imagen
def preprocess_image(img):
    # Convertir la imagen a escala de grises
    img = img.convert('L')
    
    # Binarización (umbral 180)
    img = img.point(lambda p: p > 180 and 255)
    
    # Reducir el ruido con un filtro de mediana
    img = img.filter(ImageFilter.MedianFilter(3))
    
    # Mejorar el contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    
    # Redimensionar imagen para mejorar la calidad del OCR
    img = img.resize((img.width * 2, img.height * 2))  # Aumenta el tamaño de la imagen
    
    return img

# Ruta para cargar la imagen y extraer texto
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return redirect(request.url)
    
    files = request.files.getlist('file')
    extracted_texts = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            img = Image.open(file_path)
            img = preprocess_image(img)

            lang_string = "+".join(TESSERACT_LANGUAGES)
            extracted_text = pytesseract.image_to_string(img, lang=lang_string)

            extracted_texts.append({
                'filename': filename,
                'text': extracted_text,
                'file_path': file_path
            })

    if not extracted_texts:
        return "<h2>No se pudieron procesar imágenes válidas</h2><a href='/'>Volver</a>"

    return render_template('results.html', extracted_texts=extracted_texts)

# Ruta para enviar el correo
@app.route('/send_email', methods=['POST'])
def send_email():
    extracted_text = request.form['extracted_text']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    comentario = request.form['comentario']
    
    # Crear el mensaje de correo
    msg = Message("Datos extraídos de las imágenes", 
                  recipients=[os.environ.get("MAIL_USERNAME")])  # Usamos el correo del env
    msg.body = f"Texto extraído de la imagen:\n\n{extracted_text}\n\nTeléfono: {telefono}\nDirección: {direccion}\nComentario: {comentario}"

    try:
        mail.send(msg)
        return "<h2>Correo enviado correctamente.</h2><a href='/'>Volver</a>"
    except Exception as e:
        return f"<h2>Error al enviar correo: {e}</h2><a href='/'>Volver</a>"

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
