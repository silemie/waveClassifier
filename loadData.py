import asciiComtrade
import binaryComtrade
import pandas as pd
import os

def loadPath(path):
    os.chdir(path)
    fileChdir = os.getcwd()

    fileList = []
    
    for root, dirs, files in os.walk(fileChdir):
        for file in files:
            if os.path.splitext(file)[1].lower() == '.cfg':
                fileList.append(file)

    data = pd.DataFrame()
    count = 0

    for cfg in fileList:
        print(cfg)
        f = open(cfg, encoding='utf8',errors='ignore')
        lines = f.readlines()
        index = len(lines)
        fileType = lines[index - 2].lower().replace('\n', '')
        f.close()
        del f

        if fileType == "binary":
            parser = binaryComtrade.ComtradeParser(cfg)
        else:
            parser = asciiComtrade.ComtradeParser(cfg)
        d = parser._savecsvdata()
        data = data.append(d)
        count += 1
        print("Successfully load", cfg)
    
    print("Successfully load", count, "files")

    return data

if __name__ == "__main__":
    path = '/Users/miezai/Desktop/异常波形/'
    d = loadPath(path)
    d.to_csv('data.csv')
    


