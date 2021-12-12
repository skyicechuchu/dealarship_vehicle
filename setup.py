from src import create_table_data, config



config_file = config.Config.dbinfo().copy()
file_info = config.Config.fileinfo()
db = create_table_data.InitDB(config_file)
db.check_drop_database_if_exists()
db.create_table_with_sql(schema=file_info['schema'])
db.insert_raw_data(raw_data_dir=file_info['raw_data_dir'])
db.db_connect.commit()
db.db_connect.close()