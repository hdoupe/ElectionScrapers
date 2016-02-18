from selenium import webdriver
from bs4 import BeautifulSoup
import time

def getSource(url,br, sleep = 5):
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
	br = webdriver.PhantomJS()
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
	br = webdriver.PhantomJS()
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
	br = webdriver.PhantomJS()
	soup = BeautifulSoup(getSource(url,br), "html.parser")
	td = soup.find('td',{'class':'sMarket'})
	results = []
	contest = soup.find('h3',{'style':'margin-top: 1px;'})
	contest = contest.get_text()
	for table in td.find_all('table',{'class':'sharesMarket'}):
		if table:
			trs = table.find_all('tr')
			tr = trs[1]
			
			data = {'contest':contest}		
			
			div = table.find('div',{'class':'outcome'})
			a = div.find('a')
			question = a.get('title')
			data['question'] = question
			
			sharesUps = tr.find_all('span',{'class':'sharesUp'})
			sharesDowns = tr.find_all('span',{'class':'sharesDown'})
			
			buy = {'yes':sharesUps[0].get_text(),'no':sharesDowns[0].get_text()}
			sell = {'yes':sharesUps[1].get_text(),'no':sharesUps[1].get_text()}
			for d in (buy,sell):
				for key in d:
					if d[key] == 'None':
						d[key] = u'0'
				
			data['buy'] = buy
			data['sell'] = sell
			
			results.append(data)

	return results

if __name__ == '__main__':
	results = scrapeContest()
	for result in results:
		print result	