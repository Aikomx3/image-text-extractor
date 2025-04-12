import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from flask_mail import Mail, Message

# Configuración de Flask
app = Flask(__name__)

# Carpeta donde se almacenan los archivos subidos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Usamos SSL
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)

# Función para comprobar si el archivo tiene extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Función para extraer texto de una imagen
def extract_text_from_image(image_path):
    text = ""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
    except Exception as e:
        print(f"Error al extraer texto de la imagen: {e}")
    return text


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    # Verificamos si el formulario contiene un archivo
    if 'file' not in request.files:
        return redirect(url_for('index'))

    files = request.files.getlist('file')

    # Limitar a 10 archivos (esto debería coincidir con el límite en el frontend)
    if len(files) > 10:
        return "<h2>Solo puedes subir hasta 10 imágenes.</h2><a href='/'>Volver</a>"

    if len(files) == 0:
        return redirect(url_for('index'))

    extracted_text = ""
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            try:
                file.save(path)
                extracted_text += extract_text_from_image(path)  # Extraer todo el texto de la imagen
            finally:
                if os.path.exists(path):
                    os.remove(path)  # Eliminar el archivo después de procesarlo

    # Volcar el texto extraído en results.html
    return render_template('results.html', extracted_text=extracted_text)


@app.route('/send_email', methods=['POST'])
def send_email():
    extracted_text = request.form['extracted_text']

    # Crear el mensaje de correo
    msg = Message("Datos extraídos de las imágenes",
                  recipients=[os.environ.get("MAIL_USERNAME")])
    msg.body = extracted_text

    try:
        mail.send(msg)
        return "<h2>Correo enviado correctamente.</h2><a href='/'>Volver</a>"
    except Exception as e:
        return f"<h2>Error al enviar correo: {e}</h2><a href='/'>Volver</a>"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
