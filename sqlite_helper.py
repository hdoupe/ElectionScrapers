import sqlite3 as sdb
import re


class Sqlite_Helper(object):
	def __init__(self, sqlite_path, table_name):
		self.sqlite_path = sqlite_path
		self.table_name = table_name
	
	def create(self,header):
		self.connection = sdb.connect(self.sqlite_path)
		self.cursor = connection.cursor()
		
		cursor.execute("CREATE TABLE {tn} ({hd})".\
			format(tn = self.table_name,hd = header))
		
		connection.commit()

	def insert_rows(self,length,rows):

		holders = ','.join(['?']*length)
		
		sql = "INSERT OR REPLACE INTO " + self.table_name + " VALUES (" + holders + ")" 
		
		for row in rows:
				
			row_len = len(row)
			if row_len == 1:
				break
			
			self.cursor.execute(sql,row)
		
		self.connection.commit()
	
	def set_db(self):
		self.connection = sdb.connect(self.sqlite_path)
		self.connection.row_factory = sdb.Row
		self.cursor = self.connection.cursor()
		return self.connection,self.cursor
	
	def all_variables(self):
		self.cursor.execute("PRAGMA table_info({tn})".format(tn = self.table_name))
		vars = [dscr[1] for dscr in self.cursor.fetchall()]

		return vars

class Recursive_Cursor(Sqlite_Helper):
	def __init__(self,db,table_name):
		super(Recursive_Cursor,self).__init__(db,table_name)
		
		self.conn, self.cursor = Sqlite_Helper.set_db(self)
	
	def get_data(self,sql):
		self.cursor.execute(sql)
		results = [float(result[0]) for result in self.cursor.fetchall()]
		
		return results
	
	def close_db(self):
		self.conn.close()
