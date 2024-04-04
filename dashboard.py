import dash
from dash import dcc, html, Input, Output
import pandas as pd
import pyarrow.parquet as pq
import plotly.express as px

# Load the df dataset
table = pq.read_table('assets/database.parquet')
# Convert Parquet table to pandas DataFrame
df = table.to_pandas()


# Get the categorical columns
categorical_columns = df.select_dtypes(include=['object']).columns.tolist()

# Get the numeric columns
numeric_columns = df.select_dtypes(include=['float64','int64']).columns.tolist()

# Get operators list for dropdown
operator_counts = df['Operator'].value_counts().sort_values(ascending=False)
operator_counts = operator_counts[operator_counts > 1000] #bc there is not enough data for certain carriers, we only select carriers with data for over 1000 total flights.
operators_list = operator_counts.index.tolist()
#slider=html.Div(className="options_div_1",children=[dcc.Slider(id='year-slider',min=min(df['Incident Year']), max=max(df['Incident Year']),step=1,value=min(df['Incident Year']),marks={year: str(year) for year in range(min(df['Incident Year']), max(df['Incident Year']) + 1)})], style=dict(width="100%"))
slider=html.Div(className="options_div_1",children=[
    html.Div("Select Year:", className="title"), 
    dcc.Slider(id='year-slider', min=min(df['Incident Year']), 
        max=max(df['Incident Year']), step=1, value=min(df['Incident Year']),
        marks={year: str(" ") for year in range(min(df['Incident Year']), max(df['Incident Year']) + 1)},
        tooltip={'always_visible': True})],
        style=dict(width="100%",))
radio=html.Div(className="options_div_2",children=[html.Div("Aircraft Damage:", className="title"), dcc.RadioItems(id='damage-radio', options=["True","False"], value="True", inline=True)])
dropdown=html.Div(className="options_div_3",children=[html.Div("Aircraft Operator:", className="title"), dcc.Dropdown(id='operator-dropdown',options=operators_list, value=df['Operator'][0])], style=dict(width="100%"))

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(className="parent", children=[
    html.Div("Aircraft Wildlife Strikes, 1990-2015", className="dash_title"),
    html.Div(className="options",children=[html.Div([slider,radio,dropdown], className="options_div")]),
    html.Div(className="row1",children=[html.Div(dcc.Graph(id='graph1'), className="row1_graph1"), html.Div(dcc.Graph(id='graph3'), className="row1_graph3")]),
    html.Div(className="row2",children=[html.Div(dcc.Graph(id='graph2'), className="row2_graph2"), html.Div(dcc.Graph(id='graph4'), className="row2_graph4")])
])

graph_color_theme = {
    'plot_bgcolor': '#f0f0f0',  # Set plot background color
    'paper_bgcolor': '#ffffff',  # Set paper background color
    'font_color': '#333333'  # Set font color

}

# Callback for graph 1
# graph1 = id, figure = property
@app.callback(Output("graph1",'figure'),Input('year-slider', 'value')) 
def num_strikes(year):
    year_df = df[df['Incident Year'] == year]
    months = ['Jan','Feb','Mar','Apr','May,','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    wildlife_strikes_count = year_df.groupby('Incident Month').size()
    graph1_df = pd.DataFrame({
        'Incident Month': wildlife_strikes_count.index, 
        'Wildlife Aircraft Strikes': wildlife_strikes_count.values 
    })
    figure = px.line(graph1_df,x='Incident Month',y='Wildlife Aircraft Strikes',title='Number of Strikes per Month',color_discrete_sequence=['#66A5AD'])

    figure.update_xaxes(
        tickvals=graph1_df['Incident Month'],
        ticktext=[str(month) for month in months]
    )
    figure.update_layout(**graph_color_theme)
    return figure


#Callback for graph 3
@app.callback(Output("graph3",'figure'),[Input('year-slider', 'value'),Input('damage-radio', 'value'),Input('operator-dropdown', 'value')]) 
def bird_species(year, damage, operator):

    year_df = df[df['Incident Year'] == year]
    if (damage == "True"):
        damage_bool = 1
    else:
        damage_bool = 0
    damage_df = year_df[year_df['Aircraft Damage'] == damage_bool]
    operator_df = damage_df[damage_df['Operator'] == operator]

    species_count = operator_df.groupby('Species Name').size()
    graph3_df = pd.DataFrame({
        'Species': species_count.index, 
        'Count': species_count.values 
    })
    figure = px.pie(graph3_df,names='Species',values='Count',title='Species of Wildlife',color_discrete_sequence=px.colors.qualitative.Pastel1)
    figure.update_layout(**graph_color_theme)
    return figure

#Callback for graph 2
@app.callback(Output("graph2",'figure'),[Input('year-slider', 'value'),Input('damage-radio', 'value'),Input('operator-dropdown', 'value')]) 
def airplane_part(year, damage, operator):

    year_df = df[df['Incident Year'] == year]
    if (damage == "True"):
        damage_bool = 1
    else:
        damage_bool = 0
    damage_df = year_df[year_df['Aircraft Damage'] == damage_bool]
    operator_df = damage_df[damage_df['Operator'] == operator]

    airplane_parts = ['Radome Strike', 'Windshield Strike', 'Nose Strike', 'Engine1 Strike', 'Engine2 Strike', 'Engine3 Strike', 'Engine4 Strike', 'Engine Ingested', 'Propeller Strike', 'Wing or Rotor Strike', 'Fuselage Strike', 'Landing Gear Strike', 'Tail Strike', 'Lights Strike', 'Other Strike']
    selected_df = operator_df.loc[:, airplane_parts]
    counts = []

    for column in selected_df.columns:
        count = selected_df[column].sum()
        counts.append({'Airplane Part': column, 'Number of Instances': count})

    counts_df = pd.DataFrame(counts)
    graph2_df = counts_df[counts_df['Number of Instances'] != 0]
    figure = px.bar(graph2_df,x='Airplane Part',y='Number of Instances',title='Striked Part of Airplane',color_discrete_sequence=['#66A5AD'])
    figure.update_layout(**graph_color_theme)
    return figure
    
# Callback for graph 4
@app.callback(Output("graph4",'figure'),[Input('year-slider', 'value'),Input('damage-radio', 'value'),Input('operator-dropdown', 'value')]) 
def num_strikes(year, damage, operator):
    year_df = df[df['Incident Year'] == year]
    if (damage == "True"):
        damage_bool = 1
    else:
        damage_bool = 0
    damage_df = year_df[year_df['Aircraft Damage'] == damage_bool]
    operator_df = damage_df[damage_df['Operator'] == operator]

    operator_df = operator_df.copy()
    operator_df['Flight Phase'].fillna('Overall', inplace=True)

    flight_phase_counts = operator_df.groupby('Flight Phase').size()
    graph4_df = pd.DataFrame({
        'Flight Phase': flight_phase_counts.index, 
        'Number of Strikes': flight_phase_counts.values 
    })
    figure = px.bar(graph4_df,x='Flight Phase',y='Number of Strikes',title='Flight Phase Affected',color_discrete_sequence=['#66A5AD'])
    figure.update_layout(**graph_color_theme)
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)
