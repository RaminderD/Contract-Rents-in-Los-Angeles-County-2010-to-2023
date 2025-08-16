import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import feffery_markdown_components as fmc


import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import json
from copy import deepcopy
import os

# ------------ DATA COLLECTION ------------ #
assets_path = "assets/"

data_path = "masterfiles/"

# Collect and store the mastergeometries into a dictionary whose keys represent years
geometries = [file for file in sorted(os.listdir(assets_path)) if 'contract_rent_mastergeometry' in file]
geometries_dict = dict()
years = range(2010, 2024)
for year in years:
    url_path = f'https://raw.githubusercontent.com/ramindersinghdubb/Contract-Rents-in-LA-County/refs/heads/main/assets/contract_rent_mastergeometry_{year}.json'
    gdf = gpd.read_file(url_path)
    geometries_dict[year] = gdf

# Create a stratified dictionary for mastergeometries, indexed by year and place in that order
stratified_map_dict = dict()
years = list(geometries_dict.keys())
for year in years:
    url_path = f'https://raw.githubusercontent.com/ramindersinghdubb/Contract-Rents-in-LA-County/refs/heads/main/assets/contract_rent_mastergeometry_{year}.json'
    gdf = gpd.read_file(url_path)

    dummy_dict = dict()
    places = gdf['PLACE'].unique().tolist()
    for place in places:
        mask = gdf['PLACE'] == place
        dummy_dict[place] = gdf[mask]

    stratified_map_dict[year] = deepcopy(dummy_dict)

# Collect and store the masterfiles into a dictionary whose keys represent years
files = [file for file in sorted(os.listdir(data_path)) if 'contract_rent_masterfile' in file]
files_dict = dict()
for file in files:
    file_path = data_path + file
    df = pd.read_csv(file_path)
    year = df.at[0, 'YEAR']
    files_dict[year] = df

# Create a stratified dictionary for masterfiles, indexed by year and place in that order
stratified_file_dict = dict()
years = list(files_dict.keys())

for year in years:
    file_path = f'{data_path}contract_rent_masterfile_{year}.csv'
    df = pd.read_csv(file_path)
    
    dummy_dict = dict()
    places = df['PLACE'].unique().tolist()
    for place in places:
        mask = df['PLACE'] == place
        dummy_dict[place] = df[mask]

    stratified_file_dict[year] = deepcopy(dummy_dict)


# ------------ UTILITY FUNCTIONS ------------ #
# Function for collecting all data into a dictionary stratified by Year and Place (in that order)
def place_data(label_ID, path = data_path):
    """
    Collects info on all places across all years by ACS ID into a dictionary.
    You can subset this dictionary as
    dictionary[Year][Place]
    in order to obtain values for a specific place in a specific year.
    """
    place_data_dict = dict()

    files = [file for file in sorted(os.listdir(path)) if label_ID in file]
    years = []
    for file in files:
        date = file.split('_', 3)[-1]
        date = date.split('.csv')[0]
        years.append(int(date))

    for file, year in zip(files, years):
        filepath = path + file
        df = pd.read_csv(filepath)

        placeholder_dict = dict()
        for place in df['PLACE'].unique().tolist():
            mask = df.PLACE == place
            placeholder_dict[place] = df[mask]

        place_data_dict[year] = deepcopy(placeholder_dict)

    return place_data_dict


# Function for creating a dictionary where the years (keys) hold lists of places tabulated for that year
def places_year_dict(label_ID, path = data_path):
    """
    Some places in Los Angeles County don't have any information for certain years.
    Using the cleaned data, we extract the names of places which do have data for a
    given year.
    """
    year_data_dict = dict()

    files = [file for file in sorted(os.listdir(path)) if label_ID in file]
    for file in files:
        file_path = path + file
        df = pd.read_csv(file_path)
        places = df['PLACE'].unique().tolist()
        year = df.at[0, 'YEAR']
        year_data_dict[year] = places

    return year_data_dict

# ------------ CONTAINERS AND STRINGS------------ #

# Container for geospatial choropleth map
geodata_map = html.Div([
    dcc.Graph(
        id = "chloropleth_map",
        config={'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'resetview'],
                'displaylogo': False
               },
    )
])

# Container for rent plot
geodata_plot = html.Div([
    dcc.Graph(
        id = "rent_plot",
        config={'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'resetview'],
                'displaylogo': False
               },
    )
])



# Footer string
footer_string = """
### <b style='color:#800000;'>Information</b>

This interactive website allows you to view the median, 25th percentile, and 75th percentile contract rents for census tracts across various cities in Los Angeles county. <br>

Use the dropdowns to choose a city of interest and a year of interest. <br>

Hover over the map to view information on the median, 25th percentile, and 75th percentile contract rents for census tracts in the selected city during the selected year. <br>

Click on a census tract to visualize changes in its median contract rent over time in the plot. Hover over points in the plot to view additional information on the median, 25th percentile,
and 75th percentile contract rents for the selected census tract.

<hr style="height:2px; border-width:0; color:#212122; background-color:#212122">

### <b style='color:#800000;'>Notes</b>
1. Contract rent, per the <u style='color:#800000;'><a href="https://www2.census.gov/programs-surveys/acs/methodology/design_and_methodology/2024/acs_design_methodology_report_2024.pdf" style="color:#800000;">December 2024 American Community Survey and Puerto Rico Community Survey Design and Methodology</a></u>, is defined as <br>

   <blockquote> <q> ...the monthly rent agreed to or contracted for, regardless of any furnishings, utilities, fees, meals, or services that may be included.</q> (Chapter 6) </blockquote>

   Thus, <ul>
   <li> The <b style='color:#800000;'>median contract rent</b> represents contract rent where 50% of all contract rents in a census tract are lower than this median, </li>
   <li> The <b style='color:#B22222;'>25% percentile contract rent</b> represents contract rent where 25% of all contract rents in a census tract are lower than this 25th percentile</li>
   <li> The <b style='color:#B22222;'>75% percentile contract rent</b> represents contract rent where 75% of all contract rents in a census tract are lower than this 75th percentile</li>
   </ul>

2. Data for contract rents were taken from the United States Census Bureau <u style='color:#800000;'><a href="https://www.census.gov/programs-surveys/acs.html" style="color:#800000;">American Community Survey</a></u> (ACS codes B25057, B25058, and B25059).
3. Redistricting over the years affects the availability of some census tracts in certain cities. Unavailability of data for certain census tracts during select years may affect whether or not census tracts are displayed on the map. For these reasons, some census tracts and their data may only be available for a partial range of years.
4. For data years 2014 and prior, the American Community Survey caps the imputation of contract rents at $2000. For data years 2015 and later, the American Community Survey caps the imputation of contract rents at &#36;3500. As a result, some data on select census tracts may be unavailable in virtue of being higher than those permissible by these thresholds.

### <b style='color:#800000;'>Disclaimer</b>

This tool is developed for illustrative purposes. This tool is constructed with the assistance of the United States Census Bureau’s American Community Survey data.
Survey data is based on individuals’ voluntary participation in questionnaires. The creator is not liable for any missing, inaccurate, or incorrect data. This tool
is not affiliated with, nor endorsed by, the government of the United States.

### <b style='color:#800000;'>Appreciation</b>
Thank you to <u style='color:#800000;'><a href="https://www.wearelbre.org/" style="color:#800000;">Long Beach Residents Empowered (LiBRE)</a></u> for providing the opportunity to work on this project.

### <b style='color:#800000;'>Author Information</b>
Raminder Singh Dubb <br>
GitHub — <u style='color:#800000;'><a href="https://github.com/ramindersinghdubb/Contract-Rents-in-LA-County" style="color:#800000;">https://github.com/ramindersinghdubb/Contract-Rents-in-LA-County</a></u>

© 2025 Raminder Singh Dubb
"""

# ------------ Initialization ------------ #
masterfile_place_year_dict = places_year_dict('contract_rent_masterfile')
masterfile_place_data = place_data('contract_rent_masterfile')

# ------------ Colors ------------ #
Cream_color = '#FAE8E0'
SnowWhite_color = '#F5FEFD'
AlabasterWhite_color = '#FEF9F3'
LightBrown_color = '#F7F2EE'
Rose_color = '#FF7F7F'
MaroonRed_color = '#800000'
SinopiaRed_color = '#C0451C'
Teal_color = '#2A9D8F'
ObsidianBlack_color = '#020403'
CherryRed_color = '#E3242B'


# ------------ APP ------------ #
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])

app.layout = dbc.Container([
    # ------------ Title ------------ #
    html.Div([
        html.B("Rents in Los Angeles County")
    ], style = {'display': 'block',
                'color': MaroonRed_color,
                'margin': '0.2em 0',
                'padding': '0px 0px 0px 0px', # Numbers represent spacing for the top, right, bottom, and left (in that order)
                'font-family': 'Trebuchet MS, sans-serif',
                'font-size': '220.0%'
               }
            ),
    # ------------ Subtitle ------------ #
    html.Div([
        html.P("Median, 25th Percentile, and 75th Percentile Contract Rents for Census Tracts across Cities and Census-Designated Places in Los Angeles County, 2010 to 2023")
    ], style = {'display': 'block',
                'color': ObsidianBlack_color,
                'margin': '-0.5em 0',
                'padding': '0px 0px 0px 0px',
                'font-family': 'Trebuchet MS, sans-serif',
                'font-size': '105.0%'
               }
            ),
    # ------------ Horizontal line rule ------------ #
    html.Div([
        html.Hr()
    ], style = {'display': 'block',
                'height': '1px',
                'border': 0,
                'margin': '-0.9em 0',
                'padding': 0
               }
            ),
    # ------------ Labels for dropdowns (discarded) ------------ #

    # ------------ Dropdowns ------------ #
    html.Div([
        html.Div([
            dcc.Dropdown(id='place-dropdown',
                         placeholder='Select a place',
                         options=[{'label': p, 'value': p} for p in masterfile_place_year_dict[2023]],
                         value='Long Beach',
                         clearable=False
                        )
        ], style = {'display': 'inline-block',
                    'margin': '0 0',
                    'padding': '0px 15px 0px 0px',
                    'width': '22.5%'
                   }
                ),
        html.Div([
            dcc.Dropdown(id='year-dropdown',
                         placeholder='Select a year',
                         clearable=False
                        )
        ], style = {'display': 'inline-block',
                    'margin': '0 0',
                    'padding': '30px 15px 0px 0px',
                    'width': '12.5%',
                   }
                ),
        html.Div([
            dcc.Dropdown(id='census-tract-dropdown',
                         placeholder = 'Click on a census tract in the map',
                         clearable=True
                        )
        ], style = {'display': 'inline-block',
                    'padding': '0px 30px 0px 0px',
                    'margin': '0 0',
                    'width': '30.0%'
                   }
                ),
    ]
            ),
    # ------------ Spatial map with plot ------------ #
    html.Div([
            dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(id = "map-title",
                                   style = {'background-color': MaroonRed_color,
                                            'color': '#FFFFFF'}
                                  ),
                    dbc.CardBody([geodata_map],
                                 style = {'background-color': AlabasterWhite_color}
                                )
                ])
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(id = "plot-title",
                                   style = {'background-color': Teal_color,
                                            'color': '#FFFFFF'}
                                  ),
                    dbc.CardBody([geodata_plot],
                                 style = {'background-color': AlabasterWhite_color}
                                )
                ])
            ])
        ], align='center', justify='center'
               )
    ], style = {
                'padding': '10px 0px 20px 0px',
               }
            ),
    # ------------ Footer ------------ #
    html.Div([
        fmc.FefferyMarkdown(markdownStr    = footer_string,
                            renderHtml     = True,
                            style          = {'background': LightBrown_color,
                                              'margin-top': '1em'
                                             }
                           )
    ]
            )
], style = {'background-color': '#FFFFFF', "padding": "0px 0px 20px 0px",})

# ------------ CALLBACKS ------------ #

# ------------ Dropdowns ------------ #
@app.callback(
    Output('year-dropdown', 'options'),
    [Input('place-dropdown', 'value'),
    ]
)
def set_years_options(selected_place):
    return [{'label': k, 'value': k} for k, v in masterfile_place_year_dict.items() if selected_place in v]

@app.callback(
    Output('year-dropdown', 'value'),
    [Input('year-dropdown', 'options')]
)
def set_year_value(options):
    index = next(index for (index, subdic) in enumerate(options) if subdic['label'] == 2023)
    value_label = options[index]['label']
    return value_label

@app.callback(
    Output('census-tract-dropdown', 'options'),
    [Input('place-dropdown', 'value'),
     Input('year-dropdown', 'value')
    ]
)
def set_tracts_options(selected_place, selected_year):
    df = masterfile_place_data[selected_year][selected_place]
    options = list(df[~df['B25058_001E'].isna()]['NAME'])
    return [{'label': i, 'value': i} for i in options]

@app.callback(
    Output('census-tract-dropdown', 'value'),
    Input('chloropleth_map', 'clickData')
)
def update_census_tract_dropdown(clicked_data):
    if clicked_data:
        selected_tract = clicked_data['points'][0]['customdata'][2]
    return selected_tract


# ------------ Titles ------------ #
@app.callback(
    Output('map-title', 'children'),
    [Input('place-dropdown', 'value'),
    Input('year-dropdown', 'value'),]
)
def set_map_title(selected_place, selected_year):
    if (selected_year == None):
        return [html.B(f"Please select a year to view rents in {selected_place}!")]
    else:
        return [html.B('Median Contract Rents'), ' in ', html.B(f'{selected_place}'), ' by Census Tract, ', html.B(f'{selected_year}')]

@app.callback(
    Output('plot-title', 'children'),
    [Input('place-dropdown', 'value'),
     Input('census-tract-dropdown', 'value')]
)
def set_plot_title(selected_place, selected_tract):
    if (selected_tract == None):
        return [html.B('Please click on a tract.')]
    else:
        return [f' {selected_place}, ', html.B(f'{selected_tract}')]


# ------------ Graphs ------------ #
@app.callback(
    Output('chloropleth_map', 'figure'),
    [Input('place-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('census-tract-dropdown', 'value')
    ]
)
def update_map(selected_place, selected_year, selected_tract):
    fig = rent_chloropleth_map(selected_place, selected_year)

    if selected_tract is not None:
        fig_aux = census_tract_trace(selected_place, selected_year, selected_tract)
        fig.add_trace(fig_aux.data[0])

    return fig

@app.callback(
    Output('rent_plot', 'figure'),
    [Input('place-dropdown', 'value'),
     Input('census-tract-dropdown', 'value')
    ]
)
def update_plot(selected_place, selected_tract):
    if selected_tract is None:
        return None
    else:
        fig = census_tract_plot(selected_place, selected_tract)
        return fig




# ------------ EXECUTE THE APP ------------ #
if __name__ == "__main__":
    app.run(debug=False,


# ------------ EXECUTE THE APP ------------ #
if __name__ == '__main__':
    app.run(debug=False)

#app.css.append_css({"external_url": "https://raw.githubusercontent.com/ramindersinghdubb/Contract-Rents-in-LA-County/refs/heads/main/assets/style.css"})
