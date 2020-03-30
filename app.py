import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import json
import dash_table as dt
import plotly.graph_objs as go
import flask
import io
from flask import send_file

from TLGDefinitionReader import *
sTag = 'LF_HEAT_STATUS'
df = maketlgvaluelist(sTag)
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True , dark=True, responsive=True,)


items = [table]

def serveLayout():

   return  html.Div([

       html.Div(dbc.Alert(str.format('Data Table for {0}', sTag), color="primary"),),
       #html.Div(items),

       html.Div(dbc.Row(dbc.Col(html.Div(
           dt.DataTable(
               id='table',
               columns=[{"name": i, "id": i, "selectable": True} for i in df.columns],
               data=df.to_dict('records'),
               filter_action="native",
               sort_action="native",
               sort_mode="multi", )

       ))), ),

   ] )



app.layout = serveLayout()

if __name__ == "__main__":
    app.run_server(debug=True)