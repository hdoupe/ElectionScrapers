from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
from sqlite_helper import Sqlite_Helper
import time,re,sched,datetime,argparse
br = webdriver.PhantomJS(service_log_path="/Users/HANK/Documents/election/election_data/ghostdriver.log")

pathToTable = "/Users/HANK/Documents/election/election_data/2016_election/prediction_markets.sqlite"

earlyStates = ["https://www.predictit.org/Market/1675/Who-will-win-the-2016-Nevada-Republican-caucuses","https://www.predictit.org/Market/1882/Who-will-place-2nd-in-the-2016-Nevada-Republican-caucuses","https://www.predictit.org/Market/1674/Who-will-win-the-2016-South-Carolina-Democratic-primary"]

superTuesday = ["https://www.predictit.org/Market/1716/Who-will-win-the-2016-Massachusetts-Republican-primary","https://www.predictit.org/Market/1715/Who-will-win-the-2016-Georgia-Republican-primary","https://www.predictit.org/Market/1721/Who-will-win-the-2016-Virginia-Republican-primary","https://www.predictit.org/Market/1717/Who-will-win-the-2016-Oklahoma-Republican-primary","https://www.predictit.org/Market/1709/Who-will-win-the-2016-Minnesota-Republican-caucuses","https://www.predictit.org/Market/1713/Who-will-win-the-2016-Alabama-Republican-primary","https://www.predictit.org/Market/1719/Who-will-win-the-2016-Texas-Republican-primary","https://www.predictit.org/Market/1718/Who-will-win-the-2016-Tennessee-Republican-primary","https://www.predictit.org/Market/1714/Who-will-win-the-2016-Arkansas-Republican-primary","https://www.predictit.org/Market/1712/Who-will-win-the-2016-Alaska-Republican-caucuses","https://www.predictit.org/Market/1720/Who-will-win-the-2016-Vermont-Republican-primary","https://www.predictit.org/Market/1710/Who-will-win-the-2016-Minnesota-Democratic-caucuses","https://www.predictit.org/Market/1723/Who-will-win-the-2016-Arkansas-Democratic-primary","https://www.predictit.org/Market/1725/Who-will-win-the-2016-Massachusetts-Democratic-primary","https://www.predictit.org/Market/1726/Who-will-win-the-2016-Oklahoma-Democratic-primary","https://www.predictit.org/Market/1728/Who-will-win-the-2016-Texas-Democratic-primary","https://www.predictit.org/Market/1730/Who-will-win-the-2016-Virginia-Democratic-primary","https://www.predictit.org/Market/1722/Who-will-win-the-2016-Alabama-Democratic-primary","https://www.predictit.org/Market/1711/Who-will-win-the-2016-Colorado-Democratic-caucuses","https://www.predictit.org/Market/1727/Who-will-win-the-2016-Tennessee-Democratic-primary","https://www.predictit.org/Market/1724/Who-will-win-the-2016-Georgia-Democratic-primary","https://www.predictit.org/Market/1729/Who-will-win-the-2016-Vermont-Democratic-primary"]

national = ["https://www.predictit.org/Market/1233/Who-will-win-the-2016-Republican-presidential-nomination","https://www.predictit.org/Market/1234/Who-will-win-the-2016-US-presidential-election","https://www.predictit.org/Market/1232/Who-will-win-the-2016-Democratic-presidential-nomination","https://www.predictit.org/Market/1296/Which-party-will-win-the-2016-US-Presidential-election","https://www.predictit.org/Market/1529/Who-will-win-the-2016-Republican-vice-presidential-nomination","https://www.predictit.org/Market/1530/Who-will-win-the-2016-Democratic-vice-presidential-nomination"]

def cleanUp(junk):
    if not junk:
        return None
    x = str(junk).encode('ascii','ignore')
    return re.sub('\n|\t/|\r',' ',x).strip()

def getSource(url,br, sleep = 2):
    br.get(url)
    time.sleep(sleep)
    src = br.page_source.encode('ascii','ignore')
    return src
SCURL = "https://www.predictit.org/Market/1673/Who-will-win-the-2016-South-Carolina-Republican-primary"

"""
	Gets the categories for the Political side of the betting market
"""
def getCategories():
	url = "https://www.predictit.org/Home/browseonlycategories?categoryid=6"
	br = webdriver.PhantomJS(service_log_path="/Users/HANK/Documents/election/election_data/ghostdriver.log")
	soup = BeautifulSoup(getSource(url,br), "html.parser")
	div = soup.find('div', {'class':'overflow'})
	base = "https://www.predictit.org/"
	categories = []
	for a in div.find_all('a'):
		categories.append(base + str(a.get('href').encode('ascii','ignore')))
	
	return categories


""" 
	Having trouble finding the contract list for this category. It should in either 
	'id':marketList or 'class':row but it's not showing up
"""
def getContests(category = "https://www.predictit.org/Browse/Group/54"):
	br = webdriver.PhantomJS(service_log_path="/Users/HANK/Documents/election/election_data/ghostdriver.log")
	soup = BeautifulSoup(getSource(category,br),"html.parser")
	marketList = soup.find('div',{'id','marketList'})
	print marketList
	marketList = soup.find('div', {'class','row'})
	print '2',marketList
	for div in marketList.find_all('div'):
		print div

"""
	Supposed 
"""
# def run():
# 	categories = getCategories()
# 	
# 	for category in categories:
# 		contests = getContests(category)
# 		for contest in contests:
#			scrapeContest(contest)
# 
# 	return someData


"""
	Returns dictionary with keys: contest, question, buy, sell (buy and sell are dicts
	with keys yes no
"""
def scrapeContest(url = SCURL):
	soup = BeautifulSoup(getSource(url,br), "html.parser")
	td = soup.find('td',{'class':'sMarket'})
	results = []
	contest = soup.find('h3',{'style':'margin-top: 1px;'})
	contest = contest.get_text()
	for table in td.find_all('table',{'class':'sharesMarket'}):
		if table:
			trs = table.find_all('tr')
			tr = trs[1]
			
			data = {'CONTEST':contest}		
			
			div = table.find('div',{'class':'outcome'})
			a = div.find('a')
			question = a.get('title')
			data['QUESTION'] = question
			
			sharesUps = tr.find_all('span',{'class':'sharesUp'})
			sharesDowns = tr.find_all('span',{'class':'sharesDown'})
			data['BUY_YES'],data['BUY_NO'] = sharesUps[0].get_text(),sharesDowns[0].get_text()
			data['SELL_YES'],data['SELL_NO'] = sharesUps[1].get_text(),sharesUps[1].get_text()
			
			for key in ['BUY_YES','BUY_NO','SELL_YES','SELL_NO']:
				if data[key] == 'None':
					data[key] = u'0'
			
			results.append(data)
# 	try:
# 		br.service.process.send_signal(signal.SIGTERM)
# 		br.quit()
# 	except:
# 		pass
	del soup,td

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
	for link in earlyStates+national+superTuesday:
		try:
			results = scrapeContest(link)
			rows = []
			for result in results:
				row = []
				for key in keys:
					row.append(cleanUp(result[key]))
				row.append(DATE)
				rows.append(row)
				print row
				del row
			del results
			SH.insert_rows(len(rows[0]),rows)
		except Exception as e:
			import traceback
			print 'exception',link,e,traceback.print_exc()
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
