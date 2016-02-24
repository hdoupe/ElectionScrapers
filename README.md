realclearpolitics.py scrapes polling data from their formatted tables.

predictit.py scrapes data from predictit.org and formats it into a sqlite table.  The default setting is to run once an hour, but this can be changed using the flag --interval or -i followed by the desired waiting time in seconds.

Depends on BeautifulSoup, Selenium, PhantomJS, and sqlite_helper.py

First, set the path to your sqlite file in predictit.py.  Then, the first time predictit.py is run use the command: 

python predictit.py --createTable

or 

python predictit.py --createTable --interval numberofseconds

Afterwards, just use one of the following commands 

python predictit.py --interval numberofseconds 

or just 

python predictit.py

