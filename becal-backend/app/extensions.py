from flask_mail import Mail
from flask_cors import CORS
from flasgger import Swagger
import pymysql

mail = Mail()
cors = CORS()

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Bel-Aaktun Touring & Artesanías API",
        "description": (
            "Documentación de endpoints para autenticación, reservas, productos, "
            "apartados, seguimiento, foro, contacto y administración. "
            "Los endpoints protegidos usan el encabezado "
            "`Authorization: Bearer <token>` (el token se obtiene en /api/auth/login)."
        ),
        "version": "1.1.0",
    },
    "basePath": "/",
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Escribe: Bearer <token>",
        }
    },
}

swagger = Swagger(template=swagger_template)


def get_db_connection(app_config):
    return pymysql.connect(**app_config["DB_CONFIG"])
