# --------- RHD2000EVALBOARD.h

# Imports
import Queue
import ok
from sys import exit
from math import floor, exp
import copy

# Variable Definitions
global USB_BUFFER_SIZE
USB_BUFFER_SIZE = 2400000

global RHYTHM_BOARD_ID
RHYTHM_BOARD_ID = 500

global MAX_NUM_DATA_STREAMS
MAX_NUM_DATA_STREAMS = 8

global FIFO_CAPACITY_WORDS
FIFO_CAPACITY_WORDS = 67108864

# Variable definitions for Amplifier Sample Rate (46)
SampleRate1000Hz = 1000.0
SampleRate1250Hz = 1250.0
SampleRate1500Hz = 1500.0
SampleRate2000Hz = 2000.0
SampleRate2500Hz = 2500.0
SampleRate3000Hz = 3000.0
SampleRate3333Hz = 10000.0 / 3.0
SampleRate4000Hz = 4000.0
SampleRate5000Hz = 5000.0
SampleRate6250Hz = 6250.0
SampleRate8000Hz = 8000.0
SampleRate10000Hz = 10000.0
SampleRate12500Hz = 12500.0
SampleRate15000Hz = 15000.0
SampleRate20000Hz = 20000.0
SampleRate25000Hz = 25000.0
SampleRate30000Hz = 30000.0

# USB Interface Endpoint Addr
WireInResetRun = 0x00
WireInMaxTimeStepLsb = 0x01
WireInMaxTimeStepMsb = 0x02
WireInDataFreqPll = 0x03
WireInMisoDelay = 0x04
WireInCmdRamAddr = 0x05
WireInCmdRamBank = 0x06
WireInCmdRamData = 0x07
WireInAuxCmdBank1 = 0x08
WireInAuxCmdBank2 = 0x09
WireInAuxCmdBank3 = 0x0a
WireInAuxCmdLength1 = 0x0b
WireInAuxCmdLength2 = 0x0c
WireInAuxCmdLength3 = 0x0d
WireInAuxCmdLoop1 = 0x0e
WireInAuxCmdLoop2 = 0x0f
WireInAuxCmdLoop3 = 0x10
WireInLedDisplay = 0x11
WireInDataStreamSel1234 = 0x12
WireInDataStreamSel5678 = 0x13
WireInDataStreamEn = 0x14
WireInTtlOut = 0x15
WireInDacSource1 = 0x16
WireInDacSource2 = 0x17
WireInDacSource3 = 0x18
WireInDacSource4 = 0x19
WireInDacSource5 = 0x1a
WireInDacSource6 = 0x1b
WireInDacSource7 = 0x1c
WireInDacSource8 = 0x1d
WireInDacManual = 0x1e
WireInMultiUse = 0x1f

TrigInDcmProg = 0x40
TrigInSpiStart = 0x41
TrigInRamWrite = 0x42
TrigInDacThresh = 0x43
TrigInDacHpf = 0x44
TrigInExtFastSettle = 0x45
TrigInExtDigOut = 0x46

WireOutNumWordsLsb = 0x20
WireOutNumWordsMsb = 0x21
WireOutSpiRunning = 0x22
WireOutTtlIn = 0x23
WireOutDataClkLocked = 0x24
WireOutBoardMode = 0x25
WireOutBoardId = 0x3e
WireOutBoardVersion = 0x3f

PipeOutData = 0xa0

# AuxCmdSlot -> Changed to string
AuxCmd1 = 'AuxCmd1'
AuxCmd2 = 'AuxCmd2'
AuxCmd3 = 'AuxCmd3'

# BoardPort -> Changed to string
PortA, PortB, PortC, PortD = ['PortA', 'PortB', 'PortC', 'PortD']
PortA1, PortB1, PortC1, PortD1 = ['0', '2', '4', '6']
PortA2, PortB2, PortC2, PortD2 = ['1', '3', '5', '7']


# Global variables

def fillFromUsbBuffer(dataBlock, usbBuffer, blockIndex, numDataStreams):
    index = blockIndex * 2 * dataBlock.calculateDataBlockSizeInWords(numDataStreams)
    for t in range(SAMPLES_PER_DATA_BLOCK):
        #if dataBlock.checkUsbHeader(usbBuffer, index) is False:
            #raise Exception("Error in Rhd2000EvalBoard::readDataBlock: Incorrect header.")
        index = index + 8
        dataBlock.timeStamp[t] = dataBlock.convertUsbTimeStamp(usbBuffer, index)
        index = index + 4
        for channel in range(3):
            for stream in range(numDataStreams):
                dataBlock.auxiliaryData[stream][channel][t] = dataBlock.convertUsbWord(usbBuffer, index)
                if t == 28 and channel == 1:
                    print("usbBuffer for Voltage readings : {}".format(usbBuffer[index]))
                    print("usbBuffer -> Converted : {}".format(dataBlock.auxiliaryData[stream][channel][t]))
                if t == 12 and channel == 1:
                    print("usbBuffer for tempA readings : {}".format(usbBuffer[index]))
                    print("tempA -> Converted : {}".format(dataBlock.auxiliaryData[stream][channel][t]))
                if t == 20 and channel == 1:
                    print("usbBuffer for tempB readings : {}".format(usbBuffer[index]))
                    print("tempB -> Converted : {}".format(dataBlock.auxiliaryData[stream][channel][t]))
                index = index + 2
        for channel in range(32):
            for stream in range(numDataStreams):
                dataBlock.amplifierData[stream][channel][t] = dataBlock.convertUsbWord(usbBuffer, index)
                index = index + 2
            index = index + 2 * numDataStreams
            for i in range(8):
                dataBlock.boardAdcData[i][t] = dataBlock.convertUsbWord(usbBuffer, index)
                index = index + 2
            dataBlock.ttlIn[t] = dataBlock.convertUsbWord(usbBuffer, index)
            index = index + 2
            dataBlock.ttlOut[t] = dataBlock.convertUsbWord(usbBuffer, index)
            index += 2


# --------- RHDEVALBOARD.CPP

class Rhd2000EvalBoard:
    def __init__(self):
        self.sampleRate = SampleRate30000Hz
        self.numDataStreams = 0
        self.dataStreamEnabled = [0] * MAX_NUM_DATA_STREAMS
        for i in range(MAX_NUM_DATA_STREAMS):
            self.dataStreamEnabled[i] = 0
        self.usbBuffer = [0 for i in range(USB_BUFFER_SIZE)]
        self.cableDelay = [-1] * 4

    def open(self):
        print("---- Intan Technologies ---- Rhythm RHD2000 Controller v1.0 ----")
        try:
            self.intan = ok.okCFrontPanel()
        except:
            print("Error loading Frontpanel Library")
            exit(0)
        print("Scanning USB for Opal Kelly devices...")
        nDevices = self.intan.GetDeviceCount()
        print("Found {} Opal Kelly Devices".format(nDevices))
        for i in range(nDevices):
            productName = self.intan.GetDeviceListModel(i)
            print("Device #{} : Opal Kelly {} with Serial No. {}".format(i, self.opalKellyModelName(productName),
                                                                         self.intan.GetDeviceListSerial(i)))
            if productName == ok.OK_PRODUCT_XEM6010LX45:
                serialNumber = self.intan.GetDeviceListSerial(i)
        print("Attempting to Connect to Device {}".format(serialNumber))
        try:
            result = self.intan.OpenBySerial(serialNumber)
            if self.intan.NoError != result:
                print('Error while initializing connection to Serial Deivce')
                print('Device could not be opened.  Is one connected?')
                print('Error = {}'.format(result))
                exit(0)
            else:
                print('Connected to Device {}'.format(serialNumber))
        except:
            print('Some other error occurred while connecting to device.')
            exit(0)

        self.intan.LoadDefaultPLLConfiguration()
        self.deviceInfo = ok.okTDeviceInfo()
        print(self.deviceInfo)
        print('Opal Kelly Device Firmware Version : {}'.format(self.deviceInfo.deviceMajorVersion))
        print('Opal Kelly Device Serial No. : {}'.format(self.deviceInfo.serialNumber))
        print('Opal Kelly Device ID : {}'.format(self.deviceInfo.deviceID))

    def uploadFpgaBitfile(self):
        err_code = self.intan.ConfigureFPGA('main.bit')
        if err_code == self.intan.NoError:
            print("Successfully uploaded FPGA Map.")
            pass
        elif err_code == self.intan.DeviceNotOpen:
            print("FPGA configuration failed: Device not open.")
            return False
        elif err_code == self.intan.FileError:
            print("FPGA configuration failed: Cannot find configuration file.")
            return False
        elif err_code == self.intan.InvalidBitstream:
            print("FPGA configuration failed: Bitstream is not properly formatted.")
            return False
        elif err_code == self.intan.DoneNotHigh:
            print("FPGA configuration failed: FPGA DONE signal did not assert after configuration.")
            return False
        elif err_code == self.intan.TransferError:
            print("FPGA configuration failed: USB error occurred during download.")
            return False
        elif err_code == self.intan.CommunicationError:
            print("FPGA configuration failed: Communication error with firmware.")
            return False
        elif err_code == self.intan.UnsupportedFeature:
            print("FPGA configuration failed: Unsupported feature.")
            return False
        else:
            print("FPGA configuration failed: Unknown error.")
            return False

        if self.intan.IsFrontPanelEnabled() is False:
            print("Opal Kelly FrontPanel support is not enabled in this FPGA configuration.")
            del self.intan
            return False

        self.intan.UpdateWireOuts()
        boardId = self.intan.GetWireOutValue(WireOutBoardId)
        boardVersion = self.intan.GetWireOutValue(WireOutBoardVersion)

        if boardId != RHYTHM_BOARD_ID:
            print("FPGA configuration does not support Rhythm.  Incorrect board ID: {}".format(boardId))
            return False
        else:
            print("Rhythm configuration file successfully loaded.  Rhythm version number: {}".format(boardVersion))

        return True

    def getSystemCLockFreq(self):
        print('Not Implemented Yet')

    def resetBoard(self):
        self.intan.SetWireInValue(WireInResetRun, 0x01, 0x01)
        self.intan.UpdateWireIns()
        self.intan.SetWireInValue(WireInResetRun, 0x00, 0x01)
        self.intan.UpdateWireIns()

    def setSampleRate(self, newSampleRate):
        sampleSwitch = {
            SampleRate1000Hz: [7, 125],
            SampleRate1250Hz: [7, 100],
            SampleRate1500Hz: [21, 250],
            SampleRate2000Hz: [14, 125],
            SampleRate2500Hz: [35, 250],
            SampleRate3000Hz: [21, 125],
            SampleRate3333Hz: [14, 75],
            SampleRate4000Hz: [28, 125],
            SampleRate5000Hz: [7, 25],
            SampleRate6250Hz: [7, 20],
            SampleRate8000Hz: [112, 250],
            SampleRate10000Hz: [14, 25],
            SampleRate12500Hz: [7, 10],
            SampleRate15000Hz: [21, 25],
            SampleRate20000Hz: [28, 25],
            SampleRate25000Hz: [35, 25],
            SampleRate30000Hz: [42, 25]
        }
        M, D = sampleSwitch.get(newSampleRate, "Error!")
        print("M, D = {}, {}".format(M, D))

        self.sampleRate = newSampleRate

        while self.isDcmProgDone() is False:
            pass
        self.intan.SetWireInValue(WireInDataFreqPll, (256 * M + D))
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInDcmProg, 0)

        while self.isDataClockLocked() is False:
            pass

        return True

    def isDcmProgDone(self):
        self.intan.UpdateWireOuts()
        value = self.intan.GetWireOutValue(WireOutDataClkLocked)
        return (value & 0x0002) > 1

    def isDataClockLocked(self):
        self.intan.UpdateWireOuts()
        value = self.intan.GetWireOutValue(WireOutDataClkLocked)
        return (value & 0x0001) > 0

    def initialize(self):
        self.resetBoard()
        self.setSampleRate(SampleRate30000Hz)
        print('SET SAMPLE RATE')
        self.selectAuxCommandBank(PortA, AuxCmd1, 0)
        self.selectAuxCommandBank(PortB, AuxCmd1, 0)
        self.selectAuxCommandBank(PortC, AuxCmd1, 0)
        self.selectAuxCommandBank(PortD, AuxCmd1, 0)
        self.selectAuxCommandBank(PortA, AuxCmd2, 0)
        self.selectAuxCommandBank(PortB, AuxCmd2, 0)
        self.selectAuxCommandBank(PortC, AuxCmd2, 0)
        self.selectAuxCommandBank(PortD, AuxCmd2, 0)
        self.selectAuxCommandBank(PortA, AuxCmd3, 0)
        self.selectAuxCommandBank(PortB, AuxCmd3, 0)
        self.selectAuxCommandBank(PortC, AuxCmd3, 0)
        self.selectAuxCommandBank(PortD, AuxCmd3, 0)
        self.selectAuxCommandLength(AuxCmd1, 0, 0)
        self.selectAuxCommandLength(AuxCmd2, 0, 0)
        self.selectAuxCommandLength(AuxCmd3, 0, 0)
        print('SET AUX CMD LENGTH')
        self.setContinuousRunMode(True)
        self.setMaxTimeStep(4294967295)  # 4294967295 == (2^32 - 1)
        self.setCableLengthFeet(PortA, 3.0)
        self.setCableLengthFeet(PortB, 3.0)
        self.setCableLengthFeet(PortC, 3.0)
        self.setCableLengthFeet(PortD, 3.0)
        print('SET CABLE LENGTH')
        self.setDspSettle(False)
        self.setDataSource(0, PortA1)
        self.setDataSource(1, PortB1)
        self.setDataSource(2, PortC1)
        self.setDataSource(3, PortD1)
        self.setDataSource(4, PortA2)
        self.setDataSource(5, PortB2)
        self.setDataSource(6, PortC2)
        self.setDataSource(7, PortD2)
        print('SET DATA SOURCE')
        self.enableDataStream(0, True)
        # CHANGE THIS IN ORDER TO ENABLE ALL DATA STREAMS
        # 1 Port houses two streams : PortA1, PortA2, PortB1, PortB2 .......
        # 32 inputs per stream & 2 streams per port & 4 ports
        # False to enable only stream 0(Port A1), True to enable all streams
        for i in range(1, MAX_NUM_DATA_STREAMS):
            self.enableDataStream(i, True)
        print('ENABLED DATA STREAM')
        self.clearTtlOut()
        print('CLEARED TTL')
        self.enableDac(0, False)
        self.enableDac(1, False)
        self.enableDac(2, False)
        self.enableDac(3, False)
        self.enableDac(4, False)
        self.enableDac(5, False)
        self.enableDac(6, False)
        self.enableDac(7, False)
        print('ENABLED DAC')
        self.selectDacDataStream(0, 0)
        self.selectDacDataStream(1, 0)
        self.selectDacDataStream(2, 0)
        self.selectDacDataStream(3, 0)
        self.selectDacDataStream(4, 0)
        self.selectDacDataStream(5, 0)
        self.selectDacDataStream(6, 0)
        self.selectDacDataStream(7, 0)
        self.selectDacDataChannel(0, 0)
        self.selectDacDataChannel(1, 0)
        self.selectDacDataChannel(2, 0)
        self.selectDacDataChannel(3, 0)
        self.selectDacDataChannel(4, 0)
        self.selectDacDataChannel(5, 0)
        self.selectDacDataChannel(6, 0)
        self.selectDacDataChannel(7, 0)
        print('SELECTED DAC CHANNEL')
        self.setDacManual(32768)
        self.setDacGain(0)
        self.setAudioNoiseSuppress(0)
        self.setTtlMode(1)
        self.setDacThreshold(0, 32768, True)
        self.setDacThreshold(1, 32768, True)
        self.setDacThreshold(2, 32768, True)
        self.setDacThreshold(3, 32768, True)
        self.setDacThreshold(4, 32768, True)
        self.setDacThreshold(5, 32768, True)
        self.setDacThreshold(6, 32768, True)
        self.setDacThreshold(7, 32768, True)
        print('SET DAC THRESHOLD')
        self.enableExternalFastSettle(False)
        self.setExternalFastSettleChannel(0)
        self.enableExternalDigOut(PortA, False)
        self.enableExternalDigOut(PortB, False)
        self.enableExternalDigOut(PortC, False)
        self.enableExternalDigOut(PortD, False)
        self.setExternalDigOutChannel(PortA, 0)
        self.setExternalDigOutChannel(PortB, 0)
        self.setExternalDigOutChannel(PortC, 0)
        self.setExternalDigOutChannel(PortD, 0)
        print('BOARD INITIALIZATION COMPLETE')

    def selectAuxCommandBank(self, port, auxCommandSlot, bank):
        if auxCommandSlot != 'AuxCmd1' and auxCommandSlot != 'AuxCmd2' and auxCommandSlot != 'AuxCmd3':
            raise Exception("Error in Rhd2000EvalBoard::selectAuxCommandBank: auxCommandSlot out of range.")
        if bank < 0 or bank > 15:
            raise Exception("Error in Rhd2000EvalBoard::selectAuxCommandBank: bank out of range.")
        switchPort = {
            'PortA': 0,
            'PortB': 4,
            'PortC': 8,
            'PortD': 12
        }
        bitShift = switchPort.get(port, "Error!")

        switchauxCommandSlot = {
            'AuxCmd1': [WireInAuxCmdBank1, bank << bitShift, 0x000f << bitShift],
            'AuxCmd2': [WireInAuxCmdBank2, bank << bitShift, 0x000f << bitShift],
            'AuxCmd3': [WireInAuxCmdBank3, bank << bitShift, 0x000f << bitShift]
        }
        result_switchauxCommandSlot = switchauxCommandSlot.get(auxCommandSlot, 'Error!')
        self.intan.SetWireInValue(result_switchauxCommandSlot[0], result_switchauxCommandSlot[1],
                                  result_switchauxCommandSlot[2])
        self.intan.UpdateWireIns()

    def selectAuxCommandLength(self, auxCommandSlot, loopIndex, endIndex):
        if auxCommandSlot not in [AuxCmd1, AuxCmd2, AuxCmd3]:
            raise Exception("Error in Rhd2000EvalBoard::selectAuxCommandLength: auxCommandSlot out of range.")
        if loopIndex < 0 or loopIndex > 1023:
            raise Exception("Error in Rhd2000EvalBoard::selectAuxCommandLength: loopIndex out of range.")
        if endIndex < 0 or endIndex > 1023:
            raise Exception('Error in Rhd2000EvalBoard::selectAuxCommandLength: endIndex out of range.')
        if auxCommandSlot == AuxCmd1:
            self.intan.SetWireInValue(WireInAuxCmdLoop1, loopIndex)
            self.intan.SetWireInValue(WireInAuxCmdLength1, endIndex)
        elif auxCommandSlot == AuxCmd2:
            self.intan.SetWireInValue(WireInAuxCmdLoop2, loopIndex)
            self.intan.SetWireInValue(WireInAuxCmdLength2, endIndex)
        elif auxCommandSlot == AuxCmd3:
            self.intan.SetWireInValue(WireInAuxCmdLoop3, loopIndex)
            self.intan.SetWireInValue(WireInAuxCmdLength3, endIndex)

        self.intan.UpdateWireIns()

    def setContinuousRunMode(self, continuousMode):
        if continuousMode:
            self.intan.SetWireInValue(WireInResetRun, 0x02, 0x02)
        else:
            self.intan.SetWireInValue(WireInResetRun, 0x00, 0x02)
        self.intan.UpdateWireIns()

    def setMaxTimeStep(self, maxTimeStep):
        maxTimeStepLsb = maxTimeStep & 0x0000ffff
        maxTimeStepMsb = maxTimeStep & 0xffff0000
        self.intan.SetWireInValue(WireInMaxTimeStepLsb, maxTimeStepLsb)
        self.intan.SetWireInValue(WireInMaxTimeStepMsb, maxTimeStepMsb >> 16)
        self.intan.UpdateWireIns()

    def setCableLengthFeet(self, port, lengthInFeet):
        self.setCableLengthMeters(port, 0.3048 * lengthInFeet)

    def setCableLengthMeters(self, port, lengthInMeters):
        speedOfLight = 299792458.0
        xilinxLvdsOutputDelay = 1.9e-9
        xilinxLvdsInputDelay = 1.4e-9
        rhd2000Delay = 9.0e-9
        misoSettleTime = 6.7e-9
        tStep = 1.0 / (2800.0 * self.sampleRate)
        cableVelocity = 0.555 * speedOfLight
        distance = 2.0 * lengthInMeters
        timeDelay = (
                            distance / cableVelocity) + xilinxLvdsOutputDelay + rhd2000Delay + xilinxLvdsInputDelay + misoSettleTime
        delay = floor(((timeDelay / tStep) + 1.0) + 0.5)
        if delay < 1:
            delay = 1
        self.setCableDelay(port, delay)

    def getSampleRate(self):
        print("No need to be used : use definitions at the top instead.")
        return self.sampleRate

    def setCableDelay(self, port, delay):
        if delay < 0 or delay > 15:
            raise Exception("Warning in Rhd2000EvalBoard::setCableDelay: delay out of range: {}".format(delay))
        if delay < 0:
            delay = 0
        elif delay > 15:
            delay = 15

        switchPort = {
            PortA: [0, 0],
            PortB: [4, 1],
            PortC: [8, 2],
            PortD: [12, 3]
        }
        i, j = switchPort.get(port, "Error!")
        bitShift = i
        self.cableDelay[j] = delay
        self.intan.SetWireInValue(WireInMisoDelay, int(delay) << int(bitShift), 0x000f << int(bitShift))
        self.intan.UpdateWireIns()

    def setDspSettle(self, enabled):
        if enabled is True:
            i = 0x04
        else:
            i = 0x00
        self.intan.SetWireInValue(WireInResetRun, i, 0x04)
        self.intan.UpdateWireIns()

    def setDataSource(self, stream, dataSource):
        if stream < 0 or stream > 7:
            raise Exception("Error in Rhd2000EvalBoard::setDataSource: stream out of range.")
        if stream < 4:
            endPoint = WireInDataStreamSel1234
            bitShift = int(stream * 4)
        else:
            endPoint = WireInDataStreamSel5678
            bitShift = int((stream - 4) * 4)
        self.intan.SetWireInValue(endPoint, int(dataSource) << int(bitShift), 0x000f << int(bitShift))
        self.intan.UpdateWireIns()

    def enableDataStream(self, stream, enabled):
        if stream < 0 or stream > MAX_NUM_DATA_STREAMS - 1:
            raise Exception("Error in Rhd2000EvalBoard::setDataSource: stream out of range.")
        if enabled is True:
            if self.dataStreamEnabled[stream] == 0:
                self.intan.SetWireInValue(WireInDataStreamEn, 0x0001 << stream, 0x0001 << stream)
                self.intan.UpdateWireIns()
                self.dataStreamEnabled[stream] = 1
                self.numDataStreams += 1
            else:
                if self.dataStreamEnabled[stream] == 1:
                    self.intan.SetWireInValue(WireInDataStreamEn, 0x0000 << stream, 0x0001 << stream)
                    self.intan.UpdateWireIns()
                    self.dataStreamEnabled[stream] = 0
                    self.numDataStreams = self.numDataStreams - 1

    def clearTtlOut(self):
        self.intan.SetWireInValue(WireInTtlOut, 0x0000)
        self.intan.UpdateWireIns()

    def enableDac(self, dacChannel, enabled):
        if dacChannel < 0 or dacChannel > 7:
            raise Exception("Error in Rhd2000EvalBoard::enableDac: dacChannel out of range.")
        dacSource = [WireInDacSource1, WireInDacSource2, WireInDacSource3, WireInDacSource4, WireInDacSource5,
                     WireInDacSource6, WireInDacSource7, WireInDacSource8]
        if enabled is True:
            i = 0x0200
        else:
            i = 0x0000
        self.intan.SetWireInValue(dacSource[dacChannel], i, 0x0200)
        self.intan.UpdateWireIns()

    def selectDacDataStream(self, dacChannel, stream):
        if dacChannel < 0 or dacChannel > 7:
            raise Exception("Error in Rhd2000EvalBoard::enableDac: dacChannel out of range.")
        if stream < 0 or stream > 9:
            raise Exception("Error in Rhd2000EvalBoard::selectDacDataStream: stream out of range.")
        dacSource = [WireInDacSource1, WireInDacSource2, WireInDacSource3, WireInDacSource4, WireInDacSource5,
                     WireInDacSource6, WireInDacSource7, WireInDacSource8]
        self.intan.SetWireInValue(dacSource[dacChannel], stream << 5, 0x01e0)
        self.intan.UpdateWireIns()

    def selectDacDataChannel(self, dacChannel, dataChannel):
        if dacChannel < 0 or dacChannel > 7:
            raise Exception("Error in Rhd2000EvalBoard::enableDac: dacChannel out of range.")
        if dataChannel < 0 or dataChannel > 7:
            raise Exception("Error in Rhd2000EvalBoard::selectDacDataChannel: dataChannel out of range.")
        dacSource = [WireInDacSource1, WireInDacSource2, WireInDacSource3, WireInDacSource4, WireInDacSource5,
                     WireInDacSource6, WireInDacSource7, WireInDacSource8]
        self.intan.SetWireInValue(dacSource[dacChannel], dataChannel << 0, 0x001f)
        self.intan.UpdateWireIns()

    def setDacManual(self, value):
        if value < 0 or value > 65535:
            raise Exception("Error in Rhd2000EvalBoard::setDacManual: value out of range.")
        self.intan.SetWireInValue(WireInDacManual, value)
        self.intan.UpdateWireIns()

    def setDacGain(self, gain):
        if gain < 0 or gain > 7:
            raise Exception("Error in Rhd2000EvalBoard::setDacGain: gain out of range.")
        self.intan.SetWireInValue(WireInResetRun, gain << 13, 0xe000)
        self.intan.UpdateWireIns()

    def setAudioNoiseSuppress(self, noiseSuppress):
        if noiseSuppress < 0 or noiseSuppress > 127:
            raise Exception("Error in Rhd2000EvalBoard::setAudioNoiseSuppress: noiseSuppress out of range.")
        self.intan.SetWireInValue(WireInResetRun, noiseSuppress << 6, 0x1fc0)
        self.intan.UpdateWireIns()

    def setTtlMode(self, mode):
        if mode < 0 or mode > 1:
            raise Exception("Error in Rhd2000EvalBoard::setTtlMode: mode out of range.")
        self.intan.SetWireInValue(WireInResetRun, mode << 3, 0x0008)
        self.intan.UpdateWireIns()

    def setDacThreshold(self, dacChannel, threshold, trigPolarity):
        if dacChannel < 0 or dacChannel > 7:
            raise Exception("Error in Rhd2000EvalBoard::enableDac: dacChannel out of range.")
        if threshold < 0 or threshold > 65535:
            raise Exception("Error in Rhd2000EvalBoard::setDacThreshold: threshold out of range.")
        self.intan.SetWireInValue(WireInMultiUse, threshold)
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInDacThresh, dacChannel)
        self.intan.SetWireInValue(WireInMultiUse, 1 if trigPolarity is True else 0)
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInDacThresh, dacChannel + 8)

    def enableExternalFastSettle(self, enable):
        self.intan.SetWireInValue(WireInMultiUse, 1 if enable is True else 0)
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInExtFastSettle, 0)

    def setExternalFastSettleChannel(self, channel):
        if channel < 0 or channel > 15:
            raise Exception("Error in Rhd2000EvalBoard::setExternalFastSettleChannel: channel out of range.")
        self.intan.SetWireInValue(WireInMultiUse, channel)
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInExtFastSettle, 1)

    def enableExternalDigOut(self, port, enable):
        self.intan.SetWireInValue(WireInMultiUse, 1 if enable is True else 0)
        self.intan.UpdateWireIns()
        ports_lst = [PortA, PortB, PortC, PortD]
        if port in ports_lst:
            i = ports_lst.index(port)
            self.intan.ActivateTriggerIn(TrigInExtDigOut, i)
        else:
            raise Exception("Error in Rhd2000EvalBoard::enableExternalDigOut: port out of range.")

    def setExternalDigOutChannel(self, port, channel):
        if channel < 0 or channel > 15:
            raise Exception("Error in Rhd2000EvalBoard::setExternalDigOutChannel: channel out of range.")
        self.intan.SetWireInValue(WireInMultiUse, channel)
        self.intan.UpdateWireIns()
        ports_lst = [PortA, PortB, PortC, PortD]
        if port in ports_lst:
            i = ports_lst.index(port) + 4
            self.intan.ActivateTriggerIn(TrigInExtDigOut, i)
        else:
            raise Exception("Error in Rhd2000EvalBoard::setExternalDigOutChannel: port out of range.")

    def enableDacHighpassFilter(self, enable):
        self.intan.SetWireInValue(WireInMultiUse, 1 if enable is True else 0)
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInDacHpf, 0)

    def setDacHighpassFilter(self, cutoff):
        pi = 3.1415926535897
        b = 1.0 - exp(-2.0 * pi * cutoff / self.sampleRate)
        filterCoefficient = floor(65536.0 * b + 0.5)
        if filterCoefficient > 1:
            filterCoefficient = 1
        elif filterCoefficient > 65535:
            filterCoefficient = 65535
        self.intan.SetWireInValue(WireInMultiUse, filterCoefficient)
        self.intan.UpdateWireIns()
        self.intan.ActivateTriggerIn(TrigInDacHpf, 1)

    def numWordsInFifo(self):
        self.intan.UpdateWireOuts()
        value = (self.intan.GetWireOutValue(WireOutNumWordsMsb) << 16) + self.intan.GetWireOutValue(WireOutNumWordsLsb)
        return value

    def fifoCapacityInWords(self):
        return FIFO_CAPACITY_WORDS

    def flush(self):
        while self.numWordsInFifo() >= USB_BUFFER_SIZE / 2:
            self.intan.ReadFromPipeOut(PipeOutData, self.usbBuffer)
            # ReadFromPipeOut overwrites usbBuffer with PipeOutData(new incoming data)
        while self.numWordsInFifo() > 0:
            self.intan.ReadFromPipeOut(PipeOutData, self.usbBuffer)

    def opalKellyModelName(self, model):
        if model == ok.OK_PRODUCT_XEM6010LX45:
            return 'XEM6010LX45'
        else:
            return 'Unknown'
        # We only use XEM6010lx45

    def run(self):
        self.intan.ActivateTriggerIn(TrigInSpiStart, 0)

    def isRunning(self):
        self.intan.UpdateWireOuts()
        value = self.intan.GetWireOutValue(WireOutSpiRunning)
        if (value & 0x01) == 0:
            return False
        else:
            return True

    def setTtlOut(self, ttlOutArray):
        ttlOut = 0
        for i in range(16):
            if ttlOutArray[i] > 0:
                ttlOut += 1 << i
        self.intan.SetWireInValue(WireInTtlOut, ttlOut)
        self.intan.UpdateWireIns()

    def getTtlIn(self, ttlInArray):
        self.intan.UpdateWireOuts()
        ttlIn = self.intan.GetWireOutValue(WireOutTtlIn)
        for i in range(16):
            ttlInArray[i] = 0
            if (ttlIn & (1 << i)) > 0:
                ttlInArray[i] = 1

    def setLedDisplay(self, ledArray):
        ledOut = 0
        for i in range(8):
            if ledArray[i] > 0:
                ledOut += 1 << i
        self.intan.SetWireInValue(WireInLedDisplay, ledOut)
        self.intan.UpdateWireIns()

    def estimateCableLengthMeters(self, delay):
        speedOfLight = 299792458.0
        xilinxLvdsOutputDelay = 1.9e-9
        xilinxLvdsInputDelay = 1.4e-9
        rhd2000Delay = 9.0e-9
        misoSettleTime = 6.7e-9
        tStep = 1.0 / (2800.0 * self.getSampleRate())
        cableVelocity = 0.555 * speedOfLight
        distance = cableVelocity * (((delay) - 1.0) * tStep - (
                xilinxLvdsOutputDelay + rhd2000Delay + xilinxLvdsInputDelay + misoSettleTime))
        if distance < 0.0:
            distance = 0.0
        return distance / 2.0

    def estimateCableLengthFeet(self, delay):
        return 3.2808 * self.estimateCableLengthMeters(delay)

    def getSampleRateEnum(self):
        return self.sampleRate

    def printCommandList(self, commandList):
        print("")
        for i in range(len(commandList)):
            cmd = commandList[i]
            if cmd < 0 or cmd > 0xffff:
                print("Command[{}] = INVALID COMMAND".format(i))
            elif (cmd & 0xc000) == 0x0000:
                channel = (cmd & 0x3f00) >> 8
                print("Command[{}] = CONVERT({})".format(i, channel))
            elif (cmd & 0xc000) == 0xc000:
                reg = (cmd & 0x3f00) >> 8
                print("Command[{}] = READ({})".format(i, reg))
            elif (cmd & 0xc000) == 0x8000:
                reg = (cmd & 0x3f00) >> 8
                data = (cmd & 0x00ff)
                print("Command[{}] = WRITE({}, NOT IMPLEMENTED YET)".format(i, reg))
            elif cmd == 0x5500:
                print("Command[{}] = CALIBRATE".format(i))
            elif cmd == 0x6a00:
                print("command[{}] = CLEAR".format(i))
            else:
                print("command[{}] = INVALID COMMAND".format(i))
        print("")

    def queueToFile(self, dataQueue, saveOut):
        # dataQueue is queue class, saveOut is binary file open
        count = 0
        while dataQueue.empty() is False:
            sval = dataQueue.get()
            saveOut.write(sval)
            count += 1
        return count

    def getNumEnabledDataStreams(self):
        return self.numDataStreams

    def uploadCommandList(self, commandList, auxCommandSlot, bank):
        if auxCommandSlot != AuxCmd1 and auxCommandSlot != AuxCmd2 and auxCommandSlot != AuxCmd3:
            raise Exception("Error in Rhd2000EvalBoard::uploadCommandList: auxCommandSlot out of range.")
        if bank < 0 or bank > 15:
            raise Exception("Error in Rhd2000EvalBoard::uploadCommandList: bank out of range.")
        for i in range(len(commandList)):
            self.intan.SetWireInValue(WireInCmdRamData, commandList[i])
            self.intan.SetWireInValue(WireInCmdRamAddr, i)
            self.intan.SetWireInValue(WireInCmdRamBank, bank)
            self.intan.UpdateWireIns()
            if auxCommandSlot == AuxCmd1:
                self.intan.ActivateTriggerIn(TrigInRamWrite, 0)
            elif auxCommandSlot == AuxCmd2:
                self.intan.ActivateTriggerIn(TrigInRamWrite, 1)
            elif auxCommandSlot == AuxCmd3:
                self.intan.ActivateTriggerIn(TrigInRamWrite, 2)

    def readDataBlock(self, dataBlock):
        # dataBlock : rhd2000datablock class obj
        numBytesToRead = 2 * dataBlock.calculateDataBlockSizeInWords(self.numDataStreams)
        if numBytesToRead > USB_BUFFER_SIZE:
            raise Exception("Error in Rhd2000EvalBoard::readDataBlock: USB buffer size exceeded.  ")
            return False
        buffer = bytearray("\x00" * numBytesToRead)
        self.intan.ReadFromPipeOut(0xa0, buffer)
        self.usbBuffer = buffer
        dataBlock.fillFromUsbBuffer(self.usbBuffer, 0, self.numDataStreams)
        return True

    def readDataBlocks(self, numBlocks, dataQueue, dataBlock):
        numWordstoRead = numBlocks * dataBlock.calculateDataBlockSizeInWords(self.numDataStreams)
        if self.numWordsInFifo() < numWordstoRead:
            return False
        numBytesToRead = 2 * numWordstoRead
        if numBytesToRead > USB_BUFFER_SIZE:
            raise Exception("Error in Rhd2000EvalBoard::readDataBlocks: USB buffer size exceeded.")
        self.intan.ReadFromPipeOut(PipeOutData, self.usbBuffer)
        dataBlock = Rhd2000DataBlock(self.numDataStreams)
        dataBlockSizeInBytes = 2 * dataBlock.calculateDataBlockSizeInWords(self.numDataStreams)
        sampleSizeInBytes = dataBlockSizeInBytes / SAMPLES_PER_DATA_BLOCK
        index = 0
        for sample in range(int(numBlocks * SAMPLES_PER_DATA_BLOCK)):
            if dataBlock.checkUsbHeader(self.usbBuffer, index) is False:
                if sample > 0:
                    sample = sample - 1
                    index = index - sampleSizeInBytes
                lag = int(sampleSizeInBytes / 2)
                for i in range(1, sampleSizeInBytes / 2):
                    if dataBlock.checkUsbHeader(self.usbBuffer, index + 2*i) is True:
                        lag = i
                self.readAdditionalDataWords(lag, index, numBytesToRead)
            index = index + sampleSizeInBytes
        for i in range(int(numBlocks)):
            dataBlock.fillFromUsbBuffer(self.usbBuffer, i, self.numDataStreams)
            dataQueue.put(dataBlock)
        del dataBlock
        return True

    def readAdditionalDataWords(self, numWords, errorPoint, bufferLength):
        # MAY BE BROKEN. NOT TESTED
        numBytes = 2 * numWords
        for i in range(errorPoint, bufferLength - numBytes, 2):
            self.usbBuffer[i] = self.usbBuffer[i + numBytes]
            self.usbBuffer[i + 1] = self.usbBuffer[i + numBytes + 1]
        while self.numWordsInFifo() < numWords:
            pass
        self.intan.ReadFromPipeOut(PipeOutData, self.usbBuffer[bufferLength - numBytes])

    def getBoardMode(self):
        self.intan.UpdateWireOuts()
        mode = self.intan.GetWireOutValue(WireOutBoardMode)
        print("Board Mode : {}".format(mode))
        return mode

    def getCableDelay(self, port):
        if port == PortA:
            return self.cableDelay[0]
        elif port == PortB:
            return self.cableDelay[1]
        elif port == PortC:
            return self.cableDelay[2]
        elif port == PortD:
            return self.cableDelay[3]
        else:
            raise Exception("Error in RHD2000EvalBoard::getCableDelay: unknown port.")
            return -1

    def getCableDelay(self, delays):
        if len(delays) != 4:
            resizeArray(delays, 4)
        for i in range(4):
            delays[i] = self.cableDelay[i]
        return delays

    def cccc(self, commandList):
        for i in range(len(commandList)):
            cmd = int(commandList[i])
            if cmd < 0 or cmd > 0xffff:
                print("command[{}] = INVALID COMMAND : {}".format(i, cmd))
            elif (cmd & 0xc000) == 0x0000:
                channel = (cmd & 0x3f00) >> 8
                print("command[{}] = CONVERT : {}".format(i, channel))
            elif (cmd & 0xc000) == 0xc000:
                reg = (cmd & 0x3f00) >> 8
                print("command[{}] = READ : {}".format(i, reg))
            elif (cmd & 0xc000) == 0x8000:
                reg = (cmd & 0x3f00) >> 8
                data = (cmd & 0x00ff)
                print("command[{}] = WRITE : {}".format(i, reg))
            elif cmd == 0x5500:
                print("command[{}] = CALIBRATE".format(i))
            elif cmd == 0x6a00:
                print("command[{}] = CLEAR".format(i))
            else:
                print("Invalid Command")

# RHD2000DATABLOCK

SAMPLES_PER_DATA_BLOCK = 60
RHD2000_HEADER_MAGIC_NUMBER = 0xc691199927021942


def resizeArray(array, size):
    length = len(array)
    if length > size:
        del array[size:length]
    elif length == size:
        pass
    elif length < size:
        zeroth = array[0]
        for i in range(size - length):
            array.append(zeroth)


class Rhd2000DataBlock:
    def __init__(self, numDataStreams):
        # Just Defining Data Structures
        self.timeStamp = [0] * SAMPLES_PER_DATA_BLOCK  # Not Sure
        self.amplifierData = [[[0]]]
        self.auxiliaryData = [[[0]]]
        self.boardAdcData = [[0]]
        self.ttlIn = [0]
        self.ttlOut = [0]

        self.allocateIntArray3D(self.amplifierData, numDataStreams, 32, SAMPLES_PER_DATA_BLOCK)
        self.allocateIntArray3D(self.auxiliaryData, numDataStreams, 3, SAMPLES_PER_DATA_BLOCK)
        self.allocateIntArray2D(self.boardAdcData, 8, SAMPLES_PER_DATA_BLOCK)
        self.allocateIntArray1D(self.ttlIn, SAMPLES_PER_DATA_BLOCK)
        self.allocateIntArray1D(self.ttlOut, SAMPLES_PER_DATA_BLOCK)

    def allocateIntArray1D(self, array1D, xSize):
        resizeArray(array1D, xSize)

    def allocateUIntArray1D(self, array1D, xSize):
        resizeArray(array1D, xSize)

    def allocateIntArray2D(self, array2D, xSize, ySize):
        resizeArray(array2D, xSize)
        for i in range(xSize):
            resizeArray(array2D[i], ySize)

    def allocateIntArray3D(self, array3D, xSize, ySize, zSize):
        resizeArray(array3D, xSize)
        for i in range(xSize):
            resizeArray(array3D[i], ySize)
            for j in range(ySize):
                resizeArray(array3D[i][j], zSize)

    def getSamplesPerDataBlock(self):
        return SAMPLES_PER_DATA_BLOCK

    def calculateDataBlockSizeInWords(self, numDataStreams):
        return SAMPLES_PER_DATA_BLOCK * (4 + 2 + numDataStreams * 36 + 8 + 2)

    def checkUsbHeader(self, usbBuffer, index):
        #print('Running checkUsbHeader(rhd2000datablock)')
        x1 = usbBuffer[index]
        x2 = usbBuffer[index + 1]
        x3 = usbBuffer[index + 2]
        x4 = usbBuffer[index + 3]
        x5 = usbBuffer[index + 4]
        x6 = usbBuffer[index + 5]
        x7 = usbBuffer[index + 6]
        x8 = usbBuffer[index + 7]
        header = (x8 << 56) + (x7 << 48) + (x6 << 40) + (x5 << 32) + (x4 << 24) + (x3 << 16) + (x2 << 8) + (x1 << 0)
        #print(header)
        return header == RHD2000_HEADER_MAGIC_NUMBER

    def convertUsbTimeStamp(self, usbBuffer, index):
        x1 = usbBuffer[index]
        x2 = usbBuffer[index + 1]
        x3 = usbBuffer[index + 2]
        x4 = usbBuffer[index + 3]
        return (x4 << 24) + (x3 << 16) + (x2 << 8) + (x1 << 0)

    def convertUsbWord(self, usbBuffer, index):
        x1 = int(usbBuffer[index])
        x2 = int(usbBuffer[index + 1])
        result = (x2 << 8) | (x1 << 0)
        return result

    def fillFromUsbBuffer(self, usbBuffer, blockIndex, numDataStreams):
        index = blockIndex * 2 * self.calculateDataBlockSizeInWords(numDataStreams)
        #print('HEADER : {}'.format(index))
        for t in range(SAMPLES_PER_DATA_BLOCK):
            if self.checkUsbHeader(usbBuffer, index) is False:
                raise Exception("Error in Rhd2000EvalBoard::readDataBlock: Incorrect header.")
            index = index + 8
            #print('TIMESTAMP : {}'.format(index))
            self.timeStamp[t] = self.convertUsbTimeStamp(usbBuffer, index)
            index = index + 4
            #print('Auxiliary Data : {}'.format(index))
            for channel in range(3):
                for stream in range(numDataStreams):
                    self.auxiliaryData[stream][channel][t] = self.convertUsbWord(usbBuffer, index)
                    index = index + 2
            #print('Amp Data : {}'.format(index))
            for channel in range(32):
                for stream in range(numDataStreams):
                    self.amplifierData[stream][channel][t] = self.convertUsbWord(usbBuffer, index)
                    index = index + 2

            index += 2 * numDataStreams

            for i in range(8):
                self.boardAdcData[i][t] = self.convertUsbWord(usbBuffer, index)
                index += 2

            self.ttlIn[t] = self.convertUsbWord(usbBuffer, index)
            index += 2
            self.ttlOut[t] = self.convertUsbWord(usbBuffer, index)
            index += 2

    # THIS PART WAS MODIFIED TO RETURN A VALUE : INCOMPATIBILITY WITH POINTERS
    def writeWordLittleEndian(self, outputStream, dataWord):
        lsb = dataWord & 0x00ff
        msb = (dataWord & 0xff00) >> 8
        outputStream = outputStream << lsb
        outputStream = outputStream << msb
        return outputStream

    # Not really sure about this
    def write(self, saveOut, numDataStreams):
        for t in range(SAMPLES_PER_DATA_BLOCK):
            saveOut = self.writeWordLittleEndian(saveOut, self.timeStamp[t])
            for channel in range(32):
                for stream in range(numDataStreams):
                    saveOut = self.writeWordLittleEndian(saveOut, self.amplifierData[stream][channel][t])
            for channel in range(3):
                for stream in range(numDataStreams):
                    saveOut = self.writeWordLittleEndian(saveOut, self.auxiliaryData[stream][channel][t])
            for i in range(8):
                saveOut = self.writeWordLittleEndian(saveOut, self.boardAdcData[i][t])
            saveOut = self.writeWordLittleEndian(saveOut, self.ttlIn[t])
            saveOut = self.writeWordLittleEndian(saveOut, self.ttlOut[t])
        return saveOut

    # print Replaced by rhdPrint
    def rhdPrint(self, stream):
        RamOffset = 37
        print("")
        print("RHD 2000 Data Block contents:\n  ROM contents:\n    Chip Name: ")
        print(self.auxiliaryData[stream][2][24] + self.auxiliaryData[stream][2][25] + self.auxiliaryData[stream][2][26]
              + self.auxiliaryData[stream][2][27] + self.auxiliaryData[stream][2][28] + self.auxiliaryData[stream][2][
                  29]
              + self.auxiliaryData[stream][2][30] + self.auxiliaryData[stream][2][31])
        print("    Company Name:")
        print(self.auxiliaryData[stream][2][32] + self.auxiliaryData[stream][2][33] + self.auxiliaryData[stream][2][34]
              + self.auxiliaryData[stream][2][35] + self.auxiliaryData[stream][2][36])
        print("    Intan Chip ID: {}".format(self.auxiliaryData[stream][2][19]))
        print("    Number of Amps: {}".format(self.auxiliaryData[stream][2][20]))
        if self.auxiliaryData[stream][2][21] == 0:
            print("bipolar")
        elif self.auxiliaryData[stream][2][21] == 1:
            print("unipolar")
        else:
            print("UNKNOWN")
        #print("    Die Revision: {}".format(self.auxiliaryData[stream[2][22]]))
        print("    Future Expansion Register: {}".format(self.auxiliaryData[stream][2][23]))
        print("  RAM contents:")
        print("    ADC reference BW:      {}".format((self.auxiliaryData[stream][2][RamOffset + 0] & 0xc0) >> 6))
        print("    amp fast settle:       {}".format((self.auxiliaryData[stream][2][RamOffset + 0] & 0x20) >> 5))
        print("    amp Vref enable:       {}".format((self.auxiliaryData[stream][2][RamOffset + 0] & 0x10) >> 4))
        print("    ADC comparator bias:   {}".format((self.auxiliaryData[stream][2][RamOffset + 0] & 0x0c) >> 2))
        print("    ADC comparator select: {}".format((self.auxiliaryData[stream][2][RamOffset + 0] & 0x03) >> 0))
        print("    VDD sense enable:      {}".format((self.auxiliaryData[stream][2][RamOffset + 1] & 0x40) >> 6))
        print("    ADC buffer bias:       {}".format((self.auxiliaryData[stream][2][RamOffset + 1] & 0x3f) >> 0))
        print("    MUX bias:              {}".format((self.auxiliaryData[stream][2][RamOffset + 2] & 0x3f) >> 0))
        print("    MUX load:              {}".format((self.auxiliaryData[stream][2][RamOffset + 3] & 0xe0) >> 5))
        print("    tempS2, tempS1:        {}, {}".format(((self.auxiliaryData[stream][2][RamOffset + 3] & 0x10) >> 4),
                                                         ((self.auxiliaryData[stream][2][RamOffset + 3] & 0x08) >> 3)))
        print("    tempen:                {}".format((self.auxiliaryData[stream][2][RamOffset + 3] & 0x04) >> 2))
        print("    digout HiZ:            {}".format((self.auxiliaryData[stream][2][RamOffset + 3] & 0x02) >> 1))
        print("    digout:                {}".format((self.auxiliaryData[stream][2][RamOffset + 3] & 0x01) >> 0))
        print("    weak MISO:             {}".format((self.auxiliaryData[stream][2][RamOffset + 4] & 0x80) >> 7))
        print("    twoscomp:              {}".format((self.auxiliaryData[stream][2][RamOffset + 4] & 0x40) >> 6))
        print("    absmode:               {}".format((self.auxiliaryData[stream][2][RamOffset + 4] & 0x20) >> 5))
        print("    DSPen:                 {}".format((self.auxiliaryData[stream][2][RamOffset + 4] & 0x10) >> 4))
        print("    DSP cutoff freq:       {}".format((self.auxiliaryData[stream][2][RamOffset + 4] & 0x0f) >> 0))
        print("    Zcheck DAC power:      {}".format((self.auxiliaryData[stream][2][RamOffset + 5] & 0x40) >> 6))
        print("    Zcheck load:           {}".format((self.auxiliaryData[stream][2][RamOffset + 5] & 0x20) >> 5))
        print("    Zcheck scale:          {}".format((self.auxiliaryData[stream][2][RamOffset + 5] & 0x18) >> 3))
        print("    Zcheck conn all:       {}".format((self.auxiliaryData[stream][2][RamOffset + 5] & 0x04) >> 2))
        print("    Zcheck sel pol:        {}".format((self.auxiliaryData[stream][2][RamOffset + 5] & 0x02) >> 1))
        print("    Zcheck en:             {}".format((self.auxiliaryData[stream][2][RamOffset + 5] & 0x01) >> 0))
        print("    Zcheck DAC:            {}".format((self.auxiliaryData[stream][2][RamOffset + 6] & 0xff) >> 0))
        print("    Zcheck select:         {}".format((self.auxiliaryData[stream][2][RamOffset + 7] & 0x3f) >> 0))
        print("    ADC aux1 en:           {}".format((self.auxiliaryData[stream][2][RamOffset + 9] & 0x80) >> 7))
        print("    ADC aux2 en:           {}".format((self.auxiliaryData[stream][2][RamOffset + 11] & 0x80) >> 7))
        print("    ADC aux3 en:           {}".format((self.auxiliaryData[stream][2][RamOffset + 13] & 0x80) >> 7))
        print("    offchip RH1:           {}".format((self.auxiliaryData[stream][2][RamOffset + 8] & 0x80) >> 7))
        print("    offchip RH2:           {}".format((self.auxiliaryData[stream][2][RamOffset + 10] & 0x80) >> 7))
        print("    offchip RL:            {}".format((self.auxiliaryData[stream][2][RamOffset + 12] & 0x80) >> 7))
        rH1Dac1 = self.auxiliaryData[stream][2][RamOffset + 8] & 0x3f
        rH1Dac2 = self.auxiliaryData[stream][2][RamOffset + 9] & 0x1f
        rH2Dac1 = self.auxiliaryData[stream][2][RamOffset + 10] & 0x3f
        rH2Dac2 = self.auxiliaryData[stream][2][RamOffset + 11] & 0x1f
        rLDac1 = self.auxiliaryData[stream][2][RamOffset + 12] & 0x7f
        rLDac2 = self.auxiliaryData[stream][2][RamOffset + 13] & 0x3f
        rLDac3 = self.auxiliaryData[stream][2][RamOffset + 13] & 0x40 >> 6
        rH1 = 2630.0 + rH1Dac2 * 30800.0 + rH1Dac1 * 590.0
        rH2 = 8200.0 + rH2Dac2 * 38400.0 + rH2Dac1 * 730.0
        rL = 3300.0 + rLDac3 * 3000000.0 + rLDac2 * 15400.0 + rLDac1 * 190.0
        # 275 ~ 318 skip
        print("RH1 DAC1, DAC2 : {}, {}, {}".format(rH1Dac1, rH1Dac2, rH1/1000))
        print("RH2 DAC1, DAC2 : {}, {}, {}".format(rH2Dac1, rH2Dac2, rH2 / 1000))
        print("RL DAC1, DAC2, DAC3 : {}, {}, {}".format(rLDac1, rLDac2, rLDac3))
        tempA = self.auxiliaryData[stream][1][12]
        print(tempA)
        tempB = self.auxiliaryData[stream][1][20]
        vddSample = int(self.auxiliaryData[stream][1][28])
        print(tempB)
        print("VDDSAMPLE : {}".format(vddSample))
        tempUnitsC = (tempB - tempA) / 98.9 - 273.15
        tempUnitsF = (9.0 / 5.0) * tempUnitsC + 32.0
        vddSense = 0.0000748 * vddSample
        print("  Temperature sensor (only one reading): {}".format(round(tempUnitsC, 2)))
        print("Supply voltage sensor : {}".format(vddSense))









# RHD2000REGISTERS
import math

# ------------- RHD2000REGISTERS.H
ZcheckCs100fF = 'ZcheckCs100fF'
ZcheckCs1pF = 'ZcheckCs1pF'
ZcheckCs10pF = 'ZcheckCs10pF'

ZcheckPositiveInput = 'ZcheckPositiveInput'
ZcheckNegativeInput = 'ZcheckNegativeInput'

Rhd2000CommandConvert = 'Rhd2000CommandConvert'
Rhd2000CommandCalibrate = 'Rhd2000CommandCalibrate'
Rhd2000CommandCalClear = 'Rhd2000CommandCalClear'
Rhd2000CommandRegWrite = 'Rhd2000CommandRegWrite'
Rhd2000CommandRegRead = 'Rhd2000CommandRegRead'

global MaxCommandLength
MaxCommandLength = 1024


# ------------- RESIZE (REMOVE ON MERGE)
def resizeArray(array, size):
    length = len(array)
    if length > size:
        del array[size:length]
    elif length == size:
        pass
    elif length < size:
        for i in range(size - length):
            array.append(copy.deepcopy(array[0]))


# ------------ RHD2000REGISTERS.CPP
class Rhd2000Registers:
    def __init__(self, sampleRate):
        # Defining Variables
        self.aPwr = [0]
        resizeArray(self.aPwr, 64)
        self.sampleRate = sampleRate
        self.defineSampleRate(self.sampleRate)
        self.adcReferenceBw = 3
        self.setFastSettle(False)
        self.ampVrefEnable = 1
        self.adcComparatorBias = 3
        self.adcComparatorSelect = 2
        self.vddSenseEnable = 1
        self.tempS1 = 0
        self.tempS2 = 0
        self.tempEn = 0
        self.setDigOutHiZ()
        self.weakMiso = 1
        self.twosComp = 0
        self.absMode = 0
        self.enableDsp(True)
        self.setDspCutoffFreq(1.0)
        self.zcheckDacPower = 1
        self.zcheckLoad = 0
        self.setZcheckScale(ZcheckCs100fF)
        self.zcheckConnAll = 0
        self.setZcheckPolarity(ZcheckPositiveInput)
        self.enableZcheck(False)
        self.setZcheckChannel(0)
        self.offChipRH1 = 0
        self.offChipRH2 = 0
        self.offChipRL = 0
        self.adcAux1En = 1
        self.adcAux2En = 1
        self.adcAux3En = 1
        self.setUpperBandwidth(10000.0)
        self.setLowerBandwidth(1.0)
        self.powerUpAllAmps()

    def defineSampleRate(self, newSampleRate):
        self.sampleRate = newSampleRate
        self.muxLoad = 0
        if self.sampleRate < 3334.0:
            self.muxBias = 40
            self.adcBufferBias = 32
        elif self.sampleRate < 4001.0:
            self.muxBias = 40
            self.adcBufferBias = 16
        elif self.sampleRate < 5001.0:
            self.muxBias = 40
            self.adcBufferBias = 8
        elif self.sampleRate < 6251.0:
            self.muxBias = 32
            self.adcBufferBias = 8
        elif self.sampleRate < 8001.0:
            self.muxBias = 26
            self.adcBufferBias = 8
        elif self.sampleRate < 10001.0:
            self.muxBias = 18
            self.adcBufferBias = 4
        elif self.sampleRate < 12501.0:
            self.muxBias = 16
            self.adcBufferBias = 3
        elif self.sampleRate < 15001.0:
            self.muxBias = 7
            self.adcBufferBias = 3
        else:
            self.muxBias = 4
            self.adcBufferBias = 2

    def setFastSettle(self, enabled):
        self.ampFastSettle = 1 if enabled is True else 0

    def setDigOutHiZ(self):
        self.digOut = 0
        self.digOutHiZ = 1

    def enableDsp(self, enabled):
        self.dspEn = 1 if enabled is True else 0

    def setDspCutoffFreq(self, *args):
        if len(args) == 1:
            newDspCutoffFreq = args[0]
            fCutoff = [0.0] * 16
            logFCutoff = [0.0] * 16
            Pi = 2 * math.acos(0.0)
            fCutoff[0] = 0.0
            logNewDspCutoffFreq = math.log10(newDspCutoffFreq)
            for n in range(1, 16):
                x = math.pow(2.0, float(n))
                fCutoff[n] = self.sampleRate * math.log(x / (x - 1.0)) / (2 * Pi)
                logFCutoff[n] = math.log10(fCutoff[n])
            if newDspCutoffFreq > fCutoff[1]:
                self.dspCutoffFreq = 1
            elif newDspCutoffFreq < fCutoff[15]:
                self.dspCutoffFreq = 15
            else:
                minLogDiff = 10000000.0
                for n in range(16):
                    if math.fabs(logNewDspCutoffFreq - logFCutoff[n]) < minLogDiff:
                        minLogDiff = math.fabs(logNewDspCutoffFreq - logFCutoff[n])
                        self.dspCutoffFreq = n
            return fCutoff[self.dspCutoffFreq]
        elif len(args) == 0:
            Pi = 2 * math.acos(0.0)
            x = math.pow(2.0, self.dspCutoffFreq)
            return self.sampleRate * math.log(x / (x - 1.0)) / (2 * Pi)
        else:
            raise Exception("Error in function SetDspCutoffFreq()")

    def setZcheckScale(self, scale):
        # scale is enum(ZcheckCs)
        if scale == ZcheckCs100fF:
            self.zcheckScale = 0x00
        elif scale == ZcheckCs1pF:
            self.zcheckScale = 0x01
        elif scale == ZcheckCs10pF:
            self.zcheckScale = 0x03

    def setZcheckPolarity(self, polarity):
        # polarity is enum(zcheckpolarity)
        if polarity == ZcheckPositiveInput:
            self.zcheckSelPol = 0
        elif polarity == ZcheckNegativeInput:
            self.zcheckSelPol = 1

    def enableZcheck(self, enabled):
        self.zcheckEn = 1 if enabled is True else 0

    def setZcheckChannel(self, channel):
        if channel < 0 or channel > 63:
            return -1
        else:
            self.zcheckSelect = channel
            return self.zcheckSelect

    def setUpperBandwidth(self, upperBandwidth):
        RH1Base = 2200.0
        RH1Dac1Unit = 600.0
        RH1Dac2Unit = 29400.0
        RH1Dac1Steps = 63
        RH1Dac2Steps = 31

        RH2Base = 8700.0
        RH2Dac1Unit = 763.0
        RH2Dac2Unit = 38400.0
        RH2Dac1Steps = 63
        RH2Dac2Steps = 31

        if upperBandwidth > 30000.0:
            upperBandwidth = 30000.0

        rH1Target = self.rH1FromUpperBandwidth(upperBandwidth)
        self.rH1Dac1 = 0
        self.rH1Dac2 = 0
        rH1Actual = RH1Base

        for i in range(RH1Dac2Steps):
            if rH1Actual < rH1Target - (RH1Dac2Unit - RH1Dac2Unit / 2):
                rH1Actual += RH1Dac2Unit
                self.rH1Dac2 += 1
        for i in range(RH1Dac1Steps):
            if rH1Actual < rH1Target - (RH1Dac1Unit / 2):
                rH1Actual += RH1Dac1Unit
                self.rH1Dac1 += 1
        rH2Target = self.rH2FromUpperBandwidth(upperBandwidth)

        self.rH2Dac1 = 0
        self.rH2Dac2 = 0
        rH2Actual = RH2Base

        for i in range(RH2Dac2Steps):
            if rH2Actual < rH2Target - (RH2Dac2Unit - RH2Dac1Unit / 2):
                rH2Actual += RH2Dac2Unit
                self.rH2Dac2 += 1
        for i in range(RH2Dac1Steps):
            if rH2Actual < rH2Target - (RH2Dac1Unit / 2):
                rH2Actual += RH2Dac1Unit
                self.rH2Dac1 += 1

        actualUpperBandwidth1 = self.upperBandwidthFromRH1(rH1Actual)
        actualUpperBandwidth2 = self.upperBandwidthFromRH2(rH2Actual)
        actualUpperBandwidth = math.sqrt(actualUpperBandwidth1 * actualUpperBandwidth2)

        return actualUpperBandwidth

    def rH1FromUpperBandwidth(self, upperBandwidth):
        log10f = math.log10(upperBandwidth)
        return 0.9730 * math.pow(10.0, (8.0968 - 1.1892 * log10f + 0.04767 * log10f * log10f))

    def rH2FromUpperBandwidth(self, upperBandwidth):
        log10f = math.log10(upperBandwidth)
        return 1.0191 * math.pow(10.0, (8.1009 - 1.0821 * log10f + 0.03383 * log10f * log10f))

    def upperBandwidthFromRH1(self, rH1):
        a = 0.04767
        b = -1.1892
        c = 8.0968 - math.log10(rH1 / 0.9730)
        return math.pow(10.0, ((-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)))

    def upperBandwidthFromRH2(self, rH2):
        a = 0.03383
        b = -1.0821
        c = 8.1009 - math.log10(rH2 / 1.0191)
        return math.pow(10.0, ((-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)))

    def setLowerBandwidth(self, lowerBandwidth):
        RLBase = 3500.0
        RLDac1Unit = 175.0
        RLDac2Unit = 12700.0
        RLDac3Unit = 3000000.0
        RLDac1Steps = 127
        RLDac2Steps = 63

        if lowerBandwidth > 1500.0:
            lowerBandwidth = 1500.0
        rLTarget = self.rLFromLowerBandwidth(lowerBandwidth)
        self.rLDac1 = 0
        self.rLDac2 = 0
        self.rLDac3 = 0
        rLActual = RLBase

        if lowerBandwidth < 0.15:
            rLActual += RLDac3Unit
            self.rLDac3 += 1

        for i in range(RLDac2Steps):
            if rLActual < rLTarget - (RLDac2Unit - RLDac1Unit / 2) :
                rLActual += RLDac2Unit
                self.rLDac2 += 1

        for i in range(RLDac1Steps):
            if rLActual < rLTarget - (RLDac1Unit / 2):
                rLActual += RLDac1Unit
                self.rLDac1 += 1

        actualLowerBandwidth = self.lowerBandwidthFromRL(rLActual)

        return actualLowerBandwidth

    def rLFromLowerBandwidth(self, lowerBandwidth):
        log10f = math.log10(lowerBandwidth)
        if lowerBandwidth < 4.0:
            return 1.0061 * math.pow(10.0, (
                    4.9391 - 1.2088 * log10f + 0.5698 * log10f * log10f + 0.1442 * log10f * log10f * log10f))
        else:
            return 1.0061 * math.pow(10.0, (4.7351 - 0.5916 * log10f + 0.08482 * log10f * log10f))

    def lowerBandwidthFromRL(self, rL):
        if rL < 5100.0:
            rL = 5100.0

        if rL < 30000.0:
            a = 0.08482
            b = -0.5916
            c = 4.7351 - math.log10(rL / 1.0061)
        else:
            a = 0.3303
            b = -1.2100
            c = 4.9873 - math.log10(rL / 1.0061)
        return math.pow(10.0, ((-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)))

    def setLowerBandwidth(self, lowerBandwidth):
        RLBase = 3500.0
        RLDac1Unit = 175.0
        RLDac2Unit = 12700.0
        RLDac3Unit = 3000000.0
        RLDac1Steps = 127
        RLDac2Steps = 63

        if lowerBandwidth > 1500.0:
            lowerBandwidth = 1500.0

        rLTarget = self.rLFromLowerBandwidth(lowerBandwidth)

        self.rLDac1 = 0
        self.rLDac2 = 0
        self.rLDac3 = 0
        rLActual = RLBase

        if lowerBandwidth < 0.15:
            rLActual += RLDac3Unit
            self.rLDac3 += 1
        for i in range(RLDac2Steps):
            if rLActual < rLTarget - (RLDac2Unit - RLDac1Unit / 2):
                rLActual += RLDac2Unit
                self.rLDac2 += 1
        for i in range(RLDac1Steps):
            rLActual += RLDac1Unit
            self.rLDac1 += 1
        actualLowerBandwidth = self.lowerBandwidthFromRL(rLActual)

        return actualLowerBandwidth

    def powerUpAllAmps(self):
        for channel in range(64):
            self.aPwr[channel] = 1

    def setDigOutLow(self):
        self.digOut = 0
        self.digOutHiZ = 0

    def setDigOutHigh(self):
        self.digOut = 1
        self.digOutHiZ = 0

    def enableAux1(self, enabled):
        self.adcAux1En = 1 if enabled is True else 0

    def enableAux2(self, enabled):
        self.adcAux2En = 1 if enabled is True else 0

    def enableAux3(self, enabled):
        self.adcAux3En = 1 if enabled is True else 0

    def setZcheckDacPower(self, enabled):
        self.zcheckDacPower = 1 if enabled is True else 0

    def powerDownAllAmps(self):
        for channel in range(64):
            self.aPwr[channel] = 0

    def getRegisterValue(self, reg):
        zcheckDac = 128
        if reg == 0:
            regout = (self.adcReferenceBw << 6) + (self.ampFastSettle << 5) + (self.ampVrefEnable << 4) + (
                    self.adcComparatorBias << 2) + self.adcComparatorSelect
        elif reg == 1:
            regout = (self.vddSenseEnable << 6) + self.adcBufferBias
        elif reg == 2:
            regout = self.muxBias
        elif reg == 3:
            regout = (self.muxLoad << 5) + (self.tempS2 << 4) + (self.tempS1 << 3) + (self.tempEn << 2) + (
                    self.digOutHiZ << 1) + self.digOut
        elif reg == 4:
            regout = (self.weakMiso << 7) + (self.twosComp << 6) + (self.absMode << 5) + (
                    self.dspEn << 4) + self.dspCutoffFreq
        elif reg == 5:
            regout = (self.zcheckDacPower << 6) + (self.zcheckLoad << 5) + (self.zcheckScale << 3) + (
                    self.zcheckConnAll << 2) + (self.zcheckSelPol << 1) + self.zcheckEn
        elif reg == 6:
            regout = zcheckDac
        elif reg == 7:
            regout = self.zcheckSelect
        elif reg == 8:
            regout = (self.offChipRH1 << 7) + self.rH1Dac1
        elif reg == 9:
            regout = (self.adcAux1En << 7) + self.rH1Dac2
        elif reg == 10:
            regout = (self.offChipRH2 << 7) + self.rH2Dac1
        elif reg == 11:
            regout = (self.adcAux2En << 7) + self.rH2Dac2
        elif reg == 12:
            regout = (self.offChipRL << 7) + self.rLDac1
        elif reg == 13:
            regout = (self.adcAux3En << 7) + (self.rLDac3 << 6) + self.rLDac2
        elif reg == 14:
            regout = (self.aPwr[7] << 7) + (self.aPwr[6] << 6) + (self.aPwr[5] << 5) + (self.aPwr[4] << 4) + (
                    self.aPwr[3] << 3) + (self.aPwr[2] << 2) + (self.aPwr[1] << 1) + self.aPwr[0]
        elif reg == 15:
            regout = (self.aPwr[15] << 7) + (self.aPwr[14] << 6) + (self.aPwr[13] << 5) + (self.aPwr[12] << 4) + (
                    self.aPwr[11] << 3) + (self.aPwr[10] << 2) + (self.aPwr[9] << 1) + self.aPwr[0]
        elif reg == 16:
            regout = (self.aPwr[23] << 7) + (self.aPwr[22] << 6) + (self.aPwr[21] << 5) + (self.aPwr[20] << 4) + (
                    self.aPwr[19] << 3) + (self.aPwr[18] << 2) + (self.aPwr[17] << 1) + self.aPwr[16]
        elif reg == 17:
            regout = (self.aPwr[31] << 7) + (self.aPwr[30] << 6) + (self.aPwr[29] << 5) + (self.aPwr[28] << 4) + (
                    self.aPwr[27] << 3) + (self.aPwr[26] << 2) + (self.aPwr[25] << 1) + self.aPwr[24]
        elif reg == 18:
            regout = (self.aPwr[39] << 7) + (self.aPwr[38] << 6) + (self.aPwr[37] << 5) + (self.aPwr[36] << 4) + (
                    self.aPwr[35] << 3) + (self.aPwr[34] << 2) + (self.aPwr[33] << 1) + self.aPwr[32]
        elif reg == 19:
            regout = (self.aPwr[47] << 7) + (self.aPwr[46] << 6) + (self.aPwr[45] << 5) + (self.aPwr[44] << 4) + (
                    self.aPwr[43] << 3) + (self.aPwr[42] << 2) + (self.aPwr[41] << 1) + self.aPwr[40]
        elif reg == 20:
            regout = (self.aPwr[55] << 7) + (self.aPwr[54] << 6) + (self.aPwr[53] << 5) + (self.aPwr[52] << 4) + (
                    self.aPwr[51] << 3) + (self.aPwr[50] << 2) + (self.aPwr[49] << 1) + self.aPwr[48]
        elif reg == 21:
            regout = (self.aPwr[63] << 7) + (self.aPwr[62] << 6) + (self.aPwr[61] << 5) + (self.aPwr[60] << 4) + (
                    self.aPwr[59] << 3) + (self.aPwr[58] << 2) + (self.aPwr[57] << 1) + self.aPwr[56]
        else:
            regout = -1

        return regout

    def createRhd2000Command(self, *args):
        if len(args) == 1:
            commandType = args[0]

            if commandType == Rhd2000CommandCalibrate:
                return 0x5500
            elif commandType == Rhd2000CommandCalClear:
                return 0x6a00
            else:
                raise Exception(
                    "Error in Rhd2000Registers::createRhd2000Command: \nOnly 'Calibrate' or 'Clear Calibration' commands take zero arguments.")
                return -1
        elif len(args) == 2:
            arg1 = args[1]
            commandType = args[0]
            if commandType == Rhd2000CommandConvert:
                if arg1 < 0 or arg1 > 63:
                    raise Exception("Error in Rhd2000Registers::createRhd2000Command: \nChannel number out of range.")
                    return -1
                return 0x0000 + (arg1 << 8)
            elif commandType == Rhd2000CommandRegRead:
                if arg1 < 0 or arg1 > 63:
                    raise Exception("Error in Rhd2000Registers::createRhd2000Command: \nRegister address out of range.")
                    return -1
                return 0xc000 + (arg1 << 8)
            else:
                raise Exception(
                    "Error in Rhd2000Registers::createRhd2000Command: \nOnly 'Convert' and 'Register Read' commands take one argument.")
                return -1
        elif len(args) == 3:
            arg2 = args[2]
            arg1 = args[1]
            commandType = args[0]
            if commandType == Rhd2000CommandRegWrite:
                if arg1 < 0 or arg1 > 63:
                    raise Exception("Error in Rhd2000Registers::createRhd2000Command: \nRegister address out of range.")
                    return -1
                if arg2 < 0 or arg2 > 255:
                    raise Exception("Error in Rhd2000Registers::createRhd2000Command: \nRegister data out of range.")
                    return -1

                return 0x8000 + (arg1 << 8) + arg2
            else:
                raise Exception(
                    "Error in Rhd2000Registers::createRhd2000Command: \nOnly 'Register Write' commands take two arguments.")
                return -1

    def createCommandListRegisterConfig(self, commandList, calibrate):
        # commnadList is a LIST defined on main.py
        del commandList[:]
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 63))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 63))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 0, self.getRegisterValue(0)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 1, self.getRegisterValue(1)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 2, self.getRegisterValue(2)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 4, self.getRegisterValue(4)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 5, self.getRegisterValue(5)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 7, self.getRegisterValue(7)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 8, self.getRegisterValue(8)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 9, self.getRegisterValue(9)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 10, self.getRegisterValue(10)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 11, self.getRegisterValue(11)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 12, self.getRegisterValue(12)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 13, self.getRegisterValue(13)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 14, self.getRegisterValue(14)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 15, self.getRegisterValue(15)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 16, self.getRegisterValue(16)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 17, self.getRegisterValue(17)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 63))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 62))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 61))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 60))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 59))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 48))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 49))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 50))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 51))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 52))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 53))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 54))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 55))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 40))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 41))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 42))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 43))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 44))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 0))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 1))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 2))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 3))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 4))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 5))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 6))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 7))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 8))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 9))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 10))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 11))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 12))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 13))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 14))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 15))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 16))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 17))

        if calibrate is True:
            commandList.append(self.createRhd2000Command(Rhd2000CommandCalibrate))
        else:
            commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 63))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 18, self.getRegisterValue(18)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 19, self.getRegisterValue(19)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 20, self.getRegisterValue(20)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 21, self.getRegisterValue(21)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 63))

        return int(len(commandList))

    def createCommandListTempSensor(self, commandList):
        del commandList[:]
        self.tempEn = 1
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        print('!!!!!')
        print(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        self.tempS1 = self.tempEn
        self.tempS2 = 0
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        self.tempS1 = self.tempEn
        self.tempS2 = self.tempEn
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 49))

        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        self.tempS1 = 0
        self.tempS2 = self.tempEn
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 49))

        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        self.tempS1 = 0
        self.tempS2 = 0
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))

        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
        commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 48))

        for i in range(8):
            commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 32))
            commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 33))
            commandList.append(self.createRhd2000Command(Rhd2000CommandConvert, 34))
            commandList.append(self.createRhd2000Command(Rhd2000CommandRegRead, 63))
        return int(len(commandList))

    def createCommandListUpdateDigOut(self, commandList):
        del commandList[:]
        self.tempEn = 1
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        self.tempS1 = self.tempEn
        self.tempS2 = 0
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        self.tempS1 = self.tempEn
        self.tempS2 = self.tempEn
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        self.tempS1 = 0
        self.tempS2 = self.tempEn
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        self.tempS1 = 0
        self.tempS2 = 0
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
        commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))

        for i in range(8):
            commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
            commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
            commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))
            commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 3, self.getRegisterValue(3)))

        return int(len(commandList))

    def createCommandListZcheckDac(self, commandList, frequency, amplitude):
        Pi = 2 * math.acos(0.0)
        del commandList[:]
        if amplitude < 0.0 or amplitude > 128.0:
            raise Exception("Error in Rhd2000Registers::createCommandListZcheckDac: Amplitude out of range.")
            return -1
        if frequency < 0.0:
            raise Exception("Error in Rhd2000Registers::createCommandListZcheckDac: Negative frequency not allowed.")
            return -1
        elif frequency > self.sampleRate / 4.0:
            raise Exception(
                "Error in Rhd2000Registers::createCommandListZcheckDac: \nFrequency too high relative to sampling rate.")
            return -1
        if frequency == 0.0:
            for i in range(MaxCommandLength):
                commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 6, 128))
        else:
            period = int(math.floor(self.sampleRate / frequency + 0.5))
            if period > MaxCommandLength:
                raise Exception("Error in Rhd2000Registers::createCommandListZcheckDac: Frequency too low.")
                return -1
            else:
                t = 0.0
                for i in range(period):
                    value = int(math.floor(amplitude * math.sin(2 * Pi * frequency * t) + 128.0 + 0.5))
                    if value < 0:
                        value = 0
                    elif value > 255:
                        value = 255
                    commandList.append(self.createRhd2000Command(Rhd2000CommandRegWrite, 6, value))
                    t += 1.0 / self.sampleRate
        return int(len(commandList))
