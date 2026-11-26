# Despliegue y pruebas Selenium

Todo corre con Docker Compose: **MySQL + backend Flask + nginx (Angular)**. Solo el puerto 80 queda abierto.

## 1. Servidor
Cualquier VPS con Ubuntu 22.04/24.04, 2 GB de RAM mínimo (la primera compilación de Angular consume memoria).

```bash
curl -fsSL https://get.docker.com | sh          # instala Docker + Compose
sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw enable
git clone <tu-repo> bel-aaktun && cd bel-aaktun
cp .env.example .env && nano .env
```

En `.env` completa como mínimo:
- `MYSQL_ROOT_PASSWORD`, `DB_PASSWORD`
- `SECRET_KEY` → `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `ADMIN_EMAIL` y `ADMIN_PASSWORD` (mín. 10 caracteres): el administrador se crea solo al arrancar
- `E2E_ADMIN_PASSWORD` (mín. 10) y `E2E_ARTESANO_PASSWORD` (mín. 6) para las pruebas
- `CONTACTO_MAX_POR_HORA=100` mientras pruebas (si no, el límite de 5 mensajes/hora frenará a Selenium)
- `MAIL_USERNAME`/`MAIL_PASSWORD` solo si quieres correos reales (nueva contraseña de aplicación de Gmail; **revoca la que estaba en el repositorio**). Vacío = no se envían correos.

## 2. Levantar
```bash
docker compose up -d --build
docker compose ps          # los 4 servicios deben estar "healthy"/"running"
```
Abre `http://IP-DEL-SERVIDOR/`. Swagger: `http://IP/apidocs/`. Panel admin: `/login` con `ADMIN_EMAIL`.

Si algo falla: `docker compose logs -f backend` / `web`.

## 3. Pruebas Selenium
```bash
./deploy/run-e2e.sh
```
El script siembra datos de prueba (admin de pruebas, contraseña del artesano `E2E_ARTESANO_EMAIL`, un producto «E2E Producto borrable»), levanta Chrome en un contenedor y ejecuta `e2e/tests`. El reporte queda en `e2e/reports/reporte.html` (más capturas de las pruebas que fallen).

Qué cubren: páginas cargan, catálogo, Swagger tras nginx, login incorrecto, rutas protegidas, cerrar sesión (artesano y admin), contacto → bandeja del admin, reserva → reseña pendiente → aprobada → visible en el foro, y eliminación de un producto por el admin.

> La prueba de eliminación borra el producto sembrado; `run-e2e.sh` lo vuelve a crear en cada corrida.

Contra otro sitio o con Chrome local (con ventana):
```bash
cd e2e && pip install -r requirements.txt
BASE_URL=http://IP E2E_ADMIN_PASSWORD=... E2E_ARTESANO_PASSWORD=... E2E_VISIBLE=1 pytest -v
```
(requiere haber corrido `sembrar-e2e` en el servidor.)

## 4. Después de la exposición
- Cambia las contraseñas de los artesanos (siguen en `123456` en `schema.sql`).
- Para HTTPS necesitas un dominio: apunta el DNS a la IP y añade Caddy o certbot delante de nginx.
- Actualizar: `git pull && docker compose up -d --build`.
- Respaldo: `docker compose exec mysql_db mysqldump -uroot -p$MYSQL_ROOT_PASSWORD becal_db > respaldo.sql`.
