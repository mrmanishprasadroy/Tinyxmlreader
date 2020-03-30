import re
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import os


def GetTlgList(root):
    '''
    Extract the Telegrams from the XML file
    :param root: tree.getroot()
    :return: telegram list
    '''
    TlgName = []
    for c in root.findall('telegram'):
        att = c.attrib
        TlgName.append(att.get('name'))
    return TlgName


def CreateTlgHeader(root, tlgname):
    """
    Extract the Record or Element of the telegram from the XML file
    :param root: tree.getroot()
    :param tlgname: telegram name
    :return: telegram element list
    """
    elementList = []
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

    if (elementList.__contains__('Header')):
        elementList.remove('Header')
        elementList.insert(0, 'DateTime')
        elementList.insert(1, 'MessageLength')
        elementList.insert(2, 'MessageId')
        elementList.insert(3, 'MessageCount')
        elementList.insert(4, 'UnitNo')
    else:
        elementList.insert(0, 'DateTime')
    return elementList


def maketlgvaluelist(root, sTag, filename):
    tlgDict = {}
    tValues = []
    elementList = CreateTlgHeader(root, sTag)
    regex = 'TYPE;' + sTag + ';SENDER;DH_L3_OUT;BODY;'
    with open(filename, "r") as file:
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

    if (len(tValues) > 0):
        df = pd.DataFrame(tValues)
        df['DateTime'] = df['DateTime'].astype('datetime64[s]')
        df.set_index(df['DateTime'], inplace=True)
        del df['DateTime']
        return df
    else:
        return 'No Data Found'


def createApp():
    ''' Common Telegram Data Exproler'''
    html_temp = '''
    <div style="background-color:tomato;">
    <p style="color:white;font-size:30px;padding:10px">Common Telegram DataSet Explorer</p>
    <p>Place the Tlg file and xml file at the Data and xml folder respectively  of app to extract data</p>
    </div>
    '''
    st.markdown(html_temp, unsafe_allow_html=True)

    def xml_selector(folder_path='./xml'):
        filenames = os.listdir(folder_path)
        selected_filename = st.sidebar.selectbox("Select xml file", filenames)
        return os.path.join(folder_path, selected_filename)

    filename = xml_selector()
    st.sidebar.info("You Selected {}".format(filename))
    tree = ET.parse(filename)
    root = tree.getroot()

    def file_selector(folder_path='./Data'):
        filenames = os.listdir(folder_path)
        selected_filename = st.sidebar.selectbox("Select log file", filenames)
        return os.path.join(folder_path, selected_filename)

    log_filename = file_selector()
    st.sidebar.info("You Selected {}".format(log_filename))


    telegramName = GetTlgList(root)
    option = st.selectbox(
        'Select the Telegram Name',
        telegramName)

    st.write('You selected: ', option)
    df = maketlgvaluelist(root, option, log_filename)
    st.write(df)


if __name__ == "__main__":
    createApp()
# tree = ET.parse("Telcom_Out.xml")
# root = tree.getroot()

# df = maketlgvaluelist(root, 'LF_HEAT_REPORT')
# print(df)
