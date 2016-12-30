import os
import datetime
import urllib.request
import urllib.error
from html.parser import HTMLParser
import re
import sys

user = 'user'
rootUrl = 'http://lj.rossia.org/users/'+user
saveDir = 'c:/tmp'
imageDir = saveDir + '/images'
badImportTitle = 'Imported event&nbsp;Original'
firstYear = 2006
lastYear = 2007

def report(s):
    print('>>> LOG: ' + s)


### index page ###########
class indexPage:
    def updateYear(self, year):
        print('INXED: year ' + year)
        
    def updateMonth(self, month):
        print('INXED:     month ' + month)

#########################
        
class PostHeaderParserBad(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.status = ''
        self.postHeader = ''
        self.headerFound = False
    
    def handle_endtag(self, tag):
        if not self.headerFound and tag == 'center' and self.status == '':
            print('end, ready_for_header')
            self.status = 'ready_for_header'
            
    def handle_data(self, data):
        if not self.headerFound and self.status == 'ready_for_header':
            self.postHeader = data
            self.status == ''
            self.headerFound = True

    def header(self):
        if self.headerFound:
            return self.postHeader[:100]
        else:
            return ''
    
def title(text, url):
    found = re.search(r'<title>'+user+r': (.*)</title>', text, flags=re.IGNORECASE)
    if found:
        title = found.group(1)
        if title == '' or title == badImportTitle:
            title = '<image/video>'        
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
            if re.match(r'http://lj.rossia.org/users/'+user+r'/\d*.html', self.link):
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
                imageUrl = 'http://lj.rossia.org' + imageUrl
            targetImageName = self.targetDir + '/' + imageName
            if not os.path.exists(targetImageName):
                try:
                    urllib.request.urlretrieve(imageUrl,  targetImageName)
                except Exception:
                    report('cannot download image ' + imageUrl)
            elif not (imageUrl.startswith('/') or imageUrl.startswith('http://lj.rossia.org')): 
                report('two images with the same name ' + imageUrl)

index = indexPage()   
#postParser = PostHeaderParser()    
#monthParser = MonthPageParser()
imageSaver = ImageSaver(imageDir)

def main():
    
    os.makedirs(saveDir, exist_ok = True)
    os.makedirs(imageDir, exist_ok = True)
    
    for year in reversed(range(firstYear, lastYear + 1)):
        yearUrl = rootUrl + '/' + str(year)
        try:
            yearPage = urllib.request.urlopen(yearUrl)
        except urllib.error.URLError as e:
            log('URLError on ' + yearUrl)
            continue
        processYear(str(year))

def log(msg):
    print('Log:' + msg)

def processYear(year):
    index.updateYear(year)
    for month in reversed(range(12)):
        processMonth(year, str(month+1))

def processPost(text):
    imageSaver.feed(text)
    text.replace(rootUrl, '.')
    text = re.sub(r'=\s*\".*/([^/]+gif|jpeg|jpg|png|bmp|svg)\s*\"', r'="images/\1"', text, flags=re.IGNORECASE)
    return text
    
def processMonth(year, month):
    index.updateMonth(month)
    #print(rootUrl + '/' + year + '/' + month)
    
    try:
        monthPage = urllib.request.urlopen(rootUrl + '/' + year + '/' + month)
    except urllib.error.URLError as e:
        log('URLError on ' + monthPage)
      
    monthHtml = monthPage.read().decode('utf-8')
    

    #monthParser.feed(monthHtml)
    #posts = monthParser.posts()
    
    posts = re.findall(r'http://lj.rossia.org/users/'+user+r'/\d*.html', monthHtml)
    
    for postUrl in posts:
        text = urllib.request.urlopen(postUrl).read().decode('utf-8', 'ignore')
        
        text = processPost(text)
        
        postFileName = postUrl.split('/')[-1]
        with open(saveDir + '/' + postFileName, mode='w', encoding='utf_8') as file:
            file.write(text)    
        subject = title(text, postUrl)
        print(subject)
        #if post[0] == '(no subject)':
            ##postParser.feed(text)
            ##title = postParser.header()
        #else:
            #title = post[0]

        # update index
    
    

if __name__ == "__main__":
    main()        


# !!! good index and logging

# format month
# do not truncate words in titles
# cannot fetch url or image
# posts with no text (image/link/youtube)
# progress indicator