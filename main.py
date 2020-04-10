import Queue
import ok
from sys import exit
from math import floor
import time

#class binaryStream:
 #   def __init__(self):
 #       self.saveOut = None
 #   def open(self, filename):
 #       self.saveOut = open(filename, 'rb+')

# To be moved
#ofstream = binaryStream()
#ofstream.saveOut('test_sample.txt')


import rhd2000evalboard as rhd2kbd

evalboard = rhd2kbd.Rhd2000EvalBoard()

evalboard.open()

evalboard.uploadFpgaBitfile()

evalboard.initialize()

evalboard.setDataSource(0, rhd2kbd.PortA1)

evalboard.setSampleRate(rhd2kbd.SampleRate20000Hz)

evalboard.setCableLengthFeet(rhd2kbd.PortA, 3.0)

ledArray = [1, 0, 0, 0, 0, 0, 0, 0]
evalboard.setLedDisplay(ledArray)

chipRegisters = rhd2kbd.Rhd2000Registers(evalboard.getSampleRate())
print('REGISTERED CHIP')

commandList = []
commandSequenceLength = int(chipRegisters.createCommandListZcheckDac(commandList, 1000.0, 128.0))
print('GENERATED COMMANDSEQUENCE')

evalboard.uploadCommandList(commandList, rhd2kbd.AuxCmd1, 0)
print('UPLOADED COMMAND LIST')

evalboard.selectAuxCommandLength(rhd2kbd.AuxCmd1, 0, commandSequenceLength - 1)
print('SELECTED AUX COMMAND LENGTH')

evalboard.selectAuxCommandBank(rhd2kbd.PortA, rhd2kbd.AuxCmd1, 0)
print('SEL. AUX CMD BNK')



print('FIN')


