import json,requests
from datetime import datetime
from sqlite_helper import Sqlite_Helper
import time,re,sched,datetime,argparse,json,requests
from selenium import webdriver
from bs4 import BeautifulSoup
br = webdriver.PhantomJS()

pathToTable = "prediction_markets.sqlite"

superTuesday = ['TXPRMRY16.GOP',' VAPRMRY16.GOP', 'GAPRMRY16.GOP', 'MAPRMRY16.GOP', 
	'OKPRMRY16.GOP', 'MNCAUCUS16.GOP', 'ALPRMRY16.GOP', 'TNPRMRY16.GOP','ARPRMRY16.GOP',
	'MAPRMRY16.DEM','AKCAUCUS16.GOP', 'OKPRMRY16.DEM','VTPRMRY16.GOP', 'MNCAUCUS16.DEM', 
	'TXPRMRY16.DEM','COCAUCUS16.DEM', 'ARPRMRY16.DEM',  'VAPRMRY16.DEM', 'GAPRMRY16.DEM',
	'ALPRMRY16.DEM', 'TNPRMRY16.DEM','VTPRMRY16.DEM']

national = ['RNOM16','USPREZ16', 'USPREZ16','PREZPRTY16', 'RVP16', 'DVP16',
	'CARSON.DROPOUT.022916', 'WOMAN.USPREZ16','KASICH.DROPOUT.022916','BLOOMBERG.RUN.MAR',
	'370.REPPREZ16','TRUMP.INDY.2016','GOPBROKERED.2016','370.DEMPREZ16','ROMNEY.RUN.2016',
	'CARSON.INDY.2016']


def cleanUp(junk):
    if not junk:
        return None
    x = str(junk).encode('ascii','ignore')
    return re.sub('\n|\t/|\r',' ',x).strip()


def getContracts(tickersymbol):
	url = "https://www.predictit.org/api/marketdata/ticker/{ts}".format(ts = tickersymbol)
	response = requests.get(url)
	contracts = response.json()
	
	if contracts == None:
		print "NONE",tickersymbol
		return None
	
	contest = contracts['Name'].encode('ascii')
	
	results = []
	
	for contract in contracts['Contracts']:
		data = {}
		data['CONTEST'] = contest
		data['QUESTION'] = contract['LongName'].encode('ascii')
		data['BUY_YES'] = str(int((contract['BestBuyYesCost'] if contract['BestBuyYesCost'] else 0) * 100))
		data['BUY_NO'] = str(int((contract['BestBuyNoCost']  if contract['BestBuyNoCost'] else 0)* 100))
		data['SELL_YES'] = str(int((contract['BestSellYesCost']  if contract['BestSellYesCost'] else 0)*100))
		data['SELL_NO'] = str(int((contract['BestSellNoCost'] if contract['BestSellNoCost'] else 0)*100))
		
		results.append(data)
	del contracts
	return results


def createSqliteTable():
	HEADER = "CONTEST TEXT,QUESTION TEXT,BUY_YES INTEGER,BUY_NO INTEGER,SELL_YES INTEGER, SELL_NO INTEGER,DATE TEXT"
	SH = Sqlite_Helper(pathToTable,'predictit')
	SH.create(HEADER)


def go():
	SH = Sqlite_Helper(pathToTable,'predictit')
	SH.set_db()
	SH.cursor.execute("SELECT datetime('now','localtime')")
	DATE = SH.cursor.fetchall()[0][0]
	print DATE
	keys = ['CONTEST','QUESTION','BUY_YES', 'BUY_NO', 'SELL_YES','SELL_NO']
	for tickersymbol in national + superTuesday + ['SCPRMRY16.DEM']:
		try:
			results = getContracts(tickersymbol)
			rows = []
			for result in results:
				row = []
				for key in keys:
					row.append(cleanUp(result[key]))
				row.append(DATE)
				rows.append(row)
				print row
				del row
			if rows:
				SH.insert_rows(len(rows[0]),rows)
			del results,rows
		except Exception as e:
			import traceback
			print 'exception',tickersymbol,e,traceback.print_exc()
			continue
	SH.connection.close()

s = sched.scheduler(time.time, time.sleep)

def simpleSchedule(interval):
	go()
	s.enter(interval,1,simpleSchedule,(interval,))

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--createTable","-c",dest = "createTable",action = "store_true")
	parser.add_argument("--interval","-i",dest = "interval",default = 3600)
	args = parser.parse_args()
	if args.createTable:
		createSqliteTable()
	s.enter(0,1,simpleSchedule,(int(args.interval),))
	s.run()
