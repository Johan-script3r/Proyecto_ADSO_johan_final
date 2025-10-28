from app import app, db, Usuario
with app.app_context():
    # Crea un nuevo usuario normal
    admin_usuario = Usuario(nombre='administrador', rol='admin')
    # Asigna la contraseña (cámbiala por una segura)
    admin_usuario.set_password('administrador')
    # Agrega y guarda el usuario
    db.session.add(admin_usuario)
    db.session.commit()
    print("Administrador creado exitosamente")