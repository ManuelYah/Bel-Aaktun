"""Utilidades de administración.

    python manage.py crear-admin correo@ejemplo.com            (pide la contraseña)
    python manage.py crear-admin correo@ejemplo.com --nombre "Ana"

Si el correo ya es de un administrador, solo cambia su contraseña. Con Docker:

    docker compose exec backend python manage.py crear-admin correo@ejemplo.com
"""
import argparse
import getpass
import os
import sys

from app import create_app
from app.extensions import get_db_connection
from app.security import ROL_ADMIN, hash_password


def crear_admin(email, nombre, password):
    app = create_app()
    email = email.strip().lower()
    with app.app_context():
        conn = get_db_connection(app.config)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, rol FROM usuarios WHERE LOWER(email) = %s", (email,))
                existente = cursor.fetchone()
                if existente and existente["rol"] != ROL_ADMIN:
                    print(f"{email} es una cuenta de artesano; usa otro correo.", file=sys.stderr)
                    return 1
                if existente:
                    cursor.execute(
                        "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                        (hash_password(password), existente["id"]),
                    )
                    print(f"Contraseña actualizada para {email}.")
                else:
                    cursor.execute(
                        "INSERT INTO usuarios (nombre, email, password_hash, taller_id, rol) "
                        "VALUES (%s, %s, %s, NULL, %s)",
                        (nombre, email, hash_password(password), ROL_ADMIN),
                    )
                    print(f"Administrador creado: {email}")
            conn.commit()
        finally:
            conn.close()
    return 0


def sembrar_e2e():
    """Deja listos los datos que usan las pruebas Selenium (idempotente).

    Variables: E2E_ADMIN_EMAIL, E2E_ADMIN_PASSWORD, E2E_ARTESANO_EMAIL, E2E_ARTESANO_PASSWORD.
    Crea/actualiza el administrador de pruebas, fija la contraseña de un artesano existente
    y garantiza que haya un producto "E2E Producto borrable" para probar la eliminación.
    """
    admin_email = os.getenv("E2E_ADMIN_EMAIL", "e2e-admin@belaaktun.test")
    admin_pass = os.getenv("E2E_ADMIN_PASSWORD", "")
    art_email = os.getenv("E2E_ARTESANO_EMAIL", "acosta@belaaktun.com").strip().lower()
    art_pass = os.getenv("E2E_ARTESANO_PASSWORD", "")
    if len(admin_pass) < 10 or len(art_pass) < 6:
        print("Define E2E_ADMIN_PASSWORD (min. 10) y E2E_ARTESANO_PASSWORD (min. 6).", file=sys.stderr)
        return 1
    codigo = crear_admin(admin_email, "Admin E2E", admin_pass)
    if codigo:
        return codigo
    app = create_app()
    with app.app_context():
        conn = get_db_connection(app.config)
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE usuarios SET password_hash = %s WHERE LOWER(email) = %s",
                    (hash_password(art_pass), art_email),
                )
                if cursor.rowcount == 0:
                    print(f"No existe el artesano {art_email}.", file=sys.stderr)
                    return 1
                cursor.execute("SELECT id FROM artesanos ORDER BY id LIMIT 1")
                dueno = cursor.fetchone()
                cursor.execute("SELECT id FROM productos WHERE nombre_pieza = 'E2E Producto borrable' LIMIT 1")
                if dueno and not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO productos (artesano_id, nombre_pieza, descripcion, precio, calidad, imagenes) "
                        "VALUES (%s, 'E2E Producto borrable', 'Creado para pruebas automáticas', 1, 'Fina', '[]')",
                        (dueno["id"],),
                    )
            conn.commit()
        finally:
            conn.close()
    print("Datos E2E listos.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)
    admin = sub.add_parser("crear-admin", help="Crea un administrador o cambia su contraseña")
    admin.add_argument("email")
    admin.add_argument("--nombre", default="Administrador")
    sub.add_parser("sembrar-e2e", help="Prepara usuarios y datos para las pruebas Selenium")
    args = parser.parse_args()

    if args.comando == "sembrar-e2e":
        return sembrar_e2e()

    password = getpass.getpass("Contraseña (mínimo 10 caracteres): ")
    if len(password) < 10:
        print("La contraseña debe tener al menos 10 caracteres.", file=sys.stderr)
        return 1
    if password != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.", file=sys.stderr)
        return 1
    return crear_admin(args.email, args.nombre, password)


if __name__ == "__main__":
    sys.exit(main())
