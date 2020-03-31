#
# TlgDefinitinReader
# $Id: TLGDefinitionReader.py  2020-03-31 ROYM $
# use of streamlit app
# use of ElementTree
# use of Plotly
# history:
# 2020-03-31 vl   created
#
# manish.roy@sms-group.com
#
# --------------------------------------------------------------------
"""
Copyright (c) 2020 manish.roy@sms-group.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import os
import re
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def GetTlgList(root):
    """
    Extract the Telegrams from the XML file
    :param root: tree.getroot()
    :return: telegram list
    """
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
        if counter > 1:
            if re.search(r'\bTime\b', att.get('name'), re.IGNORECASE):
                elementList.append(att.get('name'))
            else:
                for idx in range(1, counter + 1):
                    elem = att.get('name') + "_" + str(idx)
                    elementList.append(elem)
        else:
            elementList.append(att.get('name'))

    if elementList.__contains__('Header'):
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
    """
    File Processing for extracting the values from Loag file
    :param root: tree.getroot(
    :param sTag: Telegram Name
    :param filename: Logfile name for analysis
    :return: Pandas Data frame
    """
    tValues = []
    elementList = CreateTlgHeader(root, sTag)
    regex = 'TYPE;' + sTag + ';'
    with open(filename, "r") as file:
        for line in file:
            if re.search(regex, line, re.IGNORECASE) is not None:
                cLine = line.replace(regex, '')
                datetime = cLine[:23]
                sub_index = cLine.find('BODY')
                tlgValues = cLine.replace(cLine[:sub_index + 5], "")
                values = tlgValues.split('|')
                values.insert(0, datetime)
                tlgDict = dict(zip(elementList, values))
                tValues.append(tlgDict)
        file.close()

    if len(tValues) > 0:
        df = pd.DataFrame(tValues)
        return df
    else:
        return 'No Data Found'


def createApp():
    """
        Streamlit App componet start form here
        url: https://docs.streamlit.io/
    """
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

    df = maketlgvaluelist(root, option, log_filename)
    if not type(df) is str:
        st.dataframe(df.style.highlight_max(axis=0))
        # Select Columns
        if st.checkbox("Select Columns To Show"):
            all_columns = df.columns.tolist()
            selected_columns = st.multiselect("Select", all_columns)
            new_df = df[selected_columns]
            st.dataframe(new_df.style.highlight_max(axis=0))

        # Build Panda Query string
        if st.checkbox("Search Dataset"):
            hint = '''
                    <p>Query Pandas DataFrame with Condition on Single Column line >, < , for equal use == 
                        Query Pandas DataFrame with Condition on Multiple Columns using AND operator
                        Query Pandas DataFrame with Condition on Multiple Columns using OR operator</p>
            '''
            st.markdown(hint, unsafe_allow_html=True)
            query = st.text_input('Write query in String style', value="")
            if len(query) > 0:
                new_df = df.query(query)
                st.write(new_df)
        # Data Visualization for the datafile
        st.subheader("Data Visualization")

        # Customizable Plot

        st.subheader("Customizable Plot")
        all_columns_names = df.columns.tolist()
        type_of_plot = st.selectbox("Select Type of Plot", ["MatPlot", "Plotly"])
        selected_columns_names = st.multiselect("Select Columns To Plot", all_columns_names)

        if st.button("Generate Plot"):
            st.success("Generating Customizable Plot of {} for {}".format(type_of_plot, selected_columns_names))
            if type_of_plot == 'MatPlot':
                # create plot
                fig, ax = plt.subplots()
                bar_width = 0.35
                opacity = 0.8
                for col in selected_columns_names:
                    plt.plot(df.index.values.tolist(), df[col].to_list(), bar_width,
                             alpha=opacity,
                             label=col)

                plt.xlabel('Index')
                plt.legend()

                plt.tight_layout()
                st.pyplot()

            elif type_of_plot == 'Plotly':
                trace0 = []
                for item in selected_columns_names:
                    # Create and style traces
                    trace0.append(go.Scatter(
                        x=df.index.values.tolist(),
                        y=df[item],
                        name=item,
                        text=df[item],
                        line=dict(
                            # color=('rgb(205, 12, 24)'),
                            dash='solid',
                            width=2)
                    ))
                traces = [trace0]
                data = [val for sublist in traces for val in sublist]

                layout = go.Layout(
                    xaxis=dict(

                        zeroline=True,
                        showline=True,
                        mirror='ticks',
                        gridcolor='#bdbdbd',
                        gridwidth=2,
                        zerolinecolor='#969696',
                        zerolinewidth=4,
                        linecolor='#636363',
                        linewidth=6
                    ),
                    yaxis=dict(

                        zeroline=True,
                        showline=True,
                        mirror='ticks',
                        gridcolor='#bdbdbd',
                        gridwidth=2,
                        zerolinecolor='#969696',
                        zerolinewidth=4,
                        linecolor='#636363',
                        linewidth=6
                    )
                )

                # Plot and embed
                fig = dict(data=data, layout=layout)
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.write(df)


def debug():
    """
    for Debugging the software
    :return: void
    """
    tree = ET.parse("Telcom_In.xml")
    root = tree.getroot()

    df = maketlgvaluelist(root, 'SCL205', 'SCL1_TlgReceiver.log')
    print(df)


if __name__ == "__main__":
    createApp()
