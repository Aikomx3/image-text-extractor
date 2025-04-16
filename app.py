import os
from flask import Flask, render_template, request, redirect
from flask_mail import Mail, Message
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Validación de variables críticas para producción
required_env_vars = [
    "MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME",
    "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER"
]

for var in required_env_vars:
    if not os.environ.get(var):
        raise RuntimeError(f"Falta la variable de entorno obligatoria: {var}")

# Configuración segura de Flask-Mail
app.config['MAIL_SERVER'] = os.environ["MAIL_SERVER"]
app.config['MAIL_PORT'] = int(os.environ["MAIL_PORT"])
app.config['MAIL_USE_TLS'] = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
app.config['MAIL_USE_SSL'] = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
app.config['MAIL_USERNAME'] = os.environ["MAIL_USERNAME"]
app.config['MAIL_PASSWORD'] = os.environ["MAIL_PASSWORD"]
app.config['MAIL_DEFAULT_SENDER'] = os.environ["MAIL_DEFAULT_SENDER"]
app.config['MAIL_DEBUG'] = False  # seguridad en producción

mail = Mail(app)

# Crear directorio de subida si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Token secreto
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "Levies_24_token")

# Ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Idiomas
TESSERACT_LANGUAGES = [
    "ara", "bul", "ces", "chi-sim", "dan", "deu", "eng", "est", "fin", "fra", "ell",
    "hin", "hrv", "hun", "isl", "ita", "jpn", "kor", "lav", "lit", "mlt", "nld", "pol", 
    "por", "rus", "ron", "slv", "slk", "spa", "swe"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    # Verificar el token de acceso
    token = request.form.get("access_token")
    if token != ACCESS_TOKEN:
        return "<h2>Token inválido</h2><a href='/'>Volver</a>"

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
            lang_string = "+".join(TESSERACT_LANGUAGES)
            extracted_text = pytesseract.image_to_string(img, lang=lang_string)

            extracted_texts.append({
                'filename': filename,
                'text': extracted_text,
                'file_path': file_path
            })

    if not extracted_texts:
        return "<h2>No se pudieron procesar imágenes válidas</h2><a href='/'>Volver</a>"

    combined_text = "\n\n".join([e['text'] for e in extracted_texts])
    return render_template('results.html', extracted_text=combined_text)

@app.route('/send_email', methods=['POST'])
def send_email():
    extracted_text = request.form['extracted_text']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    comentario = request.form['comentario']

    msg = Message(
        subject="Datos extraídos de las imágenes",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[app.config['MAIL_USERNAME']],
        body=f"""Texto extraído de la imagen:

{extracted_text}

Teléfono: {telefono}
Dirección: {direccion}
Comentario: {comentario}"""
    )

    try:
        mail.send(msg)
        return "<h2>Correo enviado correctamente.</h2><a href='/'>Volver</a>"
    except Exception as e:
        print(f"[ERROR AL ENVIAR EMAIL] {str(e)}")  # Aparece en logs Render
        return "<h2>Error al enviar el correo. Revisa los logs del servidor.</h2><a href='/'>Volver</a>"

if __name__ == '__main__':
    app.run(debug=True)
