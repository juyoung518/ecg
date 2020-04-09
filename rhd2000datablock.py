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
        print('Running checkUsbHeader(rhd2000datablock)')
        x1 = usbBuffer[index]
        x2 = usbBuffer[index + 1]
        x3 = usbBuffer[index + 2]
        x4 = usbBuffer[index + 3]
        x5 = usbBuffer[index + 4]
        x6 = usbBuffer[index + 5]
        x7 = usbBuffer[index + 6]
        x8 = usbBuffer[index + 7]
        header = (x8 << 56) + (x7 << 48) + (x6 << 40) + (x5 << 32) + (x4 << 24) + (x3 << 16) + (x2 << 8) + (x1 << 0)
        print(header)
        return header == RHD2000_HEADER_MAGIC_NUMBER

    def convertUsbTimeStamp(self, usbBuffer, index):
        x1 = usbBuffer[index]
        x2 = usbBuffer[index + 1]
        x3 = usbBuffer[index + 2]
        x4 = usbBuffer[index + 3]
        return (x4 << 24) + (x3 << 16) + (x2 << 8) + (x1 << 0)

    def convertUsbWord(self, usbBuffer, index):
        x1 = usbBuffer[index]
        x2 = usbBuffer[index + 1]
        result = (x2 << 8) | (x1 << 0)
        return result

    def fillFromUsbBuffer(self, usbBuffer, blockIndex, numDataStreams):
        index = blockIndex * 2 * self.calculateDataBlockSizeInWords(numDataStreams)
        for t in range(SAMPLES_PER_DATA_BLOCK):
            if self.checkUsbHeader(usbBuffer, index) is False:
                raise Exception("Error in Rhd2000EvalBoard::readDataBlock: Incorrect header.")
            index = index + 8
            self.timeStamp[t] = self.convertUsbTimeStamp(usbBuffer, index)
            index = index + 4
            for channel in range(3):
                for stream in range(numDataStreams):
                    self.auxiliaryData[stream][channel][t] = self.convertUsbWord(usbBuffer, index)
                    index = index + 2
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
        print("    Die Revision: {}".format(self.auxiliaryData[stream[2][22]]))
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
        tempA = self.auxiliaryData[stream][1][12]
        tempB = self.auxiliaryData[stream][1][20]
        vddSample = self.auxiliaryData[stream][1][28]
        tempUnitsC = (tempB - tempA) / 98.9 - 273.15
        tempUnitsF = (9.0 / 5.0) * tempUnitsC + 32.0
        vddSense = 0.0000748 * vddSample
        print("  Temperature sensor (only one reading): {}".format(round(tempUnitsC, 2)))