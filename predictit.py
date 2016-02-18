from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
from sqlite_helper import Sqlite_Helper
import time,re,sched,datetime

earlyStates = ["https://www.predictit.org/Market/1673/Who-will-win-the-2016-South-Carolina-Republican-primary","https://www.predictit.org/Market/1880/Who-will-place-2nd-in-the-2016-South-Carolina-Republican-primary","https://www.predictit.org/Market/1675/Who-will-win-the-2016-Nevada-Republican-caucuses","https://www.predictit.org/Market/1674/Who-will-win-the-2016-South-Carolina-Democratic-primary","https://www.predictit.org/Market/1881/Who-will-place-3rd-in-the-2016-South-Carolina-Republican-primary","https://www.predictit.org/Market/1676/Who-will-win-the-2016-Nevada-Democratic-caucuses"]

national = ["https://www.predictit.org/Market/1233/Who-will-win-the-2016-Republican-presidential-nomination","https://www.predictit.org/Market/1234/Who-will-win-the-2016-US-presidential-election","https://www.predictit.org/Market/1232/Who-will-win-the-2016-Democratic-presidential-nomination","https://www.predictit.org/Market/1296/Which-party-will-win-the-2016-US-Presidential-election"]

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
	br = webdriver.PhantomJS(service_log_path="/Users/HANK/Documents/data_processing/election/election_data/ghostdriver.log")
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
	br = webdriver.PhantomJS(service_log_path="/Users/HANK/Documents/data_processing/election/election_data/ghostdriver.log")
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
	br = webdriver.PhantomJS(service_log_path="/Users/HANK/Documents/data_processing/election/election_data/ghostdriver.log")
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

	return results

" create sqlite table "
def create_sqlite_table(path):
	HEADER = "CONTEST TEXT,QUESTION TEXT,BUY_YES INTEGER,BUY_NO INTEGER,SELL_YES INTEGER, SELL_NO INTEGER,DATE TEXT"
	SH = Sqlite_Helper(path,'predictit')
	SH.create(HEADER)


def go():
	path = "path to your sqlite table/prediction_markets.sqlite"
	SH = Sqlite_Helper(path,'predictit')
	SH.set_db()
	SH.cursor.execute("SELECT datetime('now','localtime')")
	DATE = SH.cursor.fetchall()[0][0]
	print DATE
	keys = ['CONTEST','QUESTION','BUY_YES', 'BUY_NO', 'SELL_YES','SELL_NO']
	for link in earlyStates+national:
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
			SH.insert_rows(len(rows[0]),rows)
		except Exception as e:
			import traceback
			print 'exception',e,traceback.print_exc()
			continue
	SH.connection.close()

" run go every half hour "
s = sched.scheduler(time.time, time.sleep)

def simpleSchedule(interval = 1800):
	go()
	s.enter(interval,1,simpleSchedule,())

if __name__ == "__main__":
	s.enter(0,1,simpleSchedule,())
	s.run()
