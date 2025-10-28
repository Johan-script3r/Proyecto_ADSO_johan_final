from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import session
import os
import pymysql
from urllib.parse import quote_plus
from functools import wraps
from flask import abort


app = Flask(__name__)

MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
MYSQL_DATABASE = 'medical_data'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mi_secreto')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://johan:johanc@isladigital.xyz:3311/f58_johan'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'max_overflow': 0,
}

db = SQLAlchemy(app)

class RegistroMedico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ritmo_cardiaco = db.Column(db.Integer, nullable=False)
    presion_sistolica = db.Column(db.Integer, nullable=False)
    presion_diastolica = db.Column(db.Integer, nullable=False)
    nivel_azucar = db.Column(db.Float, nullable=False)
    colesterol = db.Column(db.Float, nullable=False)
    oxigeno_sangre = db.Column(db.Float, nullable=False)
    notas = db.Column(db.Text)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    def __repr__(self):
        return f'<RegistroMedico {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'ritmo_cardiaco': self.ritmo_cardiaco,
            'presion_sistolica': self.presion_sistolica,
            'presion_diastolica': self.presion_diastolica,
            'nivel_azucar': self.nivel_azucar,
            'colesterol': self.colesterol,
            'oxigeno_sangre': self.oxigeno_sangre,
            'notas': self.notas
        }

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    rol = db.Column(db.String(20), default='user')
    email = db.Column(db.String(120), unique=True, nullable=False)
    edad = db.Column(db.Integer)
    sexo = db.Column(db.String(10))
    telefono = db.Column(db.String(20))

    registros = db.relationship("RegistroMedico", backref="usuario", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    ritmos_cardiacos = db.relationship("RitmoCardiaco", backref="usuario", lazy=True)
    presiones = db.relationship("PresionArterial", backref="usuario", lazy=True)
    niveles_azucar = db.relationship("NivelAzucar", backref="usuario", lazy=True)
    colesteroles = db.relationship("Colesterol", backref="usuario", lazy=True)
    oxigenos = db.relationship("OxigenoSangre", backref="usuario", lazy=True)
    pesos = db.relationship("Peso", backref="usuario", lazy=True)
    alturas = db.relationship("Altura", backref="usuario", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def validar_valores(datos):
    errores = []
    if datos['ritmo_cardiaco'] < 30 or datos['ritmo_cardiaco'] > 200:
        errores.append("Ritmo cardíaco fuera del rango válido (30-200 ppm)")
    if datos['presion_sistolica'] < 70 or datos['presion_sistolica'] > 250:
        errores.append("Presión sistólica fuera del rango válido (70-250 mmHg)")
    if datos['presion_diastolica'] < 40 or datos['presion_diastolica'] > 150:
        errores.append("Presión diastólica fuera del rango válido (40-150 mmHg)")
    if datos['nivel_azucar'] < 50 or datos['nivel_azucar'] > 600:
        errores.append("Nivel de azúcar fuera del rango válido (50-600 mg/dL)")
    if datos['colesterol'] < 60 or datos['colesterol'] > 500:
        errores.append("Colesterol fuera del rango válido (100-500 mg/dL)")
    if datos['oxigeno_sangre'] < 70 or datos['oxigeno_sangre'] > 100:
        errores.append("Oxígeno en sangre fuera del rango válido (70-100%)")
    return errores

@app.route('/inicio')
def inicio():
    return render_template("inicio_salud.html")

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    registros = RegistroMedico.query.filter_by(usuario_id=session['usuario_id'])\
                .order_by(RegistroMedico.fecha.desc()).limit(10).all()
    return render_template('index.html', registros=registros)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_registro():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para agregar un registro.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            datos = {
                'ritmo_cardiaco': int(request.form['ritmo_cardiaco']),
                'presion_sistolica': int(request.form['presion_sistolica']),
                'presion_diastolica': int(request.form['presion_diastolica']),
                'nivel_azucar': float(request.form['nivel_azucar']),
                'colesterol': float(request.form['colesterol']),
                'oxigeno_sangre': float(request.form['oxigeno_sangre'])
            }
            errores = validar_valores(datos)
            if errores:
                for error in errores:
                    flash(error, 'error')
                return render_template('agregar.html')

            nuevo_registro = RegistroMedico(
                ritmo_cardiaco=datos['ritmo_cardiaco'],
                presion_sistolica=datos['presion_sistolica'],
                presion_diastolica=datos['presion_diastolica'],
                nivel_azucar=datos['nivel_azucar'],
                colesterol=datos['colesterol'],
                oxigeno_sangre=datos['oxigeno_sangre'],
                notas=request.form.get('notas', ''),
                usuario_id=session['usuario_id'] 
            )
            db.session.add(nuevo_registro)
            db.session.commit()
            flash('Registro médico agregado exitosamente!', 'success')
            return redirect(url_for('index'))
        except ValueError:
            flash('Error: Todos los campos numéricos deben tener valores válidos', 'error')
        except Exception as e:
            flash(f'Error al guardar el registro: {str(e)}', 'error')

    return render_template('agregar.html')

@app.route('/historial')
def historial():
    registros = RegistroMedico.query.filter_by(usuario_id=session['usuario_id']).order_by(RegistroMedico.fecha.desc()).all()
    return render_template('historial.html', registros=registros)

@app.route('/estadisticas')
def estadisticas():
    registros = RegistroMedico.query.filter_by(usuario_id=session['usuario_id']).all()
    if not registros:
        flash('No hay datos para mostrar estadísticas', 'info')
        return render_template('estadisticas.html', registros=None)
    return render_template('estadisticas.html', registros=registros)


@app.route('/api/registros')
def api_registros():
    registros = RegistroMedico.query.order_by(RegistroMedico.fecha.desc()).all()
    return jsonify([registro.to_dict() for registro in registros])

@app.route('/api/agregar', methods=['POST'])
def api_agregar_registro():
    try:
        data = request.get_json()
        datos = {
            'ritmo_cardiaco': int(data['ritmo_cardiaco']),
            'presion_sistolica': int(data['presion_sistolica']),
            'presion_diastolica': int(data['presion_diastolica']),
            'nivel_azucar': float(data['nivel_azucar']),
            'colesterol': float(data['colesterol']),
            'oxigeno_sangre': float(data['oxigeno_sangre'])
        }
        errores = validar_valores(datos)
        if errores:
            return jsonify({'error': errores}), 400

        nuevo_registro = RegistroMedico(
            ritmo_cardiaco=datos['ritmo_cardiaco'],
            presion_sistolica=datos['presion_sistolica'],
            presion_diastolica=datos['presion_diastolica'],
            nivel_azucar=datos['nivel_azucar'],
            colesterol=datos['colesterol'],
            oxigeno_sangre=datos['oxigeno_sangre'],
            notas=request.form.get('notas', ''),
            usuario_id=session['usuario_id']
        ) 
        db.session.add(nuevo_registro)
        db.session.commit()
        return jsonify({'message': 'Registro agregado exitosamente', 'id': nuevo_registro.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash("Sesión cerrada", "info")
    return redirect(url_for('login'))
    
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    rol = db.Column(db.String(20), default='user')

    registros = db.relationship("RegistroMedico", backref="usuario", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nameUser']
        password = request.form['passwordUser']

        if Usuario.query.filter_by(nombre=nombre).first():
            flash("Ese usuario ya existe", "error")
            return redirect(url_for('registro'))

        nuevo_usuario = Usuario(nombre=nombre)
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario registrado correctamente", "success")
        return redirect(url_for('login'))

    return render_template("registro.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form.get('nameUser', '').strip()
        password = request.form.get('passwordUser', '')

        print(f"Intento de login con usuario: '{nombre}'")
        usuario = Usuario.query.filter_by(nombre=nombre).first()

        if usuario:
            print(f"Usuario encontrado en la base de datos: {usuario.nombre}")
            if usuario.check_password(password):
                print("Contraseña correcta. Iniciando sesión...")
                session['usuario_id'] = usuario.id
                flash(f"Bienvenido, {usuario.nombre}", "success")
                
                if usuario.rol == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('inicio'))
            else:
                print("Contraseña incorrecta.")
        else:
            print("Usuario no encontrado.")

        flash("Usuario o contraseña incorrectos", "error")

    return render_template("login_salud.html")

def rol_requerido(rol):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                flash("Debes iniciar sesión para acceder.", "error")
                return redirect(url_for('login'))
            
            usuario = Usuario.query.get(session['usuario_id'])
            if not usuario or usuario.rol != rol:
                flash("No tienes permisos para acceder a esta página.", "error")
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin/dashboard')
@rol_requerido('admin')
def admin_dashboard():
    usuarios = Usuario.query.all()
    return render_template('admin_dashboard.html', usuarios=usuarios)

@app.route('/admin/registros/<int:usuario_id>')
@rol_requerido('admin')
def ver_usuario_registros(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    registros = RegistroMedico.query.filter_by(usuario_id=usuario_id).order_by(RegistroMedico.fecha.desc()).all()
    return render_template('ver_registros_usuario.html', usuario=usuario, registros=registros)
    
@app.route('/admin/promover/<int:usuario_id>')
@rol_requerido('admin')
def promover_admin(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.rol = 'admin'
    db.session.commit()
    flash(f'El usuario {usuario.nombre} ahora es un administrador.', 'success')
    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/eliminar/usuario/<int:usuario_id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    try:
        RegistroMedico.query.filter_by(usuario_id=usuario_id).delete()
        db.session.delete(usuario)
        db.session.commit()
        flash(f'El usuario {usuario.nombre} y todos sus registros han sido eliminados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/eliminar/registro/<int:registro_id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_registro(registro_id):
    registro = RegistroMedico.query.get_or_404(registro_id)
    usuario_id = registro.usuario_id

    try:
        db.session.delete(registro)
        db.session.commit()
        flash('Registro médico eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el registro: {str(e)}', 'error')
    
    return redirect(url_for('ver_usuario_registros', usuario_id=usuario_id))
    
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,host='0.0.0.0',port=5000)