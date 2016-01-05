'''
Created on Dec 30, 2015

@author: dewey
'''

import os
from urllib2 import urlopen, URLError
                

def _default_cancelled_callback():
    return False
                
def download(urllist, outfiles, overwrite=False, progresshandler=None, errorhandler=None, cancelledcallback=_default_cancelled_callback):
    
    if isinstance(outfiles, list):
        if not isinstance(urllist, list):
            raise ValueError("Cannot pass list to outfiles if urllist is not also a list")
        if len(outfiles) != len(urllist):
            raise ValueError("url and outfile must be of same length \
            if list is passed to download")
    else:
        outfiles = [outfiles, ] * len(urllist)
    
    filenames = []
    totalsize = 0
    badurls = []
    
    downloadedfiles = []
    
    for i in range(len(urllist)):
        if cancelledcallback():
            return []
        
        outfile = outfiles[i]
        url = urllist[i]
        if os.path.isdir(outfile):
            filenames.append(os.path.join(outfile, url.split("/")[-1]))
        else:
            filenames.append(outfile)
        try:
            if not os.path.isfile(filenames[i]) or overwrite:
                urlhandle = urlopen(url)
                totalsize += int(urlhandle.info()["Content-Length"])
                urlhandle.close()
            else:
                totalsize += os.path.getsize(filenames[i])
        except URLError as e:
            badurls.append(url)
            if errorhandler:
                errorhandler(str(e))
        finally:
            try:
                urlhandle.close()
            except Exception:
                pass
    
    actualsize = 0
    if progresshandler:
        progresshandler(actualsize, totalsize)
    for i in range(len(urllist)):
        if cancelledcallback():
            return downloadedfiles
        
        url = urllist[i]
        filename = filenames[i]
        #skip urls that failed the first step
        if url in badurls:
            downloadedfiles.append(None)
            continue
        try:
            if not os.path.isfile(filename) or overwrite:
                #ensure directory is already created
                directory = os.path.dirname(filename)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                fo = open(filename, "wb")
                urlhandle = urlopen(url)
                blocksize = 64*1024
                
                while not cancelledcallback():
                    block = urlhandle.read(blocksize)
                    actualsize += len(block)
                    if progresshandler:
                        progresshandler(actualsize, totalsize)
                    if len(block) == 0:
                        break
                    fo.write(block)
                
                fo.close()
                urlhandle.close()
                if cancelledcallback():
                    #remove cancelled download file
                    os.unlink(filename)
                    return downloadedfiles
            else:
                actualsize += os.path.getsize(filenames[i])
                if progresshandler:
                        progresshandler(actualsize, totalsize)
            
            downloadedfiles.append(filename)
        except IOError as e:
            if errorhandler:
                errorhandler(str(e))
        finally:
            try:
                fo.close()
                urlhandle.close()
            except Exception:
                pass
    return downloadedfiles