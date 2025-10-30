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
from sqlalchemy import func
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mi_secreto')
#app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://johan:johanc@isladigital.xyz:3311/f58_johan'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datos_medicos_local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 180, 
    'pool_timeout': 20,
    'max_overflow': 0,
    'pool_size': 10, 
    'max_overflow': 20,
}

def rol_requerido(rol):
    # La función externa recibe el argumento ('admin')
    def decorator(f):
        # La función del medio recibe la función a decorar (la ruta de Flask)
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Lógica de verificación
            if 'usuario_id' not in session or session.get('rol') != rol:
                flash("Acceso denegado. Se requiere el rol de " + rol, "error")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        # ESTO ES CRÍTICO: Debe devolver la función envuelta
        return decorated_function
    # ESTO TAMBIÉN ES CRÍTICO: Debe devolver la función interna 'decorator'
    return decorator

db = SQLAlchemy(app)


class HealthMetricMixin:
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S')
        }

class RitmoCardiaco(HealthMetricMixin, db.Model):
    valor = db.Column(db.Integer, nullable=False)
    __tablename__ = 'ritmo_cardiaco'
    def to_dict(self):
        d = super().to_dict()
        d['ritmo_cardiaco'] = self.valor
        return d

class PresionArterial(HealthMetricMixin, db.Model):
    sistolica = db.Column(db.Integer, nullable=False)
    diastolica = db.Column(db.Integer, nullable=False)
    __tablename__ = 'presion_arterial'
    def to_dict(self):
        d = super().to_dict()
        d['presion_sistolica'] = self.sistolica
        d['presion_diastolica'] = self.diastolica
        return d

class NivelAzucar(HealthMetricMixin, db.Model):
    valor = db.Column(db.Float, nullable=False)
    __tablename__ = 'nivel_azucar'
    def to_dict(self):
        d = super().to_dict()
        d['nivel_azucar'] = self.valor
        return d

class Colesterol(HealthMetricMixin, db.Model):
    valor = db.Column(db.Float, nullable=False)
    __tablename__ = 'colesterol'
    def to_dict(self):
        d = super().to_dict()
        d['colesterol'] = self.valor
        return d

class OxigenoSangre(HealthMetricMixin, db.Model):
    valor = db.Column(db.Float, nullable=False)
    __tablename__ = 'oxigeno_sangre'
    def to_dict(self):
        d = super().to_dict()
        d['oxigeno_sangre'] = self.valor
        return d

class Peso(HealthMetricMixin, db.Model):
    valor = db.Column(db.Float, nullable=False)
    __tablename__ = 'peso'
    def to_dict(self):
        d = super().to_dict()
        d['peso'] = self.valor
        return d

class Altura(HealthMetricMixin, db.Model):
    valor = db.Column(db.Float, nullable=False)
    __tablename__ = 'altura'
    def to_dict(self):
        d = super().to_dict()
        d['altura'] = self.valor
        return d


# Mapa de modelos y reglas de validación
MODELS_MAP = {
    'ritmo_cardiaco': {'model': RitmoCardiaco, 'min': 30, 'max': 200, 'type': int, 'unit': 'ppm'},
    'presion_sistolica': {'model': PresionArterial, 'min': 70, 'max': 250, 'type': int, 'unit': 'mmHg'},
    'presion_diastolica': {'model': PresionArterial, 'min': 40, 'max': 150, 'type': int, 'unit': 'mmHg'},
    'nivel_azucar': {'model': NivelAzucar, 'min': 50, 'max': 600, 'type': float, 'unit': 'mg/dL'},
    'colesterol': {'model': Colesterol, 'min': 60, 'max': 500, 'type': float, 'unit': 'mg/dL'},
    'oxigeno_sangre': {'model': OxigenoSangre, 'min': 70, 'max': 100, 'type': float, 'unit': '%'},
    'peso': {'model': Peso, 'min': 0.1, 'max': 400.0, 'type': float, 'unit': 'kg'},
    'altura': {'model': Altura, 'min': 10.0, 'max': 300.0, 'type': float, 'unit': 'cm'},
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

    # (La línea de "RegistroMedico" fue eliminada)

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

def validar_valor_individual(nombre_campo, valor_str):
    config = MODELS_MAP.get(nombre_campo)
    if not config:
        return f"Campo desconocido: {nombre_campo}"

    try:
        # Convertir a tipo numérico según la configuración
        if config['type'] == int:
            valor = int(valor_str)
        elif config['type'] == float:
            valor = float(valor_str)
        else:
            return "Tipo de dato no soportado para validación."
    except ValueError:
        return f"Error: '{valor_str}' no es un valor numérico válido para {nombre_campo.replace('_', ' ')}."

    if valor < config['min'] or valor > config['max']:
        return f"{nombre_campo.replace('_', ' ').capitalize()} fuera del rango válido ({config['min']}-{config['max']} {config['unit']})"
    
    return None, valor



@app.route('/inicio')
def inicio():
    return render_template("inicio_salud.html")

# Función auxiliar para obtener el último registro de cada métrica
def get_latest_record(model_class, user_id):
    return model_class.query.filter_by(usuario_id=user_id).order_by(model_class.fecha.desc()).first()

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    user_id = session['usuario_id']
    
    # Obtener el último registro de cada métrica
    latest_metrics = {
        'ritmo_cardiaco': get_latest_record(RitmoCardiaco, user_id),
        'presion_arterial': get_latest_record(PresionArterial, user_id),
        'nivel_azucar': get_latest_record(NivelAzucar, user_id),
        'colesterol': get_latest_record(Colesterol, user_id),
        'oxigeno_sangre': get_latest_record(OxigenoSangre, user_id),
        'peso': get_latest_record(Peso, user_id),
        'altura': get_latest_record(Altura, user_id),
    }
    
    # La plantilla 'index.html' necesitará adaptarse para mostrar este diccionario
    return render_template('index.html', latest_metrics=latest_metrics)

METRIC_OPTIONS = {
    'ritmo_cardiaco': 'Ritmo Cardíaco (ppm)',
    'presion_arterial': 'Presión Arterial (Sistólica/Diastólica)',
    'nivel_azucar': 'Nivel de Azúcar (mg/dL)',
    'colesterol': 'Colesterol (mg/dL)',
    'oxigeno_sangre': 'Oxígeno en Sangre (%)',
    'peso': 'Peso (kg)',
    'altura': 'Altura (cm)',
}



@app.route('/agregar')
def agregar_registro():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para agregar un registro.", "error")
        return redirect(url_for('login'))

    
    return render_template('agregar_botones.html', metric_options=METRIC_OPTIONS)


@app.route('/agregar/<string:metrica>', methods=['GET', 'POST'])
def agregar_metrica_individual(metrica):
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para agregar un registro.", "error")
        return redirect(url_for('login'))

    # Si es presión, se usa una plantilla especial para dos campos
    if metrica == 'presion_arterial':
        return manejar_presion_arterial()
    
    # Manejar métricas de valor único (Ritmo, Peso, Altura, Azúcar, etc.)
    
    # Mapear el nombre de la URL a la configuración de la métrica
    config = MODELS_MAP.get(metrica) 
    
    # El mapa MODELS_MAP debe ser ajustado, ya que en el código anterior
    # las claves son 'ritmo_cardiaco', 'peso', etc. y no 'ritmo_cardiaco', 'presion_arterial', etc.
    # El mapa debería ser:
    # 'ritmo_cardiaco': {'model': RitmoCardiaco, 'min': 30, 'max': 200, 'type': int, 'unit': 'ppm', 'db_field': 'valor'},
    # 'peso': {'model': Peso, 'min': 0.1, 'max': 400.0, 'type': float, 'unit': 'kg', 'db_field': 'valor'},
    # ...
    
    if not config or not METRIC_OPTIONS.get(metrica):
        abort(404) # Métrica no válida

    metric_title = METRIC_OPTIONS.get(metrica)

    if request.method == 'POST':
        # La lógica de validación debe usar el nombre real del campo de entrada, que será 'valor'
        valor_str = request.form.get('valor') 
        
        # Usamos la función de validación ajustada
        # NOTA: La validación es compleja porque 'ritmo_cardiaco' no está en MODELS_MAP con 'db_field':'valor'. 
        # Si la llave es 'ritmo_cardiaco', se debe usar: validar_valor_individual('ritmo_cardiaco', valor_str)
        # Asumiendo que has ajustado MODELS_MAP para que las llaves correspondan
        error, valor_limpio = validar_valor_individual(metrica, valor_str)

        if error:
            flash(error, 'error')
            return render_template('formulario_individual.html', metrica=metrica, metric_title=metric_title, unit=config.get('unit'))

        try:
            Modelo = config['model']
            usuario_id = session['usuario_id']
            
            # Crear el objeto dinámicamente
            nuevo_registro = Modelo(valor=valor_limpio, usuario_id=usuario_id)
            
            db.session.add(nuevo_registro)
            db.session.commit()
            flash(f'{metric_title} guardado exitosamente.', 'success')
            return redirect(url_for('agregar_registro'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'error')

    return render_template('formulario_individual.html', 
                           metrica=metrica, 
                           metric_title=metric_title, 
                           unit=config.get('unit'),
                           min_val=config.get('min'),
                           max_val=config.get('max'),
                           step=0.1 if config.get('type') == float else 1)
                           
                           
def manejar_presion_arterial():
    # Lógica específica para Presión Arterial (dos campos)
    config_sistolica = MODELS_MAP.get('presion_sistolica')
    config_diastolica = MODELS_MAP.get('presion_diastolica')

    if request.method == 'POST':
        sistolica_str = request.form.get('sistolica')
        diastolica_str = request.form.get('diastolica')
        
        error_sistolica, sistolica_limpia = validar_valor_individual('presion_sistolica', sistolica_str)
        error_diastolica, diastolica_limpia = validar_valor_individual('presion_diastolica', diastolica_str)
        
        errores = []
        if error_sistolica: errores.append(error_sistolica)
        if error_diastolica: errores.append(error_diastolica)

        if errores:
            for error in errores: flash(error, 'error')
            return render_template('formulario_presion.html', sistolica_config=config_sistolica, diastolica_config=config_diastolica)

        try:
            nuevo_registro = PresionArterial(
                sistolica=sistolica_limpia,
                diastolica=diastolica_limpia,
                usuario_id=session['usuario_id']
            )
            db.session.add(nuevo_registro)
            db.session.commit()
            flash('Presión Arterial guardada exitosamente.', 'success')
            return redirect(url_for('agregar_registro'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la presión arterial: {str(e)}', 'error')

    return render_template('formulario_presion.html', sistolica_config=config_sistolica, diastolica_config=config_diastolica)

@app.route('/historial')
def historial():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para ver el historial.", "error")
        return redirect(url_for('login'))
        
    user_id = session['usuario_id']
    
    # Se consulta el historial de cada tabla por separado
    historial_data = {
        'ritmos_cardiacos': RitmoCardiaco.query.filter_by(usuario_id=user_id).order_by(RitmoCardiaco.fecha.desc()).all(),
        'presiones': PresionArterial.query.filter_by(usuario_id=user_id).order_by(PresionArterial.fecha.desc()).all(),
        'niveles_azucar': NivelAzucar.query.filter_by(usuario_id=user_id).order_by(NivelAzucar.fecha.desc()).all(),
        'colesteroles': Colesterol.query.filter_by(usuario_id=user_id).order_by(Colesterol.fecha.desc()).all(),
        'oxigenos': OxigenoSangre.query.filter_by(usuario_id=user_id).order_by(OxigenoSangre.fecha.desc()).all(),
        'pesos': Peso.query.filter_by(usuario_id=user_id).order_by(Peso.fecha.desc()).all(),
        'alturas': Altura.query.filter_by(usuario_id=user_id).order_by(Altura.fecha.desc()).all(),
    }
    
    # La plantilla 'historial.html' debe adaptarse para mostrar las tablas por separado.
    return render_template('historial.html', historial_data=historial_data)


@app.route('/estadisticas')
def estadisticas():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para ver estadísticas.", "error")
        return redirect(url_for('login'))
        
    user_id = session['usuario_id']
    
    estadisticas_data = {}
    has_data = False

    # Métricas con columna 'valor'
    single_value_metrics = [
        ('Ritmo Cardíaco', RitmoCardiaco, RitmoCardiaco.valor, 'ppm'),
        ('Nivel de Azúcar', NivelAzucar, NivelAzucar.valor, 'mg/dL'),
        ('Colesterol', Colesterol, Colesterol.valor, 'mg/dL'),
        ('Oxígeno en Sangre', OxigenoSangre, OxigenoSangre.valor, '%'),
        ('Peso', Peso, Peso.valor, 'kg'),
        ('Altura', Altura, Altura.valor, 'cm'),
    ]

    # Calcular estadísticas para métricas de valor único
    for nombre, model, column, unit in single_value_metrics:
        resultado = db.session.query(
            func.avg(column).label('promedio'),
            func.min(column).label('minimo'),
            func.max(column).label('maximo'),
            func.count(column).label('conteo')
        ).filter(model.usuario_id == user_id).first()

        if resultado.conteo > 0:
            has_data = True
            estadisticas_data[nombre] = {
                'promedio': f"{resultado.promedio:.2f}",
                'minimo': f"{resultado.minimo}",
                'maximo': f"{resultado.maximo}",
                'unit': unit
            }

    # Caso especial: Presión Arterial
    pa_results = db.session.query(
        func.avg(PresionArterial.sistolica).label('avg_sistolica'),
        func.min(PresionArterial.sistolica).label('min_sistolica'),
        func.max(PresionArterial.sistolica).label('max_sistolica'),
        func.avg(PresionArterial.diastolica).label('avg_diastolica'),
        func.min(PresionArterial.diastolica).label('min_diastolica'),
        func.max(PresionArterial.diastolica).label('max_diastolica'),
        func.count(PresionArterial.sistolica).label('conteo')
    ).filter(PresionArterial.usuario_id == user_id).first()

    if pa_results and pa_results.conteo > 0:
        has_data = True
        estadisticas_data['Presión Sistólica'] = {
            'promedio': f"{pa_results.avg_sistolica:.2f}",
            'minimo': f"{pa_results.min_sistolica}",
            'maximo': f"{pa_results.max_sistolica}",
            'unit': 'mmHg'
        }
        estadisticas_data['Presión Diastólica'] = {
            'promedio': f"{pa_results.avg_diastolica:.2f}",
            'minimo': f"{pa_results.min_diastolica}",
            'maximo': f"{pa_results.max_diastolica}",
            'unit': 'mmHg'
        }

    if not has_data:
        flash('No hay datos suficientes para mostrar estadísticas.', 'info')
        return render_template('estadisticas.html', estadisticas=None)

    return render_template('estadisticas.html', estadisticas=estadisticas_data)

def clasificar_imc(imc):
    if imc < 18.5:
        return ("Bajo Peso", "notification is-warning")
    elif 18.5 <= imc < 25:
        return ("Peso Saludable", "notification is-success")
    elif 25 <= imc < 30:
        return ("Sobrepeso", "notification is-warning")
    elif 30 <= imc < 35:
        return ("Obesidad Clase I", "notification is-danger")
    elif 35 <= imc < 40:
        return ("Obesidad Clase II", "notification is-danger")
    else:
        return ("Obesidad Clase III (Mórbida)", "notification is-danger")


@app.route('/calcular_imc')
def calcular_imc():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión para calcular el IMC.", "error")
        return redirect(url_for('login'))
        
    user_id = session['usuario_id']

    # 1. Obtener los últimos registros de Peso y Altura
    ultimo_peso = Peso.query.filter_by(usuario_id=user_id).order_by(Peso.fecha.desc()).first()
    ultima_altura = Altura.query.filter_by(usuario_id=user_id).order_by(Altura.fecha.desc()).first()

    if not ultimo_peso or not ultima_altura:
        flash("Necesitas registrar tu Peso y tu Altura para calcular el IMC.", "info")
        return redirect(url_for('agregar_registro'))

    peso_kg = ultimo_peso.valor
    # La altura se guarda en cm, se convierte a metros
    altura_m = ultima_altura.valor / 100 
    
    # 2. Calcular IMC (Peso / Altura^2)
    if altura_m <= 0:
        flash("Error: El valor de la altura no es válido.", "error")
        return redirect(url_for('agregar_registro'))
        
    imc = peso_kg / (altura_m ** 2)
    
    # 3. Clasificar IMC
    clasificacion, estilo = clasificar_imc(imc)
    
    datos_imc = {
        'imc': f'{imc:.2f}',
        'clasificacion': clasificacion,
        'estilo': estilo,
        'peso': peso_kg,
        'altura': ultima_altura.valor,
        'fecha_peso': ultimo_peso.fecha.strftime('%Y-%m-%d %H:%M'),
        'fecha_altura': ultima_altura.fecha.strftime('%Y-%m-%d %H:%M')
    }

    return render_template('mostrar_imc.html', datos_imc=datos_imc)

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash("Sesión cerrada", "info")
    return redirect(url_for('login'))
    
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nameUser']
        password = request.form['passwordUser']
        email = request.form['emailUser']
        edad = request.form.get('edadUser', type=int)
        sexo = request.form.get('sexoUser')
        telefono = request.form.get('telefonoUser')
        if Usuario.query.filter_by(nombre=nombre).first():
            flash("Ese usuario ya existe", "error")
            return redirect(url_for('registro'))
            
        if Usuario.query.filter_by(email=email).first():
            flash("Ese correo electrónico ya está registrado", "error")
            return redirect(url_for('registro'))

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email, # Asignar el email
            edad=edad, # Asignar la edad
            sexo=sexo, # Asignar el sexo
            telefono=telefono # Asignar el teléfono
        )
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

        # ... (código de print omitido) ...
        usuario = Usuario.query.filter_by(nombre=nombre).first()

        if usuario:
            # ... (código de print omitido) ...
            if usuario.check_password(password):
                print("Contraseña correcta. Iniciando sesión...")
                
                # --- AÑADE ESTA LÍNEA CRUCIAL ---
                session['usuario_id'] = usuario.id
                session['rol'] = usuario.rol  # <--- GUARDAR EL ROL EN LA SESIÓN
                # --------------------------------
                
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

#def rol_requerido(rol):
 #      @wraps(f)
#      def decorated_function(*args, **kwargs):
 #           if 'usuario_id' not in session:
  #              flash("Debes iniciar sesión para acceder.", "error")
   #             return redirect(url_for('login'))
    #        
     #       usuario = Usuario.query.get(session['usuario_id'])
      #      if not usuario or usuario.rol != rol:
 #               flash("No tienes permisos para acceder a esta página.", "error")
#                return redirect(url_for('inicio'))
 #           return f(*args, **kwargs)
#        return decorated_function
 #   return decorator

# Coloca esta función antes de cualquier ruta que la use (al inicio de tu app.py)
@app.route('/admin/dashboard', methods=['GET'])
@rol_requerido('admin')
def admin_dashboard():
    
    search_query = request.args.get('q', '').strip()

    if search_query:
        
        usuarios = Usuario.query.filter(
            (Usuario.nombre.ilike(f'%{search_query}%')) | 
            (Usuario.email.ilike(f'%{search_query}%'))
        ).all()
        
        if not usuarios:
            flash(f"No se encontraron pacientes con el término '{search_query}'.", 'info')
    else:
       
        usuarios = Usuario.query.all()
        
    
    return render_template('admin_dashboard.html', 
                           usuarios=usuarios, 
                           search_query=search_query,
                           registros={})

@app.route('/admin/registros/<int:usuario_id>')
@rol_requerido('admin')
def ver_usuario_registros(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    historial_data = {
        'ritmos_cardiacos': RitmoCardiaco.query.filter_by(usuario_id=usuario_id).order_by(RitmoCardiaco.fecha.desc()).all(),
        'presiones': PresionArterial.query.filter_by(usuario_id=usuario_id).order_by(PresionArterial.fecha.desc()).all(),
        'niveles_azucar': NivelAzucar.query.filter_by(usuario_id=usuario_id).order_by(NivelAzucar.fecha.desc()).all(),
        'colesteroles': Colesterol.query.filter_by(usuario_id=usuario_id).order_by(Colesterol.fecha.desc()).all(),
        'oxigenos': OxigenoSangre.query.filter_by(usuario_id=usuario_id).order_by(OxigenoSangre.fecha.desc()).all(),
        'pesos': Peso.query.filter_by(usuario_id=usuario_id).order_by(Peso.fecha.desc()).all(),
        'alturas': Altura.query.filter_by(usuario_id=usuario_id).order_by(Altura.fecha.desc()).all(),
    }
    # La plantilla 'ver_registros_usuario.html' debe adaptarse para mostrar estas tablas.
    return render_template('ver_registros_usuario.html', usuario=usuario, historial_data=historial_data)
    
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
        # Eliminar registros de TODAS las tablas de métricas
        RitmoCardiaco.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        PresionArterial.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        NivelAzucar.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        Colesterol.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        OxigenoSangre.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        Peso.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        Altura.query.filter_by(usuario_id=usuario_id).delete(synchronize_session=False)
        
        db.session.delete(usuario)
        db.session.commit()
        flash(f'El usuario {usuario.nombre} y todos sus registros han sido eliminados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))

# Nueva ruta de eliminación para un registro individual de una tabla específica
@app.route('/admin/eliminar/registro/<string:modelo_nombre>/<int:registro_id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_registro(modelo_nombre, registro_id):
    MODEL_CLASSES = {
        'ritmo_cardiaco': RitmoCardiaco,
        'presion_arterial': PresionArterial,
        'nivel_azucar': NivelAzucar,
        'colesterol': Colesterol,
        'oxigeno_sangre': OxigenoSangre,
        'peso': Peso,
        'altura': Altura,
    }
    
    Modelo = MODEL_CLASSES.get(modelo_nombre)
    if not Modelo:
        flash(f'Error: Modelo {modelo_nombre} no encontrado.', 'error')
        return redirect(url_for('admin_dashboard'))

    registro = Modelo.query.get_or_404(registro_id)
    usuario_id = registro.usuario_id

    try:
        db.session.delete(registro)
        db.session.commit()
        flash(f'Registro de {modelo_nombre.replace("_", " ")} eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el registro: {str(e)}', 'error')
    
    return redirect(url_for('ver_usuario_registros', usuario_id=usuario_id))
    
@app.route('/admin/editar/registro/<string:modelo_nombre>/<int:registro_id>', methods=['GET', 'POST'])
@rol_requerido('admin')
def editar_registro(modelo_nombre, registro_id):
    MODEL_CLASSES = {
        'ritmo_cardiaco': RitmoCardiaco,
        'presion_arterial': PresionArterial,
        'nivel_azucar': NivelAzucar,
        'colesterol': Colesterol,
        'oxigeno_sangre': OxigenoSangre,
        'peso': Peso,
        'altura': Altura,
    }
    Modelo = MODEL_CLASSES.get(modelo_nombre)
    if not Modelo:
        flash(f'Error: Modelo {modelo_nombre} no encontrado.', 'error')
        return redirect(url_for('admin_dashboard'))

    registro = Modelo.query.get_or_404(registro_id)
    # Asumimos que MODELS_MAP y METRIC_OPTIONS son globales o accesibles.
    
    if request.method == 'POST':
        # --- Lógica POST (Guardar cambios) ---
        
        if modelo_nombre == 'presion_arterial':
            # Caso especial: Presión Arterial (dos campos)
            sistolica_str = request.form.get('sistolica')
            diastolica_str = request.form.get('diastolica')
            
            error_sistolica, sistolica_limpia = validar_valor_individual('presion_sistolica', sistolica_str)
            error_diastolica, diastolica_limpia = validar_valor_individual('presion_diastolica', diastolica_str)

            errores = []
            if error_sistolica: errores.append(error_sistolica)
            if error_diastolica: errores.append(error_diastolica)

            if errores:
                for error in errores: flash(error, 'error')
                return redirect(url_for('editar_registro', modelo_nombre=modelo_nombre, registro_id=registro_id))

            registro.sistolica = sistolica_limpia
            registro.diastolica = diastolica_limpia

        else: # Métricas de valor único
            valor_str = request.form.get('valor')
            
            error, valor_limpio = validar_valor_individual(modelo_nombre, valor_str)

            if error:
                flash(error, 'error')
                return redirect(url_for('editar_registro', modelo_nombre=modelo_nombre, registro_id=registro_id))

            registro.valor = valor_limpio
        
        # Guardar en la DB
        try:
            db.session.commit()
            flash(f'Registro de {modelo_nombre.replace("_", " ")} actualizado exitosamente.', 'success')
            return redirect(url_for('ver_usuario_registros', usuario_id=registro.usuario_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la edición: {str(e)}', 'error')
            return redirect(url_for('ver_usuario_registros', usuario_id=registro.usuario_id))

    else:
        # --- Lógica GET (Mostrar formulario) ---
        metric_title = METRIC_OPTIONS.get(modelo_nombre)
        
        if modelo_nombre == 'presion_arterial':
            sistolica_config = MODELS_MAP.get('presion_sistolica')
            diastolica_config = MODELS_MAP.get('presion_diastolica')
            
            return render_template('formulario_edicion_presion.html',
                                   registro=registro,
                                   modelo_nombre=modelo_nombre,
                                   metric_title=metric_title,
                                   sistolica_config=sistolica_config,
                                   diastolica_config=diastolica_config)
        else:
            config = MODELS_MAP.get(modelo_nombre)
            return render_template('formulario_edicion_individual.html',
                                   registro=registro,
                                   modelo_nombre=modelo_nombre,
                                   metric_title=metric_title,
                                   config=config)

UPLOAD_FOLDER = 'static/uploads/consejos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Consejo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    tema = db.Column(db.String(50), nullable=False) # Ej: Nutrición, Ejercicio, Sueño
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    imagen_url = db.Column(db.String(255)) # Ruta del archivo de imagen
    
    usuario_admin_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    admin = db.relationship('Usuario', backref='consejos')

    def __repr__(self):
        return f'<Consejo {self.titulo}>'

@app.route('/consejos', methods=['GET'])
def consejos():
    # Obtiene el término de búsqueda y el filtro de tema de la URL
    query = request.args.get('q', '').strip()
    tema_filtro = request.args.get('tema', '').strip()
    
    consejos_query = Consejo.query.order_by(Consejo.fecha.desc())
    
    # Aplicar filtro de búsqueda (por título o contenido)
    if query:
        consejos_query = consejos_query.filter(
            (Consejo.titulo.ilike(f'%{query}%')) | 
            (Consejo.contenido.ilike(f'%{query}%'))
        )
        
    # Aplicar filtro de tema
    if tema_filtro and tema_filtro != 'todos':
        consejos_query = consejos_query.filter_by(tema=tema_filtro)

    consejos_lista = consejos_query.all()
    
    # Obtener todos los temas únicos para el menú desplegable
    temas_unicos = db.session.query(Consejo.tema).distinct().all()
    temas_unicos = [t[0] for t in temas_unicos]

    return render_template('consejos.html', 
                           consejos=consejos_lista,
                           temas_unicos=temas_unicos,
                           query=query,
                           tema_filtro=tema_filtro)


@app.route('/admin/agregar_consejo', methods=['GET', 'POST'])
@rol_requerido('admin')
def agregar_consejo():
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        tema = request.form['tema']
        imagen = request.files.get('imagen')
        imagen_url = None
        
        if imagen and allowed_file(imagen.filename):
            try:
                # 1. Asegurar nombre de archivo
                filename = secure_filename(imagen.filename)
                
                # 2. Guardar el archivo en la carpeta de uploads
                path_to_save = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(path_to_save)
                
                # 3. Guardar la URL relativa para la DB
                imagen_url = url_for('static', filename=f'uploads/consejos/{filename}')
                
            except Exception as e:
                flash(f'Error al subir la imagen: {e}', 'error')
                return redirect(url_for('agregar_consejo'))

        nuevo_consejo = Consejo(
            titulo=titulo,
            contenido=contenido,
            tema=tema,
            imagen_url=imagen_url,
            usuario_admin_id=session.get('usuario_id') 
        )
        
        try:
            db.session.add(nuevo_consejo)
            db.session.commit()
            flash(f'Consejo "{titulo}" agregado exitosamente!', 'success')
            return redirect(url_for('consejos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el consejo: {str(e)}', 'error')
            
   
    temas_predefinidos = ['Nutrición', 'Ejercicio', 'Sueño', 'Estrés', 'Higiene','Diabetes','General']
    
    return render_template('agregar_consejo.html', temas_predefinidos=temas_predefinidos)
    


@app.route('/consejo/<int:consejo_id>')
def ver_consejo(consejo_id):
    """Muestra la página de detalles de un consejo específico."""
    
    consejo = Consejo.query.get_or_404(consejo_id)
    return render_template('consejo_detalle.html', consejo=consejo)

@app.route('/admin/editar_consejo/<int:consejo_id>', methods=['GET', 'POST'])
@rol_requerido('admin')
def editar_consejo(consejo_id):
    consejo = Consejo.query.get_or_404(consejo_id)
    temas_predefinidos = ['Nutrición', 'Ejercicio', 'Sueño', 'Estrés','Diabetes', 'Higiene', 'General']

    if request.method == 'POST':
        consejo.titulo = request.form['titulo']
        consejo.contenido = request.form['contenido']
        consejo.tema = request.form['tema']
        imagen = request.files.get('imagen')
        
        # Lógica para manejar la nueva imagen
        if imagen and allowed_file(imagen.filename):
            try:
                # Opcional: Eliminar imagen antigua si existe
                if consejo.imagen_url:
                    # Convierte la URL a ruta de sistema de archivos
                    old_filename = consejo.imagen_url.split('/')[-1]
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                        
                # 1. Guardar nueva imagen
                filename = secure_filename(imagen.filename)
                path_to_save = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(path_to_save)
                
                # 2. Actualizar la URL en la DB
                consejo.imagen_url = url_for('static', filename=f'uploads/consejos/{filename}')
                
            except Exception as e:
                flash(f'Error al subir la nueva imagen: {e}', 'error')
                return redirect(url_for('editar_consejo', consejo_id=consejo.id))

        try:
            db.session.commit()
            flash(f'Consejo "{consejo.titulo}" actualizado exitosamente!', 'success')
            return redirect(url_for('ver_consejo', consejo_id=consejo.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la edición: {str(e)}', 'error')
            
    return render_template('editar_consejo.html', 
                           consejo=consejo, 
                           temas_predefinidos=temas_predefinidos)
    
@app.route('/admin/eliminar_consejo/<int:consejo_id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_consejo(consejo_id):
    consejo = Consejo.query.get_or_404(consejo_id)
    titulo_consejo = consejo.titulo
    
    try:
        # Opcional: Eliminar la imagen del servidor antes de borrar el registro
        if consejo.imagen_url:
            # Convierte la URL a ruta de sistema de archivos
            filename = consejo.imagen_url.split('/')[-1]
            path_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(path_to_delete):
                os.remove(path_to_delete)
        
        db.session.delete(consejo)
        db.session.commit()
        flash(f'El consejo "{titulo_consejo}" ha sido eliminado exitosamente.', 'success')
        return redirect(url_for('consejos'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el consejo: {str(e)}', 'error')
        return redirect(url_for('consejos'))
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True,host='0.0.0.0',port=5000)