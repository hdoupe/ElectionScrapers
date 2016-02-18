import sqlite3 as sdb
from haversine import haversine
import re
import numpy
import scipy.stats as stats
import reverse_geocoder as rg

class Sqlite_Helper(object):
	def __init__(self, sqlite_path, table_name):
		self.sqlite_path = sqlite_path
		self.table_name = table_name
		self.percentile_dict = {}
		self.quick_percentile = {}
		self.edu_patterns = {}
	
	def create(self,header):
		connection = sdb.connect(self.sqlite_path)
		cursor = connection.cursor()
		
		cursor.execute("CREATE TABLE {tn} ({hd})".\
			format(tn = self.table_name,hd = header))
		
		connection.commit()
		connection.close()
	
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
		self.connection.create_function("REGEXP",2,self.regexp)
		self.connection.create_function("HAVERSINE",4,self.haversine)
		self.connection.create_function("PCT",2,self.pct)
		self.connection.create_function("MEAN",-1,self.mean)
		self.connection.create_function("DIVERSITY_RACE",-1,self.diversity_race)
		self.connection.create_function("DIVERSITY_AGE",-1,self.diversity_age)
		self.connection.create_function("PERCENTILE",-1,self.percentile)
		self.connection.create_function("GREATERTHANPERCENTILE",3,self.greater_than_percentile)
		self.connection.create_function("EDU",1,self.edu)
		self.connection.create_function("POLITICALBOUNDARY",3,self.political_boundary)
		self.connection.row_factory = sdb.Row
		self.cursor = self.connection.cursor()
		return self.connection,self.cursor
		
	def regexp(self,cs1,cs2):
		
		cs1 = cs1.upper().strip()
		cs2 = cs2.upper().strip()
		
		if cs1 == cs2:
			return True
		
		else:
			callsign = re.compile("[0-9A-Z]+")
			
			m1 = re.match(callsign,cs1)
			m2 = re.match(callsign,cs2)
			
			if m1 and m2:
				
				m1 = m1.group(0)
				m2 = m2.group(0)
				
				if m1 == m2:
					return True
		
		return False
	
	def mean(self,*args):
		vector = list(args)
		return numpy.average(vector)
	
	def diversity_race(self,*args):
		vector = list(args)
		for i in range(1,len(vector)):
			vector[i] = float(vector[i])
		
		Total,White,Black,AmerIndi,Asian,PI,Other,Multiple,Hispanic, NH = vector
		
		if Total > 0 and Other != Total:
			Total_minus_other = Total - Other
			White = White/Total_minus_other
			Black = Black/Total_minus_other
			AmerIndi = AmerIndi/Total_minus_other
			Asian = Asian/Total_minus_other
			PI = PI/Total_minus_other
			Multiple = Multiple/Total_minus_other
			Hispanic = Hispanic/Total
			NH = NH/Total
			Diversity = (1 - ((White**2 + Black**2 + AmerIndi**2 + Asian**2 + PI**2)*(Hispanic**2 + NH**2)))*100
		else:
			Diversity = 0.0
		return Diversity
	
	def diversity_age(self,*args):
		try:
			vector = list(args)
			for i in range(1,len(vector)):
				vector[i] = float(vector[i])
			
			Total = float(vector[0])
			if Total > 0:
				cat_1 = (numpy.sum(numpy.array(vector[1:5]))/Total)**2
				cat_2 = (numpy.sum(numpy.array(vector[5:8]))/Total)**2
				cat_3 = (numpy.sum(numpy.array(vector[8:14]))/Total)**2
				cat_4 = (numpy.sum(numpy.array(vector[14:19]))/Total)**2
				Diversity =  (1 - (cat_1 + cat_2 + cat_3 + cat_4)) * 100
			else:
				Diversity = 0.0
		
			return Diversity
		
		except Exception as e:
			print 'this',e
	
	def haversine(self,lat1,lon1,lat2,lon2):
		d = haversine((lat1,lon1),(lat2,lon2))
		return d
	
	def pct(self,N,M):
		if M == 0:
			return 0
			
		return (float(N)/float(M))*100
	
	def percentile(self,variable,N,WHERE = None):
		assert isinstance(N,int) or isinstance(N,float)
		if variable in self.percentile_dict:
			return stats.percentileofscore(self.percentile_dict[variable],N)
		else:
			RC = Recursive_Cursor(self.sqlite_path,self.table_name)
			
			if WHERE:
				sql = "SELECT {vr} FROM {tn} WHERE {W}".\
					format(vr = variable,tn = self.table_name,W = WHERE)
			else:
				sql = "SELECT {vr} FROM {tn}".format(vr = variable,tn = self.table_name)
			
			results = RC.get_data(sql)
			self.percentile_dict[variable] = results
			RC.close_db()
			return stats.percentileofscore(results,N)

# 	search for a match
	def edu(self,license):
		if not self.edu_patterns:
			self.edu_patterns = self.pattern_vector()
		license = license.split(' ')
		for word in license:
			if word[0] in self.edu_patterns:
				match = re.search(self.edu_patterns[word[0]],word.upper())
				if match:
					return 1
		return 0

# 	create dictionary of re objects, where key = first letter and value = re object
	def pattern_vector(self):
		vector = ["COLLEGE","UNIV","SCHOOL","EDUCATION"]
		d = {}
		for item in vector:
			d[item[0].upper()] = re.compile(item.upper())
		return d
		
	def greater_than_percentile(self,parameter,N,percentile):
		if parameter in self.quick_percentile:
			parameter_dictionary = self.quick_percentile[parameter]
			if percentile in parameter_dictionary:
				score_at_percentile = parameter_dictionary[percentile]
			else:
				score_at_percentile = self.get_score_at_percentile(parameter,percentile)
				parameter_dictionary[percentile] = score_at_percentile
		else:
			score_at_percentile = self.get_score_at_percentile(parameter,percentile)
			self.quick_percentile[parameter] = {percentile:score_at_percentile}
	
		if N >= percentile:
			return 1
		else:
			return 0	
	
	def get_score_at_percentile(self,parameter,percentile):
		print self.sqlite_path,self.table_name
		RC = Recursive_Cursor(self.sqlite_path,self.table_name)
		sql = "SELECT {parameter} FROM {tn}".format(parameter = parameter, tn = self.table_name)
		results = RC.get_data(sql)
		RC.close_db()
		results = [float(result) for result in results]
		results = numpy.array(results)
		Q = numpy.percentile(results,percentile)
		return Q
	
	def political_boundary(self,type,latitude,longitude):
		assert type == 'name' or type == 'admin1' or type == 'admin2' or type == 'cc'
		data = rg.search((latitude,longitude))[0]
		return data[type.encode("ASCII")]
	
	def variables(self,reach_vector = False):
		self.cursor.execute("PRAGMA table_info({tn})".format(tn = self.table_name))
		vars = [dscr[1] for dscr in self.cursor.fetchall()]
		if reach_vector:
			return vars
		else:
			lat_lon = re.compile("l[ao][tn]_[0-9]+")
			data = []
			for var in vars:
				if not re.match(lat_lon,str(var)):
					data.append(var)
		return data
	
	def get_reach_vectors(self,row):
		lats = []
		lons = []
		
		for i in range(0,360):
			lats.append(row['lat_' + str(i)])
			lons.append(row['lon_' + str(i)])
		
		return lats,lons
		
	def get_results(self):
		assert (self.search_hits != None)
		return self.search_hits
	
	def print_results(self,path_out,vars = [],delimiter = ","):
		assert (self.search_hits != None)
		
		if not vars:
			vars = self.vars
		
		out = open(path_out,'w')
		out.write(delimiter.join(vars) + '\n')
		
		for value in self.search_hits.itervalues():
			for i,datum in enumerate(value):
				if i == len(value) - 1:
					out.write(str(datum).strip() + '\n')
				else:
					out.write(str(datum).strip() + delimiter)
		
		out.close()
	
	def print_query(self,sql_str,csv):
		self.cursor.execute(sql_str)
		results = self.cursor.fetchall()
		print results
		
	
	def print_reach_coordinates(self,csv_path, sql_str = "",delimiter = ','):
		if not sql_str:
			sql_str = "SELECT * FROM {tn}".format(tn = self.table_name)
		self.cursor.execute(sql_str)
		table = self.cursor.fetchall()
		
		out = open(csv_path,'w')
		out.write("callsign" + delimiter + "latitude" + delimiter + "longitude\n")
		for row in table:
			callsign = row['callsign']
			type = str(row['type']).strip()
			
			if type == 'FM':
				lats,lons = self.get_reach_vector(row)
				
				for lat,lon in zip(lats,lons):
					out.write(callsign + delimiter + str(lat) + delimiter + str(lon) + '\n')
	
	def extract_order_by_clause(self,sql,variables):
# 			get order by values
		temp = re.split(" ORDER BY ",sql)
		ob = {}
		if len(temp) > 1:
				order_by = temp[1]
				words = order_by.split(' ')
				ob = {'order':'','variable':'','limit':''}
				for word in words:
					if re.match("ASC",word):
						ob['order'] = word
					elif re.match("DESC",word) or re.match("ASC",word):
						ob['order'] = word
					elif word in variables:
						ob['variable'] = word
					else:
						pass
				ob['limit'] = re.search("LIMIT\ [0-9]+",order_by).group(0)
		return ob
			
	
	def get_reach_vector(self,row):
		lats = []
		lons = []
		for i in range(0,360):
			lats.append(row['lat_' + str(i)])
			lons.append(row['lon_' + str(i)])
		
		return lats,lons
	
	def add_variable_to_table(self,id_variable,variable,type,function):
		
		self.cursor.execute("SELECT * FROM {tn}".format(tn = self.table_name))
		table = self.cursor.fetchall()
		
		sql_str = "ALTER TABLE {tn} ADD COLUMN '{variable}' {type}".\
			format(tn = self.table_name,variable = variable,type = type)
 		print sql_str
		
		self.cursor.execute("ALTER TABLE {tn} ADD COLUMN '{variable}' {type}".\
			format(tn = self.table_name,variable = variable,type = type))

 		self.conn.commit()
		
		for row in table:
			value = function(row,id_variable)
			id_value = row[id_variable]
			
			self.cursor.execute("UPDATE {tn} SET {variable} = '{value}' WHERE {id_variable} = '{id_value}'".\
				format(tn = self.table_name, variable = variable, value = value, id_variable = id_variable, id_value = id_value))
		
		self.conn.commit()
		self.conn.close()
	
	def demographic_variables(self,percent = False):
		p1 = re.compile("DP00[1-9]00[0-9][0-9]")
		p2 = re.compile("DP01[0|1]00[0-9][0-9]")
		re_patterns = [p1,p2]
		
		self.cursor.execute("PRAGMA table_info({tn})".format(tn = self.table_name))
		vars = [dscr[1] for dscr in self.cursor.fetchall()]
		
		variables = []
		
		for var in vars:
			for pattern in re_patterns:
				if re.search(pattern,var):
					variables.append(str(var))
					break

		if percent:
			pcts = []
			for variable in variables:
				pcts.append("PCT(" + variable + ",DP0010001)")
			return pcts
		else:
			return variables
	
	def get_average_reach(self,trans_lat,trans_lon,reach_lats,reach_lons):
		
		from haversine import haversine
		total_distance = 0.0
		vectors = 0.0

		for reach_lat,reach_lon in zip(reach_lats,reach_lons):
			total_distance += haversine((trans_lat,trans_lon),
				(float(reach_lat),float(reach_lon)))
			vectors += 1

		average_reach = total_distance/vectors
		
		return average_reach
	
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
