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
        zeroth = array[0]
        for i in range(size - length):
            array.append(zeroth)


# ------------ RHD2000REGISTERS.CPP
class Rhd2000Registers:
    def __init(self, sampleRate):
        # Defining Variables
        self.aPwr = [None]
        self.sampleRate = sampleRate
        resizeArray(self.aPwr, 64)
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

    def defineSampleRate(self, newSampleRate):
        self.sampleRate = newSampleRate
        muxLoad = 0
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

    def setDspCutoffFreq(self, newDspCutoffFreq):
        fCutoff = [None] * 16
        logFCutoff = [None] * 16
        Pi = 2 * math.acos(0.0)
        fCutoff[0] = 0.0
        logNewDspCutoffFreq = math.log10(newDspCutoffFreq)
        for n in range(16):
            x = math.pow(2.0, float(n))
            fCutoff[n] = self.sampleRate * math.log(x / (x - 1.0)) / (2*Pi)
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

    def setZcheckScale(self, scale):
        # scale is enum(ZcheckCs)
        if scale == ZcheckCs100fF:
            self.zcheckScale = 0x00
        elif scale == ZcheckCs1pF:
            self.zcheckScale = 0x01
        elif scale == ZcheckCs10pF:
            self.zcheckScale = 0x03

    def setZcheckPolarity(self, polarity):
        #polarity is enum(zcheckpolarity)
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

        if upperBandwidth > 30000.0 :
            upperBandwidth = 30000.0

        rH1Target = self.rH1FromUpperBandwidth(upperBandwidth)
        self.rH1Dac1 = 0
        self.rH1Dac2 = 0
        rH1Actual = RH1Base

        for i in range(RH1Dac2Steps) :
            if rH1Actual < rH1Target - (RH1Dac2Unit - RH1Dac2Unit / 2):
                rH1Actual += RH1Dac2Unit
                self.rH1Dac2 += 1
        for i in range(RH1Dac1Steps) :
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