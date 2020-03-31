import os
import re
import xml.etree.ElementTree as ET

import pandas as pd
# Data Viz Pkgs
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
    :return: Pandas Dataframe
    """
    tValues = []
    elementList = CreateTlgHeader(root, sTag)
    regex = 'TYPE;' + sTag + ';'
    with open(filename, "r") as file:
        for line in file:
            if re.search(regex, line, re.IGNORECASE) is not None:
                cLine = line.replace(regex, '')
                datetime = cLine[:23]
                #sub_index = line.rfind('BODY;')
                tlgValues = cLine.replace(cLine[:30], "")
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
        type_of_plot = st.selectbox("Select Type of Plot", ["area", "bar", "line"])
        selected_columns_names = st.multiselect("Select Columns To Plot", all_columns_names)

        if st.button("Generate Plot"):
            st.success("Generating Customizable Plot of {} for {}".format(type_of_plot, selected_columns_names))

            # using Plot's graphs
            if type_of_plot == 'area':
                res = []
                for col in selected_columns_names:
                    res.append(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df[col].values.tolist(),
                            name=col
                        )
                    )

                fig = go.Figure(data=res)
                st.plotly_chart(fig, use_container_width=True)

            elif type_of_plot == 'bar':
                res = []
                for col in selected_columns_names:
                    res.append(
                        go.Bar(
                            x=df.index.values.tolist(),
                            y=df[col].values.tolist(),
                            name=col
                        )
                    )

                layout = go.Layout(
                    barmode='group'
                )

                fig = go.Figure(data=res, layout=layout)
                st.plotly_chart(fig, use_container_width=True)

            elif type_of_plot == 'line':
                trace0 = []
                for item in selected_columns_names:
                    # Create and style traces
                    trace0.append(go.Scatter(
                        x=df['DateTime'],
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


if __name__ == "__main__":
    createApp()
# tree = ET.parse("Telcom_Out.xml")
# root = tree.getroot()

# df = maketlgvaluelist(root, 'LF_HEAT_REPORT')
# print(df)
