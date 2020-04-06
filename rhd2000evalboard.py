# --------- RHD2000EVALBOARD.h

# Imports
import Queue
import ok
from sys import exit
from math import floor

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
SampleRate3333Hz = 10000.0/3.0
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
PortA1, PortB1, PortC1, PortD1 = ['PortA1', 'PortB1', 'PortC1', 'PortD1']
PortA2, PortB2, PortC2, PortD2 = ['PortA2', 'PortB2', 'PortC2', 'PortD2']


# --------- RHDEVALBOARD.CPP

class Rhd2000EvalBoard:
    def __init__(self):
        self.sampleRate = SampleRate30000Hz
        self.numDataStreams = 0
        self.dataStreamEnabled = [0] * MAX_NUM_DATA_STREAMS
        for i in range(MAX_NUM_DATA_STREAMS):
            self.dataStreamEnabled[i] = 0

        self.cableDelay = [-1]*4
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
            print("Device #{} : Opal Kelly {} with Serial No. {}".format(i, productName, self.intan.GetDeviceListSerial(i)))
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
            self.resetBuffer()
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
        return ((value & 0x0002) > 1)

    def isDataClockLocked(self):
        self.intan.UpdateWireOuts()
        value = self.intan.GetWireOutValue(WireOutDataClkLocked)
        return ((value & 0x0001) > 0)

    def initialize(self):
        self.resetBoard()
        self.setSampleRate(SampleRate30000Hz)
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
        self.setContinuousRunMode(True)
        self.setMaxTimeStep(4294967295)  # 4294967295 == (2^32 - 1)
        self.setCableLengthFeet(PortA, 3.0)
        self.setCableLengthFeet(PortB, 3.0)
        self.setCableLengthFeet(PortC, 3.0)
        self.setCableLengthFeet(PortD, 3.0)
        self.setDspSettle(False)
        self.setDataSource(0, PortA1)
        self.setDataSource(1, PortB1)
        self.setDataSource(2, PortC1)
        self.setDataSource(3, PortD1)
        self.setDataSource(4, PortA2)
        self.setDataSource(5, PortB2)
        self.setDataSource(6, PortC2)
        self.setDataSource(7, PortD2)
        self.enableDataStream(0, True)
        for i in range(1, MAX_NUM_DATA_STREAMS):
            self.enableDataStream(i, False)
        self.clearTtlOut()
        self.enableDac(0, False)
        self.enableDac(1, False)
        self.enableDac(2, False)
        self.enableDac(3, False)
        self.enableDac(4, False)
        self.enableDac(5, False)
        self.enableDac(6, False)
        self.enableDac(7, False)
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
        self.intan.SetWireInValue(result_switchauxCommandSlot[0], result_switchauxCommandSlot[1], result_switchauxCommandSlot[2])
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
        if continuousMode == True:
            self.intan.SetWireInValue(WireInResetRun, 0x02, 0x02)
        else:
            self.intan.SetWireInValue(WireInResetRun, 0x00, 0x02)
        self.intan.UpdateWireIns()

    def setMaxTimeStep(self, maxTimeStep):
        maxTimeStepLsb = maxTimeStep & 0x0000ffff
        maxTimeStepMsb = maxTimeStep & 0xffff0000
        self.intan.SetWireInValue(WireInMaxTimeStepLsb, maxTimeStep)
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
        timeDelay = (distance / cableVelocity) + xilinxLvdsOutputDelay + rhd2000Delay + xilinxLvdsInputDelay + misoSettleTime
        delay = floor(((timeDelay / tStep) + 1.0) + 0.5)
        if delay < 1:
            delay = 1
        self.setCableDelay(port, delay)
    def getSampleRate(self):
        print("No need to be implemented")
    def setCableDelay(self, port, delay):
        if delay < 0 or delay > 15:
            raise Exception("Warning in Rhd2000EvalBoard::setCableDelay: delay out of range: {}".format(delay))
        if delay < 0:
            delay = 0
        elif delay > 15:
            delay = 15

        switchPort = {
            PortA: [0,0],
            PortB: [4,1],
            PortC: [8,2],
            PortD: [12,3]
        }
        i, j = switchPort.get(port, "Error!")
        bitShift = i
        self.cableDelay[j] = delay
        self.intan.SetWireInValue(WireInMisoDelay, delay << bitShift, 0x000f << bitShift)
        self.intan.UpdateWireIns()
    def setDspSettle(self, enabled):
        if enabled is True:
            i = 0x04
        else:
            i = 0x00
        self.intan.SetWireInValue(WireInResetRun, i, 0x04)
    def setDataSource(self, stream, dataSource):
        if stream < 0 or stream > 7:
            raise Exception("Error in Rhd2000EvalBoard::setDataSource: stream out of range.")
        if stream < 4:
            endPoint = WireInDataStreamSel1234
            bitShift = int(stream * 4)
        else:
            endPoint = WireInDataStreamSel5678
            bitShift = int((stream - 4) * 4)
        self.intan.SetWireInValue(endPoint, dataSource << bitShift, 0x000f << bitShift)
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

