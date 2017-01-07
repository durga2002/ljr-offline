import os
import datetime
import urllib.request
import urllib.error
import re
import sys
import calendar
import itertools
from html.parser import HTMLParser

# TO DO
# don't compile regexes
# extend image file name pattern (tom_of_finland_15.jpg?w=640)
#check why http://i.piccy.info/i9/ecfd943a1e2639cfecae2c217f9e8087/1478666204/7773/1087829/14786577994840s_240.jpg is reported as can't download and why its link is left not localized.
2016
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
        print('<h3 style="font-family:verdana;">' + calendar.month_name[month] + '</h3>', file = self.indexFile)

    def addPost(self, title, link):
        print('<p style="font-family:verdana;">&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"' + link + '\">' + title + '</a>', file = self.indexFile)
         
class ImageSaver(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and attrs[0][0] == 'src':
            imageUrl = attrs[0][1]
            imageName = imageUrl.split('/')[-1]
            if imageUrl.startswith('/'):
                imageUrl = g.blogUrl + imageUrl
            targetImageName = g.imageDir + '/' + imageName
            if not os.path.exists(targetImageName):
                try:
                    urllib.request.urlretrieve(imageUrl,  targetImageName)
                except Exception:
                    report('cannot download image ' + imageUrl)
            elif not imageUrl.startswith(('/', g.blogUrl, 'http://stat.livejournal.com/img/talk/')): 
                report('two images with the same name ' + imageUrl)
                
                
################# FUNCTIONS #####################
                
def report(s):
    print('\b' + s)



def title(text, url):
    found = searchTitleRegex.search(text)
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

def processPost(text):
    imageSaver.feed(text)
    text.replace(g.rootUrl, '.')
    text = replaceImageLinkRegex.sub(r'="images/\1"', text)
    return text

def processMonth(year, month):
    index.addMonth(month)
    
    try:
        monthPage = urllib.request.urlopen(g.rootUrl + '/' + year + '/%.2d' % month)
    except urllib.error.URLError as e:
        report('URLError on ' + monthPage)
      
    monthHtml = monthPage.read().decode('utf-8')
    posts = findPostsLinksRegex.findall(monthHtml)
    
    for postUrl in posts:
        text = urllib.request.urlopen(postUrl).read().decode('utf-8', 'ignore')
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

imageSaver = ImageSaver()
spinner = ProgressSpinner()
searchTitleRegex = re.compile(r'<title>'+g.user+r': (.*)</title>', flags=re.IGNORECASE)
replaceImageLinkRegex = re.compile(r'=\s*\".*/([^/]+gif|jpeg|jpg|png|bmp|svg)\s*\"', flags=re.IGNORECASE)
findPostsLinksRegex = re.compile(g.rootUrl + r'/\d*.html')

for year in reversed(range(firstYear, lastYear + 1)):
    yearUrl = g.rootUrl + '/' + str(year)
    try:
        yearPage = urllib.request.urlopen(yearUrl)
    except urllib.error.URLError as e:
        report('URLError on ' + yearUrl)
        continue
    processYear(str(year))
    
    report("\bDone.")