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

import os
import re
import xml.etree.ElementTree as ET
from datetime import date
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


class TinyXmlReader:
    """
    Class to decode tlg structure and passing of the log file
    """

    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()

    def __repr__(self):
        return 'TinyXmlReader({self.root!r})'

    def get_tlg_list(self):
        """
        Extract the Telegrams from the XML file
        :return: telegram list
        """
        tlg_name = []
        for c in self.root.findall('telegram'):
            att = c.attrib
            tlg_name.append(att.get('name'))
        return tlg_name

    def CreateTlgHeader(self, tlg_name: str) -> list:
        """
        Extract the Record or Element of the telegram from the XML file
        :param tlg_name: telegram name
        :return: telegram element list
        """
        return_list = []
        element_list = []
        d_type = []
        x_string = "./telegram[@name ='" + tlg_name + "']/record/element"
        for item in self.root.findall(x_string):
            # iterate child elements of item
            data_type = ""
            for dt in item.findall("./primitive"):
                sub_att = dt.attrib
                data_type = sub_att.get('appType')
            att = item.attrib
            count = att.get('count')
            counter = int(count)
            dt = data_type
            if counter > 1:
                if re.search(r'\bTime\b', att.get('name'), re.IGNORECASE):
                    element_list.append(att.get('name'))
                    d_type.append(np.object)

                else:
                    for idx in range(1, counter + 1):
                        elem = att.get('name') + "_" + str(idx)
                        element_list.append(elem)
                        if dt == 'integer':
                            d_type.append('int64')
                        elif dt == 'number':
                            d_type.append('float64')
                        else:
                            d_type.append('object')
            else:
                element_list.append(att.get('name'))
                if dt == 'integer':
                    d_type.append('int64')
                elif dt == 'number':
                    d_type.append('float64')
                else:
                    d_type.append('object')

        if element_list.__contains__('Header'):
            element_list.remove('Header')
            del d_type[0]
            element_list.insert(0, 'DateTime')
            d_type.insert(0, 'datetime64[s]')
            element_list.insert(1, 'MessageLength')
            d_type.insert(1, 'int64')
            element_list.insert(2, 'MessageId')
            d_type.insert(2, 'int64')
            element_list.insert(3, 'MessageCount')
            d_type.insert(3, 'int64')
            element_list.insert(4, 'UnitNo')
            d_type.insert(4, 'int64')
        else:
            element_list.insert(0, 'DateTime')
            d_type.insert(0, 'datetime64[s]')

        return_list.append(element_list)
        return_list.append(d_type)
        return return_list

    def make_tlg_value_list(self, sTag: str, filename: str) -> pd.DataFrame:
        """
        File Processing for extracting the values from Loag file
        :param sTag: Telegram Name
        :param filename: Logfile name for analysis
        :return: Pandas Data frame
        """
        t_values = []
        return_list = self.CreateTlgHeader(sTag)
        element_list = return_list[0]
        d_types = return_list[1]
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
                    tlg_dict = dict(zip(element_list, values))
                    t_values.append(tlg_dict)
            file.close()

        if len(t_values) > 0:
            df = pd.DataFrame(t_values)
            convert_dict = dict(zip(element_list, d_types))
            try:
                df = df.astype(convert_dict)
            except ValueError:
                pass
            return df


def createApp():
    """
        Streamlit App Component start form here
        url: https://docs.streamlit.io/
    """
    html_temp = '''
        <div style="background-color:tomato;">
        <p style="color:white;font-size:30px;padding:10px">Common Telegram DataSet Explorer</p>
        <p>Place the Tlg file and xml file at the Data and xml folder respectively  of app to extract data</p>
        </div>
    '''
    st.markdown(html_temp, unsafe_allow_html=True)
    xml_dir = config.get('PATHS', 'xml_path')

    def xml_selector(folder_path=xml_dir):
        file_name = os.listdir(folder_path)
        selected_filename = st.sidebar.selectbox("Select xml file", file_name)
        return os.path.join(folder_path, selected_filename)

    filename = xml_selector()
    st.sidebar.info("You Selected {}".format(filename))
    reader = TinyXmlReader(filename)
    data_dir = config.get('PATHS', 'data_path')

    def file_selector(folder_path=data_dir):
        filenames = os.listdir(folder_path)
        selected_filename = st.sidebar.selectbox("Select log file", filenames)
        return os.path.join(folder_path, selected_filename)

    log_filename = file_selector()
    st.sidebar.info("You Selected {}".format(log_filename))

    telegramName = reader.get_tlg_list()
    option = st.selectbox(
        'Select the Telegram Name',
        telegramName)

    @st.cache
    def clean_data_source(tag, log_file_name):
        return reader.make_tlg_value_list(tag, log_file_name)

    df = clean_data_source(option, log_filename)
    if isinstance(df, pd.DataFrame):
        st.write(str.format("No of Rows are {} and Coulmns are {}", df.shape[0], df.shape[1]))
        if st.button("Download Excel File"):
            df.to_excel("{}_{}.xlsx".format(option, date.today()))
            st.info("{}_{}.xlsx file saved in root directory of app".format(option, date.today()))
        st.dataframe(df.style.highlight_max(axis=1))
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
        selected_columns_names = st.multiselect(
            "Select Columns To Plot", all_columns_names)
        type_of_plot = "Plotly"
        if st.button("Generate Plot"):
            st.success("Generating Customizable Plot of {} for {}".format(
                type_of_plot, selected_columns_names))
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
                               {'count': 30, 'label': '30M',
                                'step': 'minute', 'stepmode': 'backward'},
                               {'count': 1, 'label': '1H', 'step': 'hour',
                                'stepmode': 'backward'},
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


def debug():
    """
    for Debugging the software
    :return: void
    """
    xml_file = config.get('DEBUG', 'xml_filename')
    log_filename = config.get('DEBUG', 'filename')
    tlg_name = config.get('DEBUG', 'tlg_name')
    reader = TinyXmlReader(xml_file)

    df = reader.make_tlg_value_list(tlg_name, log_filename)
    print(df.info())


if __name__ == "__main__":
    if config['DEFAULT'].getboolean('debug'):
        debug()
    else:
        createApp()
    # debug('Telcom_out.xml', 'LF_HEAT_STATUS', 'L2_L3_TlgSender_20-03-24_110141.log')
