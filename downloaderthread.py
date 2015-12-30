'''
Created on Dec 30, 2015

@author: dewey
'''

import os
from urllib2 import urlopen, URLError

from PyQt4.QtCore import QThread, SIGNAL

class DownloaderThread(QThread):
    
    def __init__(self, parent, url, outfile, key=None, overwrite=False):
        QThread.__init__(self, parent)
        self.keyobj = key
        if(isinstance(url, list)):
            self.url = url
        else:
            self.url = [url, ]
        
        if isinstance(outfile, list):
            if not isinstance(self.url, list):
                raise ValueError("Cannot pass list to outfile if url is not also a list")
            if len(outfile) != len(self.url):
                raise ValueError("url and outfile must be of same length \
                if list is passed to DownloaderThread")
            self.outfile = outfile
        else:
            self.outfile = [outfile, ] * len(self.url)
        
        self.overwrite = overwrite
        self.cancel = False
        self.downloadedfiles = []
    
    def setOnFinished(self, slot):
        if self.keyobj is None:
            self.connect(self, SIGNAL("finished()"), slot)
        else:
            self.connect(self, SIGNAL("finished()"), lambda: slot(self.keyobj))
    
    def setOnError(self, slot):
        if self.keyobj is None:
            self.connect(self, SIGNAL("error(QString)"), slot)
        else:
            self.connect(self, SIGNAL("error(QString)"), lambda string: slot(self.keyobj, string))
    
    def setOnProgress(self, slot):
        if self.keyobj is None:
            self.connect(self, SIGNAL("progress(int, int)"), slot)
        else:
            self.connect(self, SIGNAL("progress(int, int)"), lambda current, total: slot(self.keyobj, current, total))
    
    def run(self):
        #first get total size (also makes sure all URLs are valid
        self.emit(SIGNAL("progress(int, int)"), 0, 0)
        
        
        filenames = []
        totalsize = 0
        badurls = []
        
        for i in range(len(self.url)): 
            outfile = self.outfile[i]
            url = self.url[i]
            if os.path.isdir(outfile):
                filenames.append(os.path.join(outfile, url.split("/")[-1]))
            else:
                filenames.append(filename = outfile)
            try:
                if not os.path.isfile(filenames[i]) or self.overwrite:
                    urlhandle = urlopen(url)
                    totalsize += int(urlhandle.info()["Content-Length"])
                    urlhandle.close()
                else:
                    totalsize += os.path.getsize(filenames[i])
            except URLError as e:
                badurls.append(url)
                self.emit(SIGNAL("error(QString)"), str(e))
            finally:
                try:
                    urlhandle.close()
                except Exception:
                    pass
        
        actualsize = 0
        self.emit(SIGNAL("progress(int, int)"), actualsize, totalsize)
        for i in range(len(self.url)):
            url = self.url[i]
            filename = filenames[i]
            #skip urls that failed the first step
            if url in badurls:
                self.downloadedfiles.append(None)
                continue
            try:
                if not os.path.isfile(filenames[i]) or self.overwrite:
                    fo = open(filename, "wb")
                    urlhandle = urlopen(url)
                    blocksize = 64*1024
                    
                    while not self.cancel:
                        block = urlhandle.read(blocksize)
                        actualsize += len(block)
                        self.emit(SIGNAL("progress(int, int)"), actualsize, totalsize)
                        if len(block) == 0:
                            break
                        fo.write(block)
                    
                    fo.close()
                    urlhandle.close()
                else:
                    actualsize += os.path.getsize(filenames[i])
                    self.emit(SIGNAL("progress(int, int)"), actualsize, totalsize)
                
                self.downloadedfiles.append(filename)
            except IOError as e:
                self.emit(SIGNAL("error(QString)"), str(e))
            finally:
                try:
                    fo.close()
                    urlhandle.close()
                except Exception:
                    pass