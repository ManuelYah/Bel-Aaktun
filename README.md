# Becal-touring-System
Sistema de Gestión y Visibilidad para el Sector Turístico de Calkiní (con enfoque en los tejedores). Plataforma digital para que los artesanos tejedores de jipi de Becal y otros prestadores de servicios turísticos locales gestionen, visibilicen y comercialicen su oferta cultural y turística.

## Puesta en marcha

1. Copia `.env.example` como `.env` y llena los valores:
   - `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ADMIN_EMAIL` y `ADMIN_PASSWORD`: el administrador se crea al iniciar (mínimo 10 caracteres).
   - `MAIL_PASSWORD`: contraseña de aplicación de Gmail (nunca la subas al repositorio).
2. `docker compose up --build`
3. Frontend: `cd becal-frontend && npm install && npm start` (http://localhost:4200).
4. Documentación de la API: http://localhost:5000/apidocs

Para crear o cambiar la contraseña de un administrador después:

    docker compose exec backend python manage.py crear-admin correo@ejemplo.com

## Roles

- **Administrador** (`/admin`): aprueba o rechaza las reseñas antes de que salgan en el foro y lee los mensajes del formulario de contacto.
- **Artesano** (`/dashboard`): gestiona solo las reservas, apartados y productos de su taller.

Las reseñas nuevas (y las editadas) quedan **pendientes** hasta que el administrador las aprueba.

## Pruebas del backend

    cd becal-backend && python -m unittest discover -s tests -t . -v

Usan SQLite en memoria; no necesitan MySQL.
