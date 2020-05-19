import configparser
from datetime import date
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import base64
from log_parser import TinyXmlReader

config = configparser.ConfigParser()
config.read('config.ini')
global log_bytes


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
    uploaded_xml_file = st.sidebar.file_uploader("Choose a Valid Telcom XMl file", type="xml")
    if uploaded_xml_file is not None:
        reader = TinyXmlReader(uploaded_xml_file)
        telegramName = reader.get_tlg_list()
        option = st.selectbox('Select the Telegram Name', telegramName)

    uploaded_log_file = st.sidebar.file_uploader("Choose a Valid Log file", type="log")
    if uploaded_log_file is not None:
        log_bytes = uploaded_log_file.read()

    if uploaded_xml_file is not None and uploaded_log_file is not None:
        @st.cache
        def clean_data_source(tag, log_file_name):
            return reader.make_tlg_value_list(tag, log_file_name)

        df = clean_data_source(option, log_bytes)
        if isinstance(df, pd.DataFrame):
            st.write(str.format("No of Rows are {} and Columns are {}", df.shape[0], df.shape[1]))
            # When no file name is given, pandas returns the CSV as a string, nice.
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
            filename = "{}_{}".format(option, date.today())
            href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)

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
