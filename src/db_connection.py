import mysql.connector
from mysql.connector import errorcode
from . import config
    

class DBConnector(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(DBConnector)
            return cls.instance
        return cls.instance

    def __init__(self, user, passwd, db):
        self.user = user
        self.passwd = passwd
        self.db = db
        self.create_connection()

    def create_connection(self):   
        self.cnx = mysql.connector.connect(user=self.user, passwd = self.passwd,database= self.db)
        self.cursor = self.cnx.cursor()
        self.cnx._open_connection()
        return self.cursor

    def query(self, sql_statement, val):
        self.cursor.execute(sql_statement, val)
        return self.cursor.fetchall()
    
    def simple_query(self, sql_statement):
        self.cursor.execute(sql_statement)
        return self.cursor.fetchall()
    
    def insert(self, sql_statement, val):
        self.cursor.execute(sql_statement, val)
        self.cnx.commit()
    
    def update():
        pass

    def close_connection(self):
        self.cursor.close()