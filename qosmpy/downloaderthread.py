'''
Created on Dec 30, 2015

@author: dewey
'''

import os
from urllib2 import urlopen

from qosmlogging import log
                

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
    log("download() starting with %s urls and %s outfiles" % (len(urllist), len(outfiles)))
    
    downloadedfiles = []
    
    if progresshandler:
        progresshandler(0, len(urllist))
    for i in range(len(urllist)):
        if cancelledcallback():
            return downloadedfiles
        
        url = urllist[i]
        outfile = outfiles[i]
        
        if os.path.isdir(outfile):
            filename = os.path.join(outfile, url.split("/")[-1])
        else:
            filename = outfile

        try:
            if progresshandler:
                progresshandler(i, len(urllist))
            if not os.path.isfile(filename) or overwrite:
                log("Downloading " + url)
                #ensure directory is already created
                directory = os.path.dirname(filename)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                fo = open(filename, "wb")
                urlhandle = urlopen(url)
                blocksize = 64*1024
                
                while not cancelledcallback():
                    block = urlhandle.read(blocksize)
                    if len(block) == 0:
                        break
                    fo.write(block)
                
                fo.close()
                urlhandle.close()
                downloadedfiles.append(filename)
                log("Downloaded to " + filename)
            else:
                log("Skipping existing file: " + filename)
            if cancelledcallback():
                #remove cancelled download file
                os.unlink(filename)
                return downloadedfiles
            
            
            
        except IOError as e:
            log("Error downloading: %s" % e)
            if errorhandler:
                errorhandler(str(e))
            fo.close()
            os.unlink(filename)
        finally:
            try:
                fo.close()
                urlhandle.close()
            except Exception:
                pass
    if progresshandler:
        progresshandler(len(urllist), len(urllist))
    return downloadedfiles