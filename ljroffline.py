import os
import datetime
import urllib.request
import urllib.error
import re
import sys
import calendar
import itertools
from html.parser import HTMLParser
import requests

# TODO
# Two images with the same name http://i43.tinypic.com/242wm1i.jpg
# Can not download image: http://i43.tinypic.com/242wm1i.jpg -- wrong message
#
# why cannot download from wikipedia? http://upload.wikimedia.org/wikipedia/commons/e/e4/Cathars_expelled.JPG http://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Fryne_przed_areopagiem.jpg/800px-Fryne_przed_areopagiem.jpg
# http://lj.rossia.org/users/ogles/77735.html
#
# http://lj.rossia.org/users/ogles/25878.html -- stupid exception on fetching image. Add exception handling.
############# CLASSES ####################
class g: #globals
    user = ''    
    blogUrl = 'http://lj.rossia.org'
    rootUrl = ''
    saveDir = ''
    imageDir = ''
    badImportTitle = 'Imported event&nbsp;Original'
    
class ProgressSpinner:
    def __init__(self):
        self.spin = itertools.cycle('-\\|/-\\|/')
    def showProgress(self):
        sys.stdout.write('\b%s' % next(self.spin))
        sys.stdout.flush()            
        
class Index:
    def __init__(self):
        indexFileName = g.saveDir + '/index.html'
        try:
            self.indexFile = open(file=indexFileName, mode='w', encoding = 'utf-8')
        except OSError:
            report('Cannot create index file ' + indexFileName)
            sys.exit(-1)
        print('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"> <html lang="en"> <head> <meta http-equiv="content-type" content="text/html; charset=utf-8"> <title>Index</title> </head> <body style="background-color:cornsilk;">', file = self.indexFile)
            
    def __del__(self):
        print('<p></body> </html>', file = self.indexFile)
        self.indexFile.close()
        
    def addYear(self, year):
        print('<h1 style="font-family:verdana;">' + year + '</h1>', file = self.indexFile)
        
    def addMonth(self, month):
        self.indexFile.flush()
        print('<h3 style="font-family:verdana;">' + calendar.month_name[month] + '</h3>', file = self.indexFile)

    def addPost(self, title, link):
        print('<p style="font-family:verdana;">&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"' + link + '\">' + title + '</a>', file = self.indexFile)
         
                
################# FUNCTIONS #####################
                
def report(s):
    print('\b' + s)

def title(text, url):
    found = re.search(r'<title>'+g.user+r': (.*)</title>', text, flags=re.IGNORECASE)
    if found:
        title = found.group(1).strip()
        if title == '' or title == g.badImportTitle:
            title = '[image/video]'
    else:
        report('WARNING: no TITLE tag in ' + url)
        title = '???'
    return title


def processYear(year):
    index.addYear(year)
    for month in reversed(range(12)):
        processMonth(year, month+1)

def downloadImage(imageUrl, imageFileName):
    if imageUrl.startswith('/'):
        imageUrl = g.blogUrl + imageUrl
    targetImageName = g.imageDir + '/' + imageFileName
    
    if not os.path.exists(targetImageName):
        try:
            req = requests.get(imageUrl, headers={'User-agent': 'Mozilla/5.0'})
        except e:
            return ''                    
        
        if not req.ok:
            return ''
        
        with open(targetImageName, 'wb') as imgFile:
            imgFile.write(req.content)
            imgFile.close()

    elif not imageUrl.startswith(('/', g.blogUrl, 'http://stat.livejournal.com/img/talk/')): 
        report('Two images with the same name ' + imageUrl)  
        return ''
    
    return targetImageName
    
        
def processImage(matchObj):
    imageUrl =  matchObj.group(2)
    imageFileName = re.search(r'.*/([^/]*[jpeg|jpg|png|gif|bmp])\W*.*', imageUrl).group(1)
    if not imageFileName:
        report('Can not understand image URL: '+ imageUrl)
        return matchObj.group(0)
    localImagePath = downloadImage(imageUrl, imageFileName)
    if localImagePath == '':
        report('Can not download image: '+ imageUrl)
        return matchObj.group(0)         
    else:
        return '<img %s src="%s"%s>' % (matchObj.group(1), localImagePath, matchObj.group(3))

    
def processPost(text):
    
    # save images
    text = re.sub(r'<img\s*(.*?)\s*src\s*=\s*\"([^\"]*)\"([^>]*)>', processImage, text, flags=re.IGNORECASE)
    
    # make links local
    text = re.sub(r'('+g.rootUrl+')', '.', text)    
    
    return text

def processMonth(year, month):
    index.addMonth(month)
    
    try:
        monthPage = urllib.request.urlopen(g.rootUrl + '/' + year + '/%.2d' % month)
    except urllib.error.URLError as e:
        report('URLError on ' + monthPage)
        return
      
    monthHtml = monthPage.read().decode('utf-8')
    posts = re.findall(g.rootUrl + r'/\d*.html', monthHtml)
    
    for postUrl in posts:
        try:
            text = urllib.request.urlopen(postUrl).read().decode('utf-8', 'ignore')
        except urllib.error.URLError as e:
            report('URLError on ' + postUrl)
            index.addPost('BAD POST: ' + postUrl, '')
            continue
        text = processPost(text)
        postFileName = postUrl.split('/')[-1]
        localFileName = g.saveDir + '/' + postFileName
        with open(localFileName, mode='w', encoding='utf_8') as file:
            file.write(text)  
            file.close()
        subject = title(text, postUrl)
        
        spinner.showProgress()        

        index.addPost(subject, localFileName)


####################### CODE ####################
        
if len(sys.argv) != 5:
    report('Usage: ' + sys.argv[0] + ' <ljr-user> <from-year> <to-year> <save-dir>')
    sys.exit(-1)
    
g.user = sys.argv[1]
firstYear = int(sys.argv[2])
lastYear = int(sys.argv[3])

g.saveDir = sys.argv[4]
os.makedirs(g.saveDir, exist_ok = True)

g.imageDir = g.saveDir + '/images'
os.makedirs(g.imageDir, exist_ok = True)

g.rootUrl = g.blogUrl + '/users/' + g.user

index = Index()   

spinner = ProgressSpinner()

for year in reversed(range(firstYear, lastYear + 1)):
    yearUrl = g.rootUrl + '/' + str(year)
    try:
        yearPage = urllib.request.urlopen(yearUrl)
    except urllib.error.URLError as e:
        report('URLError on ' + yearUrl)
        continue
    processYear(str(year))
    
report("\bDone.")