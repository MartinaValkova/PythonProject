import pandas as pd
import matplotlib.pyplot as plt
import datetime



# load the death, confirmed and recovered data to separate dataframes from the url
# https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series

confirmed_df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
recovered_df =  pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')
death_df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')

# Rename column names in all dataframes
confirmed_df.rename(columns={'Province/State':'state', 'Country/Region':'country'}, inplace=True)
recovered_df.rename(columns={'Province/State':'state', 'Country/Region':'country'}, inplace=True)
death_df.rename(columns={'Province/State':'state', 'Country/Region':'country'}, inplace=True)

# Drop unwanted columns
confirmed_df.drop(columns=['state','Lat', 'Long'],inplace=True)
recovered_df.drop(columns=['state','Lat', 'Long'],inplace=True)
death_df.drop(columns=['state','Lat', 'Long'],inplace=True)

# getting the date columns
date_cols = confirmed_df.columns[1:]

# transposing the count of cases , which is stored as columns for each date , to rows. This helps in data visulatization
confirmed_df_new = pd.DataFrame()
recovered_df_new = pd.DataFrame()
death_df_new = pd.DataFrame()

temp_df = pd.DataFrame()

for dt in date_cols:
    cols = list(['country', dt])
    temp_df = confirmed_df[cols].copy()
    temp_df.columns = ['country', 'count']
    temp_df['dates'] = datetime.datetime.strptime(dt, "%m/%d/%y").strftime("%Y/%m/%d")
    confirmed_df_new = confirmed_df_new.append(temp_df, ignore_index=False)

for dt in date_cols:
    cols = list(['country', dt])
    temp_df = recovered_df[cols].copy()
    temp_df.columns = ['country', 'count']
    temp_df['dates'] = datetime.datetime.strptime(dt, "%m/%d/%y").strftime("%Y/%m/%d")
    recovered_df_new = recovered_df_new.append(temp_df, ignore_index=False)

for dt in date_cols:
    cols = list(['country', dt])
    temp_df = death_df[cols].copy()
    temp_df.columns = ['country', 'count']
    temp_df['dates'] = datetime.datetime.strptime(dt, "%m/%d/%y").strftime("%Y/%m/%d")
    death_df_new = death_df_new.append(temp_df, ignore_index=False)

confirmed_df_new.reset_index(drop=True, inplace=True)
recovered_df_new.reset_index(drop=True, inplace=True)
death_df_new.reset_index(drop=True, inplace=True)

# aggregating the data at country-date level
confirmed_df_new = confirmed_df_new.groupby(['country','dates']).sum()
recovered_df_new = recovered_df_new.groupby(['country','dates']).sum()
death_df_new = death_df_new.groupby(['country','dates']).sum()

# resetting the index
confirmed_df_new.reset_index(inplace=True)
recovered_df_new.reset_index(inplace=True)
death_df_new.reset_index(inplace=True)

# Merge the 3 dataframes into a single dataframe
covid_df = pd.merge(pd.merge(confirmed_df_new,recovered_df_new,on=['country','dates']),death_df_new,on=['country','dates'])
covid_df.columns=['country','dates','confirmed','recovered','death']

# Find the active covid cases
covid_df['active'] = covid_df['confirmed'] - covid_df['recovered'] - covid_df['death']

# Calculate case-fatality_ratio ( number of deaths per 100 COVID-19 confirmed cases.)
covid_df['case_fatality_ratio'] = round(covid_df['death']/(covid_df['confirmed']/100))

import dash
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
# from jupyter_dash import JupyterDash

# app = JupyterDash(__name__)
app = dash.Dash(__name__)
server = app.server

colors = {
    'background': '#FFFFFF',
    'text': '#7FDBFF'
}


# Defining App Layout



app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1('COVID - 19 by Martina.V ', style={'textAlign':'center'}),
        html.Div([
            html.Div([
                html.Img(src=app.get_asset_url('IMG_2772.jpg'),
                     id = 'corona-image',
                     style={'height':'60px',
                           'width' : 'auto' ,
                           'margin-bottom': '25px'}),
                     html.Label('Date'),
                       dcc.Dropdown(
                    id='dates_dropdown',
                    options=[{'label': i, 'value': i} for i in covid_df.dates.unique()],
                    value=covid_df.dates.max()
                    )
                ]),
        html.Div([
            html.Label('Interest Variable'),
                dcc.Dropdown(
                    id='interest-variable',
                    options=[{'label': 'Total Active', 'value':'active'},
                        {'label': 'Total Deaths', 'value':'death'},
                        {'label': 'Total Recovered', 'value':'recovered'}],
                    value='active'
                )
            ])
    ], style = {'width':'50%','margin':'auto'}),
    html.Div([
        dcc.Graph(
            id='confirmed_Vs_others',
            ),
        html.Div(
            dcc.Graph(
                id='cases_per_country',
            )
            , style={'width': '90%', 'display': 'inline-block'})
    ], style = {'width':'90%','margin':'auto'})
])

@app.callback(Output('confirmed_Vs_others', 'figure'),
            [Input('dates_dropdown', 'value'),
            Input('interest-variable', 'value')])
def update_scatter(selected_pop, interest_var):
    sorted = covid_df[covid_df.dates == selected_pop]
    fig = px.scatter(sorted,
        x=sorted.confirmed,
        y=sorted[interest_var],
        size='confirmed',
        color='country',
        hover_name='country',
        template='plotly_white',
        labels={'y':interest_var,
                'x': 'confirmed'},
        title='confirmed Vs ' + interest_var)
    fig.update_layout(transition_duration=500)
    return fig

@app.callback(Output('cases_per_country', 'figure'),
              [Input('dates_dropdown', 'value'),
               Input('interest-variable', 'value')])
def update_country_bar(selected_pop, interest_var):
    sorted = covid_df[covid_df.dates == selected_pop]
    fig = px.bar(sorted,
        x='country',
        y=interest_var,
        color='case_fatality_ratio',
        template='plotly_white',
        labels={'country':'Country',
            'confirmed':'Total Confirmed',
            'active':'Total Active',
            'deaths':'Total death',
            'recovered':'Total Recovered'},
            title='Total Cases per Country')

    fig.update_layout()
    return fig


if __name__ == '__main__':
    # app.run_server(mode='inline')
    app.run_server()