import matplotlib.pyplot as plt
import numpy as np
import os.path as op
import struct

class AnalogInfo:

    def __init__(self, infoStr):
        self.str = infoStr.replace('\n', '')
        buf = self.str.split(',')
        self.an = int(buf[0])
        self.ch_id = buf[1]
        self.ph = buf[2]
        self.ccbm = buf[3]
        self.uu = buf[4]
        self.a = float(buf[5])
        self.b = float(buf[6])
        if not (buf[7]):
            self.skew = 0.0
        else: self.skew = float(buf[7])
        self.min = float(buf[8])
        self.max = float(buf[9])
        self.primary = float(buf[10])
        self.secondary = float(buf[11])
        self.ps = buf[12]
        self._data = []

    def appendData(self, rawValue):
        value = rawValue * self.a + self.b
        self._data.append(value)

    def data(self):
        return np.array(self._data)

    def __repr__(self):
        return self.str
    __str__ = __repr__
        
class DigitalInfo:

    def __init__(self, infoStr):
        self.str = infoStr.replace('\n', '')
        buf = self.str.split(',')
        self.dn = int(buf[0])
        self.ch_id = buf[1]
        self.ph = buf[2]
        self.ccbm = buf[3]
        self.y = int(buf[4])
        self._data = []

    def appendData(self, value):
        if value & (0x0001 << self.dn):
            value = 1
        else:
            value = 0
        self._data.append(value)

    def data(self):
        return np.array(self._data)

    def __repr__(self):
        return self.str
    __str__ = __repr__
        
class FileInfo:

    def __init__(self, infoStr):
        self.str = infoStr.replace('\n', '')
        buf = self.str.split(',')
        self.station_name = buf[0]
        self.rec_dev_id = int(buf[1])
        self.rev_year = buf[2]
        self.str = 'Station name:%s\n' % self.station_name
        self.str += 'ID:%d\n' % self.rec_dev_id
        self.str += 'IEEE Std C37.111-%s COMTRADE' % self.rev_year
    def __repr__(self):
        return self.str
    __str__ = __repr__

class ChannelInfo:

    def __init__(self, infoStr):
        self.str = infoStr.replace('\n', '')
        buf = self.str.split(',')
        self.tt = int(buf[0])
        self.analog = 0
        self.digital = 0
        if 'A' in buf[1]:
            self.analog = int(buf[1].replace('A', ''))
        if 'D' in buf[2]:
            self.digital = int(buf[2].replace('D', ''))
        if self.tt != self.analog + self.digital:
            self.analog = 0
            self.digital = 0
            self.tt = 0
        self.str = 'There is %d channels，including:\n' % self.tt
        self.str += 'analog: %d\n' % self.analog
        self.str += 'digital: %d' % self.digital
    def __repr__(self):
        return self.str
    __str__ = __repr__

class SampleInfo:

    def __init__(self, infoStr):
        self.str = infoStr.replace('\n', '')
        buf = self.str.split(',')
        self.rate = float(buf[0])
        self.end = int(buf[1])
        self.str = 'rate: %.3fHz\n' % self.rate
        self.str += 'id: %d' % self.end
    def __repr__(self):
        return self.str
    __str__ = __repr__
        
class TimeStamp:

    def __init__(self, infoStr):
        self.str = infoStr.replace('\n', '')
        buf = self.str.split(',')
        dateList = buf[0].split('/')
        timeList = buf[1].split(':')
        self.day = int(dateList[0])
        self.month = int(dateList[1])
        self.year = int(dateList[2])
        self.hour = int(timeList[0])
        self.minute = int(timeList[1])
        self.second = float(timeList[2])
    def __repr__(self):
        return self.str
    __str__ = __repr__

class ComtradeConfig:

    def __init__(self, filePath):
        self.path = filePath
        self.result = 'none'
        if not op.exists(self.path):
            self.result = 'no file'
            return
        else:
            self.result = 'parsing'
        f = open(self.path)
        lines = f.readlines()
        f.close()
        del f
        lines = self._removeNextline(lines)
        self._parse(lines)

    def _parse(self, infoStrs):
        index = 0
        self.fileInfo = FileInfo(infoStrs[index])
        index += 1
        self.channelInfo = ChannelInfo(infoStrs[index])
        index += 1
        self.analogInfo = []
        for i in range(0, self.channelInfo.analog):
            self.analogInfo.append(AnalogInfo(infoStrs[index]))
            index += 1
        self.digitalInfo = []
        for i in range(0, self.channelInfo.digital):
            self.digitalInfo.append(DigitalInfo(infoStrs[index]))
            index += 1
        self.frequency = float(infoStrs[index])
        index += 1
        self.nrates = int(infoStrs[index])
        index += 1
        self.sampleInfo = []
        for i in range(0, self.nrates):
            self.sampleInfo.append(SampleInfo(infoStrs[index]))
            index += 1
        self.startTime = TimeStamp(infoStrs[index])
        index += 1
        self.triggerTime = TimeStamp(infoStrs[index])
        index += 1
        self.dataFormat = infoStrs[index].lower()
        index += 1
        self.timemult = float(infoStrs[index])
        self.result = 'parsed'
        print("parsed done")

    def _removeNextline(self, strList):
        result = []
        for each in strList:
            result.append(each.replace('\n', ''))
        return result

class ComtradeData:

    def __init__(self, config):
        self.result = 'none'
        pathList = config.path.split('.')
        self.path = pathList[0] + '.dat'
        print(self.path)
        if config.result != 'parsed':
            print("data not parsed") 
            return
        if not op.exists(self.path):
            self.result = 'no file'
            print("no file")
            return
        else:
            self.result = 'parsing'
        datFile = open(self.path, 'rb')
        data = datFile.read()
        size = datFile.tell()
        datFile.close()
        del datFile
        analogChNum = config.channelInfo.analog
        digitalChNum = config.channelInfo.digital
        analogBytesLen = 2 * analogChNum
        digitalBytesLen = 0
        if digitalChNum % 16 != 0:
            digitalBytesLen =  2 * ((digitalChNum // 16) + 1)
        else:
            digitalBytesLen = 2 * (digitalChNum // 16)
        self.unitSize = 4 + 4 + digitalBytesLen + analogBytesLen
        self.sampleCount = config.sampleInfo[0].end
        self.deltaT = 1.0 / config.sampleInfo[0].rate
        self.config = config
        for i in range(0, self.sampleCount):
            analogIndex = i * self.unitSize + 8
            for ch in range(0, analogChNum):
                index = ch * 2 + analogIndex
                raw = struct.unpack('h', data[index:index+2])[0]
                self.config.analogInfo[ch].appendData(raw)
            digitalIndex = i * self.unitSize + 8 + analogBytesLen
            for ch in range(0, digitalChNum):
                index = (ch // 16) * 2 + digitalIndex
                raw = struct.unpack('h', data[index:index+2])[0] 
                self.config.digitalInfo[ch].appendData(raw)
        self._analog = {}
        self._digital = {}
        for each in self.config.analogInfo:
            self._analog[each.ch_id + '(%s)' % each.uu] = each.data()
        for each in self.config.digitalInfo:
            self._digital[each.ch_id] = each.data()
        self.result = 'parsed'
        print("Done")

    def t(self):
        if self.result == 'parsed':
            return (np.linspace(0.0, self.deltaT * self.sampleCount, self.sampleCount))
        else:
            return np.zeros(0)

    def analog(self):
        if self.result == 'parsed':
            return self._analog
        else:
            return {}
    
    def digital(self):
        if self.result == 'parsed':
            return self._digital
        else:
            return {}

class ComtradeParser:

    def __init__(self, path):
        self.result = 'none'
        if not '.cfg' in path:
            if not '.dat' in path:
                self.result = 'not a comtrade file: %s' % path
                return
            else:
                path = path.replace('.dat', '')
        else:
            path = path.replace('.cfg', '')
        self.path = path
        print(path)
        self.result = 'parsing'
        self.config = ComtradeConfig(self.path + '.cfg')
        self.dat = ComtradeData(self.config)
        self.analog = self.dat.analog()
        self.digital = self.dat.digital()
        self.result = 'parsed'
        self.t = self.dat.t()
        self.fs = self.config.sampleInfo[0].rate

    def _savecsvdata(self, filePath , chtype='analog'):
        chtype = chtype.lower()
        if chtype == 'analog':
            rawdict = self.analog
        elif chtype == 'digital':
            rawdict = self.digital
        else:
            rawdict = dict(self.analog, **self.digital)
        datalist = list(rawdict.values())
        datamatrix = np.array(datalist)
        csvdata = datamatrix.transpose()
        np.savetxt(filePath, csvdata, fmt='%.2f', delimiter=',')
        f = open(filePath, 'r')
        lines = f.readlines()
        f.close()
        tablehead = ','.join(rawdict.keys()) + '\n'
        lines.insert(0, tablehead)
        f = open(filePath, 'w')
        f.writelines(lines)
        f.close()

    def show(self):

        if self.result == 'parsed':
            plt.show()

    def savefig(self, figFormat='pdf'):
 
        if self.result == 'parsed':
            figName = self.path + '_' \
                    + '.' + figFormat
            if figFormat == 'png':
                plt.savefig(figName, dpi=300)
            elif figFormat == 'csv':
                self._savecsvdata(figName, self.plotchannel)
            else:
                plt.savefig(figName)

    def plot(self, chType='analog'):

        if self.result == 'parsed':
            data = {}
            title = ''
            self.plotchannel = chType.upper()
            if chType == 'analog':
                data = self.analog
                temp = self.path.split('/')[-1]
                title = temp + 'digital data'
            elif chType == 'digital':
                data = self.digital
                temp = self.path.split('/')[-1]
                title = temp + 'analog data'
            else:
                data = dict(self.analog, **self.digital)
                temp = self.path.split('/')[-1]
                title = temp + 'all'
            count = len(data)
            row = count // 2 + (count % 2)
            column = 2
            plt.close('all')
            plt.figure(figsize=(16, count*1))
            plt.suptitle(title)
            subplotN = 1
            for key, data in data.items():
                plt.subplot(row, column, subplotN)
                subplotN += 1
                plt.plot(self.t, data, label=key) 
                plt.legend()

if __name__ == "__main__":
    parser = ComtradeParser('/Users/miezai/Desktop/waveClassifier/data/test.cfg')
    parser._savecsvdata('/Users/miezai/Desktop/waveClassifier/data/data.csv')
    parser.plot
    parser.show

