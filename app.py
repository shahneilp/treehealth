# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 09:21:49 2020

@author: Neil
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go

#Building the Health DataFrame

boros=['Queens', 'Brooklyn', 'Manhattan', 'Staten Island', 'Bronx']
#Looping over to make a dataframe

df=pd.DataFrame()
for i in boros:
    soql_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?$select=spc_common,health,count(spc_common)&$where=boroname='+repr(str(i.replace(' ', '%20')))+'&$group=spc_common,health')
    dftemp=pd.read_json(soql_url)
    dftemp['Borough']=i
    df=df.append(dftemp,ignore_index=True)
df.columns=['Borough','Count','Health','Species']
df.dropna(axis=0,inplace=True)
df.reset_index(drop=True,inplace=True)
boroughchoices=df['Borough'].unique()

###Begin Dash
app = dash.Dash()

app.layout = html.Div([
    html.H2("New York City: Tree Health Tool"),
    html.Div(
        [
            dcc.Dropdown(
                id="Borough",
                options=[{
                    'label': i,
                    'value': i
                } for i in boroughchoices],
                value='Manhattan'),
        ],
        style={'width': '25%',
               'display': 'inline-block'}),
    dcc.Graph(id='funnel-graph'),
])


@app.callback(
    dash.dependencies.Output('funnel-graph', 'figure'),
    [dash.dependencies.Input('Borough', 'value')])
def update_graph(Borough):
    #Drop down to select Borough
    df_plot = df[df['Borough'] == Borough]
    #Converts counts to proportion 
    df_plot['Count']=round(df_plot['Count']/df_plot.groupby('Species')['Count'].transform('sum')*100,2)
    pv = pd.pivot_table(
        df_plot,
        index=['Species'],
        columns=['Health'],
        values=['Count'],
        aggfunc=sum,
        fill_value=0)

    trace1 = go.Bar(x=pv.index, y=pv[('Count', 'Good')], name='Good')
    trace2 = go.Bar(x=pv.index, y=pv[('Count', 'Fair')], name='Fair')
    trace3 = go.Bar(x=pv.index, y=pv[('Count', 'Poor')], name='Poor')

    return {
        'data': [trace1, trace2, trace3],
        'layout':
        go.Layout(
            title='Health Proportion for Tree Species in {}'.format(Borough),
            barmode='stack')
        }

if __name__ == '__main__':
    app.run_server(debug=True)

