
### Step 1
* Go here: http://www.ema.europa.eu/ema/index.jsp?curl=pages/medicines/landing/epar_search.jsp&mid=WC0b01ac058001d124
* Click "View all"
* Click "Download results to spreadsheet"

or use this:
`curl 'http://www.ema.europa.eu/ema/downloadDataServlet?category=true&type=epar' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Accept-Language: en-US,en;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' -H 'Referer: http://www.ema.europa.eu/ema/index.jsp?curl=pages%2Fmedicines%2Flanding%2Fepar_search.jsp&mid=WC0b01ac058001d124&searchTab=&alreadyLoaded=true&isNewQuery=true&status=Authorised&status=Withdrawn&status=Suspended&status=Refused&startLetter=View+all&keyword=Enter+keywords&searchType=name&taxonomyPath=&treeNumber=&searchGenericType=generics' -H 'Cookie: JSESSIONID=qGE_QiQnqFDqu2KIglMB1OmyXnyGtqjh5tAG1j3pdS-MISw8Zuyy!-1720614694' -H 'Connection: keep-alive' --compressed`

### Step 2
* Run parse.py

### Step 3
* Run process_indications.py