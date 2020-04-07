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
        self.timeStamp = [0]*SAMPLES_PER_DATA_BLOCK  # Not Sure
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
    # def print(self, stream)
    # This part is skipped.
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
