import os

class Config(object):
    """Configure me so examples work
    
    Use me like this:
    
        mysql.connector.Connect(**Config.dbinfo())
    """
    INSTALL_PATH = os.getcwd()
    HOST = 'localhost'
    DATABASE = 'cs6400_fa21_team020'
    USER = 'root'
    PASSWORD = 'cs6400team20'
    PORT = 3306


    CHARSET = 'utf8'
    UNICODE = True
    WARNINGS = True
    
    @classmethod
    def dbinfo(cls):
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.DATABASE,
            'user': cls.USER,
            'password': cls.PASSWORD,
            'charset': cls.CHARSET,
            'use_unicode': cls.UNICODE,
            'get_warnings': cls.WARNINGS,
            }
    
    @classmethod
    def fileinfo(cls):
        schema = os.path.join(cls.INSTALL_PATH, "sql", "team020_p2_schema.sql")
        raw_data_dir = os.path.join(cls.INSTALL_PATH, "data")
        return {
            'schema': schema,
            'raw_data_dir': raw_data_dir
        }
