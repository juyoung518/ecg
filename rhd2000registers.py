
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
