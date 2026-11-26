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
        "description": "Documentación de endpoints para autenticación, reservas, productos, apartados, seguimiento y foro.",
        "version": "1.0.0"
    },
    "basePath": "/",
}

swagger = Swagger(template=swagger_template)


def get_db_connection(app_config):
    return pymysql.connect(**app_config['DB_CONFIG'])