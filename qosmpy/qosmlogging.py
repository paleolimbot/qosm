'''
Created on Jan 5, 2016

@author: dewey
'''

import os
import time

FILE = os.path.join(os.path.dirname(__file__), "../qosm.log.txt")
PREVIOUS_FILE = os.path.join(os.path.dirname(__file__), "../qosm.previous.log.txt")
_yesdoitlogme = False

def initialize_logging():
    global _yesdoitlogme
    _yesdoitlogme = True
    if os.path.isfile(PREVIOUS_FILE):
        os.unlink(PREVIOUS_FILE)
    if os.path.isfile(FILE):
        os.rename(FILE, PREVIOUS_FILE)
    f = open(FILE, "w")
    f.write(time.strftime("%c") + ": Logging started\n")
    f.close()

def log(message):
    if _yesdoitlogme:
        try:
            f = open(FILE, "a")
            f.write(time.strftime("%c") + ": ")
            f.write(message)
            f.write("\n")
            f.close()
        except IOError:
            pass #silently fail on logging error