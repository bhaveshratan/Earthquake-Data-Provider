# importing relevant libraries

from dash import Dash,dcc,Input,Output,html,dash_table
import dash_bootstrap_components as dbc
import snscrape.modules.twitter as sntwitter
import pandas as pd
import dash.exceptions
import plotly.graph_objs as go
import plotly.express as px
import hidden


# creating instance of Dash class
app = Dash(__name__,prevent_initial_callbacks=True,meta_tags=[{'name':'viewport', 'content':'width=device-width'}])
server = app.server
app.title='Earthquake Data'

none_graph = px.scatter(x = [0],y=[0],
                        labels = {'x':'','y':''},
                        title = 'NO DATA (Check whether the dates are in YYYY-MM-DD format and in correct interval)',
                        template='plotly_dark'
                        )


# data soure

link = 'https://twitter.com/NCS_Earthquake?ref_src=twsrc%5Egoogle%7Ctwcamp%5Eserp%7Ctwgr%5Eauthor'
data_source = \
    html.Div([
        html.A('Data Source',href = link, target='_blank',style = {'fontSize':'18px','color':'black',},className='link'),
        ],className='data_link')


# designing the navber
navbar= dbc.NavbarSimple(children = [data_source],
    brand=" Earthquake Data Provider ",
    color="#EE204D",
    dark=False,
    style={'height':'70px','fontWeight':'bold',},
    fluid=False,
    class_name='navbar_top',
    brand_style = {'fontSize': '30px','text-shadow':'0px 0px 0px red, 1px 1px 1px white'}
)

# add a disclaimer

discalimer = html.Sub([
    'This App accesses publicly available Earthquake data provided by National Center of Seismology, Ministry Of Earth Sciences, Govt. Of India. Enter a date on or after 2020-05-27'
],className='disclaimer')


# take to and from dates

in_from = (
    html.Div([
    dbc.Input(id="i_f", placeholder="Example. 2023-01-01", type="text",debounce=True,className='enter_input')
],className='date_input')
)

in_to = (
    html.Div([
    dbc.Input(id = 'i_t',placeholder="Example. 2023-01-31", type="text",debounce=True,className='enter_input'),
],className='date_input')
)

# define the data_table

data_table = html.Div([dash_table.DataTable( id = 'datable_interactive' )],className='table_div')

# layout for input dates

input_boxes = dbc.Container([
    dbc.Row([
        dbc.Col(children = [html.Div(['From Date'],className='date_title'),
                            in_from,
                            ],className='col_input_from'),
        dbc.Col(children = [html.Div(['To Date'],className='date_title'),
                            in_to,
                            ],className='col_input_to'),
    ]),

],className='input_boxes')

# define the slider

slider  = html.Div([
    html.Br(),
    html.H6('Choose range of Magnitude',),
    html.Br(),
    dcc.RangeSlider(id = 'slider_magnitude',
                    value = [1,9],
                    dots = False,
                    max = 9,
                    min = 1,
                    allowCross=True,
                    disabled=False,
                    updatemode='mouseup',
                    included=True,
                    vertical=False,
                    tooltip={'always_visible':False,'placement':'bottom'},
                    className='slider'
                    )
],className='slider_container')

# dcc Graph component for map

only_map = html.Div([

    dcc.Graph(id = 'scatter_mapbox',config={'displayModeBar':'hover'})

],className='map_container')

data_map = dbc.Container([
    html.Div([
        dbc.Row([
            dbc.Col(children=[html.Br(), html.H6('Data'), html.Br(), data_table,html.Br()], className='data_table_col'),
        ]),

    ], className='inside_data_and_map'),

    slider,
    only_map,

], className='data_and_map')


# creating the app layout
app.layout = html.Div([navbar,discalimer,input_boxes,data_map,html.Br(),])


@app.callback(
    Output('datable_interactive', 'data'),
    Output('datable_interactive', 'columns'),
    Output('datable_interactive', 'style_cell_conditional'),
    Output('datable_interactive', 'style_cell'),
    Output('datable_interactive', 'style_data'),
    Output('datable_interactive', 'page_current'),
    Output('datable_interactive', 'page_size'),
    Output('datable_interactive', 'sort_action'),
    Output('datable_interactive', 'sort_mode'),
    Output('datable_interactive', 'editable'),
    Output('datable_interactive', 'filter_action'),
    Output('datable_interactive', 'column_selectable'),
    Output('datable_interactive', 'row_selectable'),
    Output('datable_interactive', 'row_deletable'),
    Output('datable_interactive', 'selected_columns'),
    Output('datable_interactive', 'selected_rows'),
    Output('datable_interactive','style_as_list_view'),
    Output('datable_interactive','style_header'),
    Output('datable_interactive','style_data_conditional'),
    Input('i_f','value'),
    Input('i_t','value'),
    Input('slider_magnitude','value')

)

def update_table(from_date,to_date,s_range):

    if from_date is not None and to_date is not None:

      try :

        # create the tweet data frame

        query = f"(from:NCS_Earthquake) until:{to_date} since:{from_date}"
        tweets = []
        limit = 5000

        for tweet in sntwitter.TwitterSearchScraper(query).get_items():
            if len(tweets) == limit:
                break
            else:
                tweets.append([tweet.rawContent])
        tweet_df = pd.DataFrame(tweets, columns=['Tweet'])

        tweet_df.fillna('NA')

        # remove irrelevant tweets

        c = 0
        for i in tweet_df['Tweet']:

            if i is None or 'Earthquake of Magnitude:' not in i:
                tweet_df.drop(labels=c, axis='rows', inplace=True)

            c += 1
        tweet_df.reset_index(drop=True)

        # split the tweet in relevant columns

        tweet_df[['Magnitude', 'Date', 'Time', 'Lat_Lon', 'Depth(km)', 'Tweet']] = tweet_df['Tweet'].str.split(',', n=5, expand=True)
        tweet_df['Magnitude'] = tweet_df['Magnitude'].str.replace('Earthquake of Magnitude:', '')
        tweet_df['Date'] = tweet_df['Date'].str.replace('Occurred on ', '')
        tweet_df['Depth(km)'] = tweet_df['Depth(km)'].str.replace('Depth:', '')
        tweet_df['Depth(km)'] = tweet_df['Depth(km)'].str.replace(' Km', '')
        tweet_df[['Latitude', 'Lat_Lon']] = tweet_df['Lat_Lon'].str.split(';', n=2, expand=True)
        tweet_df.rename(columns={'Lat_Lon': 'Longitude'}, inplace=True)
        tweet_df['Longitude'] = tweet_df['Longitude'].str.replace('Long: ', '')
        tweet_df['Latitude'] = tweet_df['Latitude'].str.replace('Lat: ', '')
        tweet_df['Latitude'] = tweet_df['Latitude'].str.replace('&amp', '')
        tweet_df['Tweet'] = tweet_df['Tweet'].str.replace('Location: ', '')
        tweet_df.rename(columns={'Tweet': 'Location'}, inplace=True)

        # drop all rows which have none in the data frame after splitting

        tweet_df = tweet_df.mask(tweet_df.eq('None')).dropna()
        tweet_df = tweet_df.reset_index(drop=True)

        # remove irrelevant information from the location column

        location = []
        for i in tweet_df['Location']:
            r = i.split('for', 1)[0]
            location.append(r)
        tweet_df['Location'] = location

        # remove all rows in which the numeric value is not in form of number

        tweet_df['Magnitude'] = pd.to_numeric(tweet_df['Magnitude'], errors='coerce')
        tweet_df['Longitude'] = pd.to_numeric(tweet_df['Longitude'], errors='coerce')
        tweet_df['Latitude'] = pd.to_numeric(tweet_df['Latitude'], errors='coerce')
        tweet_df['Depth(km)'] = pd.to_numeric(tweet_df['Depth(km)'], errors='coerce')
        tweet_df = tweet_df.mask(tweet_df.eq('None')).dropna()
        tweet_df.reset_index(drop=True)

        # rearrange the columns

        tweet_df = tweet_df[['Date', 'Location', 'Magnitude', 'Latitude', 'Longitude', 'Depth(km)']]
        tweet_df.reset_index(drop=True)

        #filter data frame based on range slider values

        min = s_range[0]
        max = s_range[1]

        tweet_filter = tweet_df[(tweet_df['Magnitude'] >= min) & (tweet_df['Magnitude']<=max)]


        # required DataFrame has been formed, now forming the data table

        columns = [{'name': col, 'id': col} for col in tweet_filter.columns]
        earthquake_data = tweet_filter.to_dict(orient='records')
        style_cell_conditional = [{'if': {'column_id': 'Location'}, 'width': '40%'},
                                  {'if': {'column_id': 'Date'}, 'width': '10%'},
                                  {'if': {'column_id': 'Magnitude'}, 'width': '10%'},
                                  {'if': {'column_id': 'Longitude'}, 'width': '10%'},
                                  {'if': {'column_id': 'Latitude'}, 'width': '10%'},
                                  {'if': {'column_id': 'Depth(km)'}, 'width': '10%'},
                                  ]
        style_cell = {'minWidth': 35, 'maxWidth': 35, 'width': 35, "whiteSpace": "pre-line", 'textAlign':'left'}
        style_data = {'whitespace': 'normal', 'height': 'auto', 'max-height': '200px','margin-left' : '5px','color' : '#DODODO','backgroundColor':'#202020','border':'1px solid #DODODO'}
        page_current = 0
        page_size = 10
        sort_action = 'native'
        sort_mode = 'single'
        editable = True
        filter_action = 'native'
        column_selectable = 'multi'
        row_selectable = 'multi'
        row_deletable = True
        selected_columns = []
        selected_rows = []
        style_as_list_view = True
        style_header = {
            'backgroundColor':'#E8E8E8',
            'fontWeight' : 'bold',
            'border' : '1px solid black',
            'color' : 'black'
        }
        style_data_conditional = [{'if': {'row_index':'odd'},'backgroundColor':'#383838'},
                                  {'if':{'column_id':'Magnitude','filter_query':'{Magnitude} > 6'},'backgroundColor':'#DE3163','color':'DODODO'},
                                  {'if': {'column_id': 'Magnitude', 'filter_query': '{Magnitude} > 7'},'backgroundColor': '#ED2939', 'color': 'DODODO'},
                                  {'if': {'column_id': 'Magnitude', 'filter_query': '{Magnitude} > 8'},'backgroundColor': 'red', 'color': 'DODODO'},
                                  {'if': {'column_id': 'Magnitude', 'filter_query': '{Magnitude} < 6'}, 'color': 'DODODO'}
                                    ]



    # return the data table parameters

        return earthquake_data, columns, style_cell_conditional,style_cell,style_data,page_current,page_size,sort_action, \
                sort_mode,editable,filter_action,column_selectable,row_selectable,row_deletable,selected_columns, \
                selected_rows,style_as_list_view,style_header,style_data_conditional

      except ValueError:

          raise dash.exceptions.PreventUpdate



    else :

        raise dash.exceptions.PreventUpdate


@app.callback(

    Output('scatter_mapbox','figure'),
    Input('datable_interactive','derived_virtual_data'),
    Input('datable_interactive','derived_virtual_selected_rows')


)

def update_map(all_rows_data,selected_rows_indices):

 df_map = pd.DataFrame(all_rows_data)



 if 'Magnitude' in df_map:

        c = ['yellow' if i in selected_rows_indices else 'red' for i in range(len(df_map))]

        mapbox = {
            'data':[go.Scattermapbox(
                lon = df_map['Longitude'],
                lat = df_map['Latitude'],
                mode = 'markers',
                marker = go.scattermapbox.Marker(size = ((df_map['Magnitude']))*150,
                                                 colorscale='HSV',
                                                 #color = df_map['Magnitude'],
                                                 color=c,
                                                 showscale=False,
                                                 sizemode='area',
                                                 opacity=0.3,
                                                 ),
                hoverinfo='text',
                hovertext='<b>Location: </b>'+df_map['Location'].astype(str)+'<br>'+
                          '<b>Date: </b>' + df_map['Date'].astype(str) + '<br>' +
                          '<b>Magnitude: </b>' + df_map['Magnitude'].astype(str) + '<br>' +
                          '<b>Depth: </b>' + df_map['Depth(km)'].astype(str) + 'km'+'<br>' +
                          '<b>Latitude: </b>' + df_map['Latitude'].astype(str) + '<br>' +
                          '<b>Longitude: </b>' + df_map['Longitude'].astype(str) + '<br>'

            )],
            'layout': go.Layout(
                uirevision = 'zz',
                hovermode = 'closest',
                hoverdistance=5,
                paper_bgcolor = '#1f2c56',
                plot_bgcolor = '#1f2c56',
                margin = dict(r=0,l=0,b=0,t=0),
                mapbox = dict(
                    accesstoken = hidden.api_key,
                    center = go.layout.mapbox.Center(lat = 28.6139,lon=77.2090),
                    style = 'dark',
                    zoom = 2,
                ),
                autosize = True,
                ),

        }

        return mapbox
 else:
        return none_graph



if __name__ == '__main__':
    app.run_server(debug = True)

