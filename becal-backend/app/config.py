import os
import pymysql

class Config:
    CORS_RESOURCES = {r"/api/*": {"origins": "*"}}
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'belaaktun@gmail.com'
    MAIL_PASSWORD = 'tvwc bwha ehta gtlf'
    MAIL_DEFAULT_SENDER = ('Bel-Aaktun Ruta de las Cuevas', 'belaaktun@gmail.com')
    
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', 3307)),
        'user': os.getenv('DB_USER', 'becal_user'),
        'password': os.getenv('DB_PASSWORD', 'becal_pass'),
        'database': os.getenv('DB_NAME', 'becal_db'),
        'cursorclass': pymysql.cursors.DictCursor
    }