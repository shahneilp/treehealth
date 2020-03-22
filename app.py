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

'''
Neil Shah: Data 608: Module 3

To answer the question about health and stewardship among the census data
I made three tools:

1) A top-down snapshot of the health of all species in a borough
2) A more granular chart on a specifc species health break down
3) A further break down of 2) by stewardship.

'''

'''
This portion is generating the dataframe that
will be manipulated in each plot call
'''


#Generating a Master Database 
boros=['Queens', 'Brooklyn', 'Manhattan', 'Staten Island', 'Bronx']
trees=pd.DataFrame()
for i in boros:
    soql_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=steward,health,spc_common,count(tree_id)' +\
        '&$where=boroname='+repr(str(i.replace(' ', '%20')))+'&$group=steward,health,spc_common')
    dftemp=pd.read_json(soql_url)
    dftemp['Borough']=i
    trees=trees.append(dftemp,ignore_index=True)

#Cleaning up nan
trees.dropna(axis=0,inplace=True)
trees.reset_index(drop=True,inplace=True)
#Cleaning up names
trees.columns=['Count','Steward','Health','Species','Borough']
#Converting None to 0
trees['Steward'].replace('None',value=0,inplace=True)
#Creating dropdowns
boroughchoices=sorted(trees['Borough'].unique())
specieschoices=sorted(trees['Species'].unique())

'''
The Dash portion consists of 2 variables (Species and Borough)
that will be called to the three plots
'''


###Begin Dash
app = dash.Dash()
server = app.server 
app.layout = html.Div([
    html.H1("New York City: Tree Health Tool"),
    
            dcc.Dropdown(
                id="Borough",
                options=[{
                    'label': i,
                    'value': i
                } for i in boroughchoices],
                value='Bronx',
                clearable=False),
            
            dcc.Dropdown(
                id="Species",
                options=[{
                    'label': i,
                    'value': i
                } for i in specieschoices],
                value='American beech',
                clearable=False),
    dcc.Graph(id='healthproportion'),
    dcc.Graph(id='specieshealth'),
    dcc.Graph(id='steward'),
    
    ],
    
           style={'width': '90%',
               'display': 'inline-block'})


# Top down health plot
@app.callback(
    dash.dependencies.Output('healthproportion', 'figure'),
    [dash.dependencies.Input('Borough', 'value')])
def update_graph(Borough):
    #Creating filertered database by Borough
    df_health = trees[trees['Borough'] == Borough].copy()
    #Converts counts to proportion 
    df_health['Count']=round(df_health['Count']/df_health.groupby('Species')['Count'].transform('sum')*100,2)
    pv = pd.pivot_table(
        df_health,
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
            title='{} Top down health proportion for all Tree Species'.format(Borough),
            barmode='stack')
        }

'''
Species Specific plot based on selected Borough/Species
'''
#Species Specific Health Plot
@app.callback(
    dash.dependencies.Output('specieshealth', 'figure'),
    [dash.dependencies.Input('Borough', 'value'),
    Input('Species','value')])

def update_figure2(Borough,Species):
    #Create Filtered Database to plot
    df_spec=trees[trees['Borough']==Borough].copy()
    df_spec=df_spec[df_spec['Species']==Species]
    sg = pd.pivot_table(
    df_spec,
    index=['Health'],
    columns=['Borough'],
    values=['Count'],
    aggfunc=sum,
    fill_value=0)    
    #Create a trace based on the previous pivot-table
    trace = go.Bar(x=sg.index, y=sg[('Count',Borough)], name=Borough)

    return {
        'data': [trace],
        'layout':
        go.Layout(
            title='{} specific health in {}'.format(Species,Borough),
            barmode='stack')
        }

'''
Now utilzing the stewardship call
generating a dataframe/pivot table based once again on Species/Borough
'''

#Stewardship Question
@app.callback(
    dash.dependencies.Output('steward', 'figure'),
    [dash.dependencies.Input('Borough', 'value'),
     Input('Species','value')])
def update_figure3(Borough,Species):
    
    #Create Filtered Database to plot
    df_stew=trees[trees['Borough']==Borough].copy()
    df_stew=df_stew[df_stew['Species']==Species]
    sv = pd.pivot_table(
    df_stew,
    index=['Health'],
    columns=['Steward'],
    values=['Count'],
    aggfunc=sum,
    fill_value=0)    
    #Create traces if there is data available!
    features=[]
    traces=[]
    for i in list(range(0,len(sv.columns))):
        features.append(sv.columns[i])
        
    for i in features:
        traces.append(go.Bar(x=sv.index, y=sv[i], name=i[1]))    
    return {
        'data':traces,
        'layout':
        go.Layout(
            title='Stewardship Impact on  {} in {}'.format(Species,Borough),
            barmode='group')
        }

if __name__ == '__main__':
    app.run_server(debug=True)

