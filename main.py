import Queue
import ok
from sys import exit
from math import floor
import time
from math import ceil, floor

# Stream > Channel > Time

# Initialization of Device
import rhd2000evalboard as rhd2kbd

run_settings = {'continuousRunMode' : True, 'SampleRate': rhd2kbd.SampleRate20000Hz, 'RefreshRate' : 30}

def getBoardSampleRate():
    return run_settings['SampleRate']
def getObjectiveRefreshRate():
    return run_settings['RefreshRate']

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


# Sample 1 second RUN

evalboard.setMaxTimeStep(60)
evalboard.setContinuousRunMode(False)

print("NumWords in FIFO before Test Run : {}".format(evalboard.numWordsInFifo()))
print("FIFO buffer capacity : {}".format(evalboard.fifoCapacityInWords()))

evalboard.run()

dataBlock = rhd2kbd.Rhd2000DataBlock(evalboard.getNumEnabledDataStreams())

evalboard.readDataBlock(dataBlock)
dataBlock.rhdPrint(0)
print("NumWords in FIFO after Test Run : {}".format(evalboard.numWordsInFifo()))

# Real Run -----------------------------

evalboard.selectAuxCommandBank(rhd2kbd.PortA, rhd2kbd.AuxCmd3, 0)

# Acquire Datablock Size For Sample Run
dataBlockSize = dataBlock.calculateDataBlockSizeInWords(evalboard.getNumEnabledDataStreams())

# Select Number of Datablocks to read to achieve objective RefreshRate
# 20000hz -> 20000 samples per sec. 1 sample per 1/20000sec.
usbBlocksToRead = int(ceil(getBoardSampleRate() / (rhd2kbd.SAMPLES_PER_DATA_BLOCK * getObjectiveRefreshRate())))
timePerReadingSessionIncr = rhd2kbd.SAMPLES_PER_DATA_BLOCK / getBoardSampleRate() * usbBlocksToRead

# Keep Track of Elapsed Time(s)
time = 0

print("NumWords in FIFO before session : {}".format(evalboard.numWordsInFifo()))

# Preparations b4 starting session
dataQueue = Queue.Queue()
del dataBlock
dataBlock = rhd2kbd.Rhd2000DataBlock(evalboard.getNumEnabledDataStreams())
dataBlockLength = dataBlock.calculateDataBlockSizeInWords(evalboard.getNumEnabledDataStreams())
#testBufferQueue = []

terminate = False


while terminate is False:
    dataBlock = rhd2kbd.Rhd2000DataBlock(evalboard.getNumEnabledDataStreams())
    evalboard.setMaxTimeStep(60)
    evalboard.setContinuousRunMode(False)
    evalboard.run()
    while evalboard.isRunning() is True:
        pass
    evalboard.readDataBlock(dataBlock)
    #testBufferQueue.append(dataBlock)
    for i in range(len(dataBlock.amplifierData[0][0])):
        print(dataBlock.amplifierData[0][0][i])
    del dataBlock
    #print('Datablock Created')

print("Number of 16-bit words in FIFO before Reset : {}".format(evalboard.numWordsInFifo()))

evalboard.flush()
evalboard.resetBoard()


print("Number of 16-bit words in FIFO after Reset : {}".format(evalboard.numWordsInFifo()))

print('FIN')

