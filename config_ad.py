from app import app, db, Usuario

# --- 1. CONFIGURACIÓN ---
# Define los datos para el nuevo usuario administrador
ADMIN_NOMBRE = 'administrador'
ADMIN_PASSWORD = 'administrador' # ! CAMBIA ESTO !
ADMIN_EMAIL = 'admin@miaplicacion.com' # Correo es obligatorio

# --- 2. LÓGICA DE CREACIÓN ---
with app.app_context():
    
    # Verifica si el usuario ya existe
    if Usuario.query.filter_by(nombre=ADMIN_NOMBRE).first():
        print(f"❌ ERROR: El usuario '{ADMIN_NOMBRE}' ya existe.")
    
    else:
        # Crea el usuario, incluyendo los nuevos campos opcionales (edad, sexo, teléfono)
        # y el campo obligatorio 'email'.
        admin_usuario = Usuario(
            nombre=ADMIN_NOMBRE,
            email=ADMIN_EMAIL, 
            rol='admin',
            # Los siguientes campos son opcionales y se omiten,
            # o puedes añadirles valores iniciales si lo deseas:
            # edad=30,
            # sexo='masculino',
            # telefono='1234567890'
        )
        
        # Asigna y hashea la contraseña
        admin_usuario.set_password(ADMIN_PASSWORD)
        
        # Agrega y guarda el usuario
        try:
            db.session.add(admin_usuario)
            db.session.commit()
            print(f"✅ Administrador '{ADMIN_NOMBRE}' creado exitosamente.")
            print(f"   Contraseña: {ADMIN_PASSWORD}")
            print(f"   Email: {ADMIN_EMAIL}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al guardar en la base de datos: {e}")