import Queue
import ok
from sys import exit
from math import floor
import rhd2000evalboard
import rhd2000datablock

class binaryStream:
    def __init__(self):
        self.saveOut = None
    def open(self, filename):
        self.saveOut = open(filename, 'rb+')

# To be moved
ofstream = binaryStream()
ofstream.open('test_sample')


import rhd2000evalboard as rhd2kbd

evalboard = rhd2kbd.Rhd2000EvalBoard()

evalboard.open()

#evalboard.uploadFpgaBitfile()

#evalboard.initialize()

#evalboard.setDataSource(0, rhd2kbd.PortA1)

#evalboard.setSampleRate(rhd2kbd.SampleRate20000Hz)

#evalboard.setCableLengthFeet(rhd2kbd.PortA, 3.0)
