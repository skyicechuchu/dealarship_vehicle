#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess, os, glob, re
import pandas as pd
import numpy as np
import csv
from subprocess import Popen, PIPE
from typing import Collection
import mysql.connector

class InitDB(object):
    
    def __init__(self, config):
        self.config = config
        self.db_connect = mysql.connector.Connect(host=config['host'],
                                user=config['user'],
                                password=config['password'])
        self.tbl = self.config['database']

    def check_drop_database_if_exists(self):
        cursor = self.db_connect.cursor()
        cursor.execute('SET sql_mode = ""')
        # Drop table if exists, and create it new
        stmt_drop = "DROP DATABASE IF EXISTS {0}".format(self.tbl)
        cursor.execute(stmt_drop)
        # Create A new database
        sql = "CREATE DATABASE IF NOT EXISTS {0} DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;".format(self.tbl)
        cursor.execute(sql)

    def create_table_with_sql(self, schema):
        cursor = self.db_connect.cursor()
        with open(schema) as f:
            sql_file = f.read()
            sql_commands = sql_file.split(";")

            for command in sql_commands:
                try:
                    if command.strip() != '':
                        cursor.execute(command)
                except IOError as msg:
                    print ("Create Table Command skipped: ", msg)


    def insert_raw_data(self, raw_data_dir):
        """ defin a data csv file with "insert_$table.csv"
        """
        cursor = self.db_connect.cursor()
        csv_file_container = glob.glob("{0}/insert_*.csv".format(raw_data_dir))
        table_container = {}
        for each_csv_file in csv_file_container:
            table_numer_string = re.match(r'insert_(.*)_([0-9]+).csv', os.path.basename(each_csv_file))
            table_container[int(table_numer_string[2])] = [table_numer_string[1], table_numer_string[0]]

        sorted_stable_container = dict(sorted(table_container.items()))
        for each in sorted_stable_container.values():
            table_name, each_csv_file = each[0], os.path.join(raw_data_dir, each[1])
            df = pd.read_csv(each_csv_file, index_col=False)
            empdata = df.replace({np.nan:None})

            head_string = ""
            for i, each in enumerate(list(empdata.columns)):
                if i == len(list(empdata.columns)) - 1:
                    head_string += each
                else:
                    head_string += each + ","
            s_nubmer = ", ".join(["%s" for i in range(len(empdata.columns))])
            sql = "INSERT INTO {} ({}) VALUES ({})".format(table_name, head_string, s_nubmer)
            for i,row in empdata.iterrows():
                print(sql, tuple(row))
                cursor.execute(sql, tuple(row))