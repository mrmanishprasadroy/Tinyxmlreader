from xml.dom import minidom

xmldoc = minidom.parse("Telcom_Out.xml")

telegram = xmldoc.getElementsByTagName("telegram")
print(telegram[1].secondChild)
tlgList = []

def getTlgList():
    for tlg in telegram:
        tlgList.append(tlg.attributes['name'].value)
        print(tlg.firstchi)
    return tlgList


def getTlgElement(tlgName):
    pass



if __name__ == "__main__":
    print(getTlgList)
    #tlgName = getTlgList[1]
    #getTlgElement(tlgName)
