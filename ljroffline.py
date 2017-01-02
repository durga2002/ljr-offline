import os
import datetime
import urllib.request
import urllib.error
from html.parser import HTMLParser
import re
import sys
import calendar

# global definitions

blogUrl = 'http://lj.rossia.org'
saveDir = 'c:/tmp'
imageDir = saveDir + '/images'
badImportTitle = 'Imported event&nbsp;Original'
firstYear = 2006
lastYear = 2007




# errors, warnings
def report(s):
    print('>>> ' + s)
    
# progress    
def log(msg):
    print(msg)    


### index page ###########
class indexPage:
    def __init__(self, indexName=''):
        if indexName:
            try:
                self.indexFile = open(file=indexName, mode='w', encoding = 'utf-8', buffering=1)
            except OSError:
                report('Cannot create index file')
                sys.exit(-1)
        else:
            log('no target index name is spcified, using stdout')
            self.indexFile = sys.stdout
        print('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"> <html lang="en"> <head> <meta http-equiv="content-type" content="text/html; charset=utf-8"> <title>Index</title> </head> <body>', file = self.indexFile)
    
    def __del__(self):
        print('<p></body> </html>', file = self.indexFile)
        self.indexFile.close()
        
    def addYear(self, year):
        print('<p>year:', year, file = self.indexFile)
        
    def addMonth(self, month):
        print('<p>&nbsp;&nbsp;month:', calendar.month_name[month], file = self.indexFile)

    def addPost(self, title, link):
        print('<p>&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"' + link + '\">' + title + '</a>', file = self.indexFile)
      

#########################
       
def title(text, url):
    found = re.search(r'<title>'+user+r': (.*)</title>', text, flags=re.IGNORECASE)
    if found:
        title = found.group(1).strip()
        if title == '' or title == badImportTitle:
            title = '[image/video]'
    else:
        report(url + ': no TITLE tag')
        title = '???'
    return title

class MonthPageParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.status = ''
        self.link = ''
        self.postList = []
            
    def handle_starttag(self, tag, attrs):
        if tag == 'a' and attrs[0][0] == 'href':
            self.link = attrs[0][1]
            if re.match(rootUrl + r'/\d*.html', self.link):
                self.status = 'ready_for_header'
            
    def handle_data(self, data):
        if self.status == 'ready_for_header':
            self.postList.append((data, self.link))
            self.status = ''
            self.link = ''
    
    def posts(self):
        return self.postList
         
class ImageSaver(HTMLParser):

    def __init__(self, targetDir):
        HTMLParser.__init__(self)
        self.targetDir = targetDir
          
    def handle_starttag(self, tag, attrs):
        if tag == 'img' and attrs[0][0] == 'src':
            imageUrl = attrs[0][1]
            imageName = imageUrl.split('/')[-1]
            if imageUrl.startswith('/'):
                imageUrl = blogUrl + imageUrl
            targetImageName = self.targetDir + '/' + imageName
            if not os.path.exists(targetImageName):
                try:
                    urllib.request.urlretrieve(imageUrl,  targetImageName)
                except Exception:
                    report('cannot download image ' + imageUrl)
            elif not imageUrl.startswith(('/', blogUrl, 'http://stat.livejournal.com/img/talk/')): 
                report('two images with the same name ' + imageUrl)

def processYear(year):
    index.addYear(year)
    for month in reversed(range(12)):
        processMonth(year, month+1)

def processPost(text):
    imageSaver.feed(text)
    text.replace(rootUrl, '.')
    text = re.sub(r'=\s*\".*/([^/]+gif|jpeg|jpg|png|bmp|svg)\s*\"', r'="images/\1"', text, flags=re.IGNORECASE)
    return text
    
def processMonth(year, month):
    index.addMonth(month)
    
    try:
        monthPage = urllib.request.urlopen(rootUrl + '/' + year + '/%.2d' % month)
    except urllib.error.URLError as e:
        report('URLError on ' + monthPage)
      
    monthHtml = monthPage.read().decode('utf-8')
    posts = re.findall(rootUrl + r'/\d*.html', monthHtml)
    
    for postUrl in posts:
        text = urllib.request.urlopen(postUrl).read().decode('utf-8', 'ignore')
        text = processPost(text)
        postFileName = postUrl.split('/')[-1]
        localFileName = saveDir + '/' + postFileName
        with open(localFileName, mode='w', encoding='utf_8') as file:
            file.write(text)    
        subject = title(text, postUrl)
        log(subject)
        
        #if post[0] == '(no subject)':
            ##postParser.feed(text)
            ##title = postParser.header()
        #else:
            #title = post[0]

        # update index
        index.addPost(subject, localFileName)
      
if len(sys.argv) < 2:
    print('user name is not specified')
    log('ERROR: user name is not specified')    
    sys.exit(-1)
user = sys.argv[1]
rootUrl = blogUrl + '/users/' + user

index = indexPage(saveDir + '/index.html')   
imageSaver = ImageSaver(imageDir)
     
os.makedirs(saveDir, exist_ok = True)
os.makedirs(imageDir, exist_ok = True)

for year in reversed(range(firstYear, lastYear + 1)):
    yearUrl = rootUrl + '/' + str(year)
    try:
        yearPage = urllib.request.urlopen(yearUrl)
    except urllib.error.URLError as e:
        report('URLError on ' + yearUrl)
        continue
    processYear(str(year))    

