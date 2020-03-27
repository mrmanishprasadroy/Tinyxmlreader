import xml.etree.ElementTree as ET
import pandas as pd
import re

tree = ET.parse("Telcom_Out.xml")
root = tree.getroot()
tag = root.tag
TlgName = []
elementList = []
tlgDict = {}
MakeTlgDict = {}
tValues = []



# Get the Telegram List
def GetTlgList():
    for c in root.findall('telegram'):
        att = c.attrib
        TlgName.append(att.get('name'))
    return TlgName


def CreateTlgHeader(tlgname):
    Xstring = "./telegram[@name ='" + tlgname + "']/record/element"
    for item in root.findall(Xstring):
        # iterate child elements of item
        att = item.attrib
        count = att.get('count')
        counter = int(count)
        if (counter > 1):
            if (re.search('Time', att.get('name'), re.IGNORECASE)):
                elementList.append(att.get('name'))
            else:
                for idx in range(1, counter + 1):
                    elem = att.get('name') + "_" + str(idx)
                    elementList.append(elem)
        else:
            elementList.append(att.get('name'))
    return elementList

def maketlgvaluelist(sTag):
    regex = 'TYPE;' + sTag +';SENDER;DH_L3_OUT;BODY;'
    with open("L2_L3_TlgSender.log", "r") as file:
        for line in file:
            if re.search(regex, line, re.IGNORECASE) != None:
                cLine = line.replace(regex, '')
                datetime = cLine[:23]
                tlgValues = cLine.replace(cLine[:30], "")
                values = tlgValues.split('|')
                values.insert(0, datetime)
                tlgDict = dict(zip(elementList, values))
                tValues.append(tlgDict)
    file.close()


def maketlgelements(sTag):
    for tag in GetTlgList():
        if (tag == sTag):
            CreateTlgHeader(tag)
            if (elementList.__contains__('Header')):
                elementList.remove('Header')
                elementList.insert(0, 'DateTime')
                elementList.insert(1, 'MessageLength')
                elementList.insert(2, 'MessageId')
                elementList.insert(3, 'MessageCount')
                elementList.insert(4, 'UnitNo')
            else:
                elementList.insert(0, 'DateTime')



if __name__ == "__main__":
    maketlgelements('LF_HEAT_REPORT')
    maketlgvaluelist('LF_HEAT_REPORT')
    df_Heat_status = pd.DataFrame(tValues)
    print(df_Heat_status.head())
