import Queue
import ok
from sys import exit
from math import floor
import time

saveOut = open('test.txt', 'w+b')


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


commandSequenceLength = chipRegisters.createCommandListTempSensor(commandList)
evalboard.uploadCommandList(commandList, rhd2kbd.AuxCmd2, 0)
evalboard.selectAuxCommandLength(rhd2kbd.AuxCmd2, 0, commandSequenceLength - 1)
evalboard.selectAuxCommandBank(rhd2kbd.PortA, rhd2kbd.AuxCmd2, 0)


dspCutoffFreq = chipRegisters.setDspCutoffFreq(10.0)
print('Actual DSP Cutoff Frequency : {}'.format(dspCutoffFreq))

chipRegisters.setLowerBandwidth(1.0)
chipRegisters.setUpperBandwidth(7500.0)

commandSequenceLength = chipRegisters.createCommandListRegisterConfig(commandList, False)
print('CMDSEQ')

evalboard.uploadCommandList(commandList, rhd2kbd.AuxCmd3, 0)

chipRegisters.createCommandListRegisterConfig(commandList, True)

evalboard.uploadCommandList(commandList, rhd2kbd.AuxCmd3, 1)

evalboard.selectAuxCommandLength(rhd2kbd.AuxCmd3, 0, commandSequenceLength - 1)

evalboard.selectAuxCommandBank(rhd2kbd.PortA, rhd2kbd.AuxCmd3, 1)

evalboard.setMaxTimeStep(60)
evalboard.setContinuousRunMode(False)

print("Number of 16-bit words in FIFO : {}".format(evalboard.numWordsInFifo()))

evalboard.run()

while evalboard.isRunning() is True:
    pass

print('Number of 16-bit words in FIFO : {}'.format(evalboard.numWordsInFifo()))

dataBlock = rhd2kbd.Rhd2000DataBlock(evalboard.getNumEnabledDataStreams())
evalboard.readDataBlock(dataBlock)

dataBlock.rhdPrint(0)

evalboard.selectAuxCommandBank(rhd2kbd.PortA, rhd2kbd.AuxCmd3, 0)

print("Number of 16-bit words in FIFO : {}".format(evalboard.numWordsInFifo()))

evalboard.flush()
evalboard.resetBoard()


print("Number of 16-bit words in FIFO : {}".format(evalboard.numWordsInFifo()))

print('FIN')


