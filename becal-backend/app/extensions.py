from flask_mail import Mail
from flask_cors import CORS
import pymysql

mail = Mail()
cors = CORS()

def get_db_connection(app_config):
    return pymysql.connect(**app_config['DB_CONFIG'])