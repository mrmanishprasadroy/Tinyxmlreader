#
# TlgDefinitinReader
# $Id: TLGDefinitionReader.py  2020-03-31 ROYM $
# use of streamlit app
# use of ElementTree
# use of Plotly
# history:
# 2020-03-31 vl   created
# 2020-04-02 V1.0.01 Added Data type for the Data frame
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
import numpy as np


class Tinyxmlreader:
    """
    Class to decode tlg structure and passing of the log file
    """

    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()

    def __repr__(self):
        return f'Tinyxmlreader({self.root!r})'

    def GetTlgList(self):
        """
        Extract the Telegrams from the XML file
        :return: telegram list
        """
        TlgName = []
        for c in self.root.findall('telegram'):
            att = c.attrib
            TlgName.append(att.get('name'))
        return TlgName

    def CreateTlgHeader(self, tlgname):
        """
        Extract the Record or Element of the telegram from the XML file
        :param tlgname: telegram name
        :return: telegram element list
        """
        returnList = []
        elementList = []
        dtype = []
        Xstring = "./telegram[@name ='" + tlgname + "']/record/element"
        for item in self.root.findall(Xstring):
            # iterate child elements of item
            datatype = ""
            for dt in item.findall("./primitive"):
                satt = dt.attrib
                datatype = satt.get('appType')
            att = item.attrib
            count = att.get('count')
            counter = int(count)
            dt = datatype
            if counter > 1:
                if re.search(r'\bTime\b', att.get('name'), re.IGNORECASE):
                    elementList.append(att.get('name'))
                    dtype.append(np.object)

                else:
                    for idx in range(1, counter + 1):
                        elem = att.get('name') + "_" + str(idx)
                        elementList.append(elem)
                        if dt == 'integer':
                            dtype.append('int64')
                        elif dt == 'number':
                            dtype.append('float64')
                        else:
                            dtype.append('object')
            else:
                elementList.append(att.get('name'))
                if dt == 'integer':
                    dtype.append('int64')
                elif dt == 'number':
                    dtype.append('float64')
                else:
                    dtype.append('object')

        if elementList.__contains__('Header'):
            elementList.remove('Header')
            del dtype[0]
            elementList.insert(0, 'DateTime')
            dtype.insert(0, 'datetime64[s]')
            elementList.insert(1, 'MessageLength')
            dtype.insert(1, 'int64')
            elementList.insert(2, 'MessageId')
            dtype.insert(2, 'int64')
            elementList.insert(3, 'MessageCount')
            dtype.insert(3, 'int64')
            elementList.insert(4, 'UnitNo')
            dtype.insert(4, 'int64')
        else:
            elementList.insert(0, 'DateTime')
            dtype.insert(0, 'datetime64[s]')

        returnList.append(elementList)
        returnList.append(dtype)
        return returnList

    def maketlgvaluelist(self, sTag, filename):
        """
        File Processing for extracting the values from Loag file
        :param sTag: Telegram Name
        :param filename: Logfile name for analysis
        :return: Pandas Data frame
        """
        tValues = []
        returnList = self.CreateTlgHeader(sTag)
        elementList = returnList[0]
        dtypes = returnList[1]
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
            convert_dict = dict(zip(elementList, dtypes))
            try:
                df = df.astype(convert_dict)
            except ValueError:
                # print(ValueError)
                pass
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
    reader = Tinyxmlreader(filename)

    def file_selector(folder_path='./Data'):
        filenames = os.listdir(folder_path)
        selected_filename = st.sidebar.selectbox("Select log file", filenames)
        return os.path.join(folder_path, selected_filename)

    log_filename = file_selector()
    st.sidebar.info("You Selected {}".format(log_filename))

    telegramName = reader.GetTlgList()
    option = st.selectbox(
        'Select the Telegram Name',
        telegramName)

    @st.cache
    def clean_data_source(option, log_filename):
        return reader.maketlgvaluelist(option, log_filename)

    df = clean_data_source(option, log_filename)
    if not type(df) is str:
        st.write(str.format("No of Rows are {} and Coulmns are {}", df.shape[0], df.shape[1]))
        if st.button("Download Excel File"):
            df.to_excel("output.xlsx")
            st.info("output.xlsx file saved in root directory of app")
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
            try:
                if len(query) > 0:
                    new_df = df.query(query)
                    st.write(new_df)
            except ValueError:
                st.error('failed to querry the dataset, check query condition ')
        # Data Visualization for the datafile
        st.subheader("Data Visualization")

        # Customizable Plot

        st.subheader("Customizable Plot")
        all_columns_names = df.columns.tolist()
        # type_of_plot = st.selectbox("Select Type of Plot", ["MatPlot", "Plotly"])
        selected_columns_names = st.multiselect("Select Columns To Plot", all_columns_names)
        type_of_plot = "Plotly"
        if st.button("Generate Plot"):
            st.success("Generating Customizable Plot of {} for {}".format(type_of_plot, selected_columns_names))
            if type_of_plot == 'MatPlot':
                # create plot
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
                        x=df['DateTime'].to_list(),
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
                    xaxis={"title": "Date Time",
                           'rangeselector': {'buttons': list([
                               {'count': 30, 'label': '30M', 'step': 'minute', 'stepmode': 'backward'},
                               {'count': 1, 'label': '1H', 'step': 'hour', 'stepmode': 'backward'},
                               {'step': 'all'}
                           ])}, 'rangeslider': {'visible': True}, 'type': 'date'},
                    margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                    legend={'x': 0, 'y': 1},
                    hovermode='closest'

                )

                # Plot and embed
                fig = dict(data=data, layout=layout)
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.write(df)


def debug(xmlfilename, tlgname, logfilename):
    """
    for Debugging the software
    :return: void
    """
    reader = Tinyxmlreader(xmlfilename)

    df = reader.maketlgvaluelist(tlgname, logfilename)
    print(df.info())


if __name__ == "__main__":
    createApp()
    # debug('Telcom_out.xml', 'LF_HEAT_STATUS', 'L2_L3_TlgSender_20-03-24_110141.log')
