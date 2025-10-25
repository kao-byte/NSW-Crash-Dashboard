from dash import Dash, dcc, html, Input, Output # type: ignore
from flask import send_from_directory
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore
from plotly.subplots import make_subplots # type: ignore
import pandas as pd # type: ignore

transport_nsw_df = pd.read_csv('transport_nsw.csv')

# Ensure numeric lat/lon and drop rows with missing coordinates
transport_nsw_df['latitude'] = pd.to_numeric(transport_nsw_df['latitude'], errors='coerce')
transport_nsw_df['longitude'] = pd.to_numeric(transport_nsw_df['longitude'], errors='coerce')
transport_nsw_df['no_total_injured'] = transport_nsw_df['no_seriously_injured'] + transport_nsw_df['no_moderately_injured'] + transport_nsw_df['no_minor_other_injured']
transport_nsw_df = transport_nsw_df.dropna(subset=['latitude', 'longitude'])

app = Dash(__name__, title='NSW Road Crash Dashboard')
app._favicon = 'favicon.ico'

# Build selector options
weather_values = sorted([str(w) for w in transport_nsw_df['weather'].dropna().unique()])
weather_options = [{'label': 'All', 'value': 'All'}] + [{'label': w, 'value': w} for w in weather_values]
surface_condition_values = sorted([str(r) for r in transport_nsw_df['surface_condition'].dropna().unique()])
surface_condition_options = [{'label': 'All', 'value': 'All'}] + [{'label': r, 'value': r} for r in surface_condition_values]
lga_values = sorted([str(l) for l in transport_nsw_df['lga'].dropna().unique()])
lga_options = [{'label': 'All', 'value': 'All'}] + [{'label': l, 'value': l} for l in lga_values]

app.layout = html.Div([
    # Top banner: logo on the left, title on the right
    html.Div([
        html.A(
            html.Img(
                src='/assets/nsw.svg',
                style={'height': '70px', 'display': 'block','marginRight': '20px'}
            ),
            href='https://opendata.transport.nsw.gov.au/data/dataset/nsw-crash-data',
            target='_blank',
            style={'textDecoration': 'none'}
        ),
        html.H1(
            'Road Crash Statistics',
            style={'margin': '0', 'fontSize': '28px', 'fontWeight': '600', 'fontFamily': 'Trebuchet MS, sans-serif', 'textAlign': 'left'}
        ),
    ],
        style={'display': 'flex', 'alignItems': 'center', 'padding': '12px 20px', 'borderBottom': '1px solid #ddd', 'backgroundColor': "#e0eaf4", 'marginBottom': '20px'}
    ),

    # Top row: RangeSlider on the left, Weather selector on the right
    # Use class names so responsive CSS in assets/style.css can switch layout
    html.Div([
        html.Div([
            html.Div("Select Year of Crash:", style={'marginBottom': '8px'}),
            dcc.RangeSlider(
                min=int(transport_nsw_df['year_of_crash'].min()),
                max=int(transport_nsw_df['year_of_crash'].max()),
                step=1,
                value=[
                    int(transport_nsw_df['year_of_crash'].min()),
                    int(transport_nsw_df['year_of_crash'].max())
                ],
                marks={str(year): str(year) for year in sorted(transport_nsw_df['year_of_crash'].unique())},
                id='year-slider'
            )
        ], style={'flex': '1'}, className='filter-control range'),

        html.Div([
            html.Div("Select Weather Conditions:", style={'marginBottom': '8px'}),
            dcc.Dropdown(
                options=weather_options,
                value=['All'],
                multi=True,
                id='weather-selector',
                clearable=False,
            )
        ], className='filter-control'),

        html.Div([
            html.Div("Select Surface Condition:", style={'marginBottom': '8px'}),
            dcc.Dropdown(
                options=surface_condition_options,
                value=['All'],
                multi=True,
                id='surface-condition-selector',
                clearable=False,
            )
        ], className='filter-control'),

        html.Div([
            html.Div("Select Local Government Area:", style={'marginBottom': '8px'}),
            dcc.Dropdown(
                options=lga_options,
                value=['All'],
                multi=True,
                id='lga-selector',
                clearable=False,
            )
        ], className='filter-control'),

    ], className='filters-row', style={'fontFamily': 'Trebuchet MS, sans-serif'}),

    # Key Indicators Row
    html.Div([
        html.Div([
            html.Div("Total Accidents", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px'}),
            html.Div(id='total-accidents', style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#333'})
        ], className='indicator-card'),
        
        html.Div([
            html.Div("Passengers Involved", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px'}),
            html.Div(id='passengers-involved', style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#333'})
        ], className='indicator-card'),
        
        html.Div([
            html.Div("Moderately Injured", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px'}),
            html.Div(id='moderately-injured', style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#FF9800'})
        ], className='indicator-card'),
        
        html.Div([
            html.Div("Seriously Injured", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px'}),
            html.Div(id='seriously-injured', style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#FF5722'})
        ], className='indicator-card'),
        
        html.Div([
            html.Div("Killed", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px'}),
            html.Div(id='killed', style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#ce0e25'})
        ], className='indicator-card'),
    ], className='indicators-row', style={'fontFamily': 'Trebuchet MS, sans-serif', 'marginBottom': '20px'}),

    # Second row: Three charts (Trend, Location Types, Injury Distribution)
    html.Div([
        html.Div([
            html.H1(
                'Accidents & Fatalities Trend',
                style={'margin': '0', 'fontSize': '18px', 'fontWeight': '300', 'fontFamily': 'Trebuchet MS, sans-serif', 'textAlign': 'left'}
            ),
            dcc.Graph(id='trend-chart', className='trend-chart', style={'height': '350px'}),
        ], className='chart-card'),
        html.Div([
            html.H1(
                'Top 5 Location Types',
                style={'margin': '0', 'fontSize': '18px', 'fontWeight': '300', 'fontFamily': 'Trebuchet MS, sans-serif', 'textAlign': 'left'}
            ),
            dcc.Graph(id='location-bar-chart', className='location-bar-chart', style={'height': '350px'}),
        ], className='chart-card'),
        html.Div([
            html.H1(
                'Injury Distribution',
                style={'margin': '0', 'fontSize': '18px', 'fontWeight': '300', 'fontFamily': 'Trebuchet MS, sans-serif', 'textAlign': 'left'}
            ),
            dcc.Graph(id='degree-pie-chart', className='degree-pie-chart', style={'height': '350px'}),
        ], className='chart-card'),
    ], className='graphs-row', style={'fontFamily': 'Trebuchet MS, sans-serif', 'marginBottom': '20px'}),

    # Third row: Speed Limit vs Accidents, Region Distribution, and Map
    html.Div([
        html.Div([
            html.H1(
                'Speed Limit vs Accidents',
                style={'margin': '0', 'fontSize': '18px', 'fontWeight': '300', 'fontFamily': 'Trebuchet MS, sans-serif', 'textAlign': 'left'}
            ),
            dcc.Graph(id='speed-limit-chart', className='speed-limit-chart', style={'height': '350px'}),
        ], className='chart-card'),
        html.Div([
            html.H1(
                'Region Distribution',
                style={'margin': '0', 'fontSize': '18px', 'fontWeight': '300', 'fontFamily': 'Trebuchet MS, sans-serif', 'textAlign': 'left'}
            ),
            dcc.Graph(id='conurbation-donut-chart', className='conurbation-donut-chart', style={'height': '350px'}),
        ], className='chart-card'),
        html.Div([
            dcc.Graph(id='map-chart', className='map-chart', style={'height': '350px'}),
        ], className='chart-card'),
    ], className='graphs-row', style={'fontFamily': 'Trebuchet MS, sans-serif'}),

    # Data Source and License Card
    html.Div([
        html.Div([
            html.Span('Data Source: ', className='label'),
            html.A(
                'TfNSW Open Data Hub',
                href='https://opendata.transport.nsw.gov.au/data/dataset/nsw-crash-data',
                target='_blank',
                className='separator'
            ),
            html.Br(),
            html.Span('License: ', className='label'),
            html.A(
                'Creative Commons Attribution',
                href='https://opendefinition.org/licenses/cc-by/',
                target='_blank'
            ),
        ], className='data-source-card', style={'marginTop': '15px'})
    ], className='data-source-container')
])


@app.callback(
    Output('map-chart', 'figure'),
    Output('degree-pie-chart', 'figure'),
    Output('trend-chart', 'figure'),
    Output('speed-limit-chart', 'figure'),
    Output('location-bar-chart', 'figure'),
    Output('conurbation-donut-chart', 'figure'),
    Output('total-accidents', 'children'),
    Output('passengers-involved', 'children'),
    Output('moderately-injured', 'children'),
    Output('seriously-injured', 'children'),
    Output('killed', 'children'),
    Input('year-slider', 'value'),
    Input('weather-selector', 'value'),
    Input('surface-condition-selector', 'value'),
    Input('lga-selector', 'value')
)

def update_figure(selected_range, selected_weather, selected_surface_condition, selected_lga):
    start_year, end_year = selected_range
    filtered_df = transport_nsw_df[
        (transport_nsw_df['year_of_crash'] >= start_year) &
        (transport_nsw_df['year_of_crash'] <= end_year)
    ].copy()

    # Apply filters
    # The dropdown returns a list; 'All' indicates no filtering.
    if selected_weather and 'All' not in selected_weather:
        filtered_df = filtered_df[filtered_df['weather'].astype(str).isin(selected_weather)]
    if selected_surface_condition and 'All' not in selected_surface_condition:
        filtered_df = filtered_df[filtered_df['surface_condition'].astype(str).isin(selected_surface_condition)]
    if selected_lga and 'All' not in selected_lga:
        filtered_df = filtered_df[filtered_df['lga'].astype(str).isin(selected_lga)]

    # Color mapping used for charts below.
    injury_donut_color_map = {
        'Non-casualty (towaway)': "#15a539",
        'Minor/Other Injury':     "#dcac2a",
        'Moderate Injury':        "#5BB3BC",
        'Serious Injury':         "#45134E",
        'Fatal':                  "#ce0e25",
    }

    map_color_map = {
        'Non-casualty (towaway)': "#2ca02c",
        'Injury':                 "#9467bd",
        'Fatal':                  "#ce0e25",
    }

    map_fig = px.scatter_map(
        filtered_df,
        lat='latitude',
        lon='longitude',
        hover_name='degree_of_crash_detailed',
        # color markers by the degree_of_crash column
        #color='degree_of_crash',
        #color_discrete_map=map_color_map,
        zoom=12,
        center={'lat': -33.871, 'lon': 151.195},
        custom_data=['year_of_crash', 'weather', 'no_killed', 'no_total_injured'],
        opacity=0.3,
    )

    # Define a hovertemplate with human-readable labels. Use <extra></extra> to remove the trace name box.
    map_hover_template = (
         "<b>%{hovertext}</b><br><br>"
         "Year of crash: <b><span style='font-size:16px'>%{customdata[0]}</span></b><br>"
         "Weather: <b><span style='font-size:16px'>%{customdata[1]}</span></b><br>"
         "<b><span style='font-size:16px'>%{customdata[2]}</span></b> killed<br>"
         "<b><span style='font-size:16px'>%{customdata[3]}</span></b> injured<br>"
         "<extra></extra>"
    )

    # Apply hovertemplate to all traces
    for trace in map_fig.data:
        trace.hovertemplate = map_hover_template

    map_fig.update_layout(
        mapbox_style='open-street-map', 
        transition_duration=500, 
        showlegend=False,
        height=350,
        autosize=True
    )
    map_fig.update_layout(margin={'r':0,'t':0,'l':0,'b':0})

    # Build Degree of Crash distribution and convert to percentage-based pie chart.
    pie_desired_order = ['Non-casualty (towaway)', 'Minor/Other Injury', 'Moderate Injury', 'Serious Injury', 'Fatal']

    # Mapping for concise labels
    label_mapping = {
        'Non-casualty (towaway)': 'Non-casualty',
        'Minor/Other Injury': 'Minor',
        'Moderate Injury': 'Moderate',
        'Serious Injury': 'Serious',
        'Fatal': 'Fatal',
    }

    # Compute counts and reindex to ensure all categories appear in the desired order
    degree_of_crash_counts = filtered_df['degree_of_crash_detailed'].value_counts().reindex(pie_desired_order, fill_value=0)
    crash_distribution = (degree_of_crash_counts.rename_axis('degree_of_crash_detailed').reset_index(name='count'))
    
    # Map to concise labels
    crash_distribution['label'] = crash_distribution['degree_of_crash_detailed'].map(label_mapping)

    injury_donut_fig = px.pie(
        crash_distribution,
        names='label',
        values='count',
        hole=0.4,
        labels={"label": "Crash Degree", "count": "Count of Incidents"},
        category_orders={'label': ['Non-casualty', 'Minor', 'Moderate', 'Serious', 'Fatal']},
        color='degree_of_crash_detailed',
        color_discrete_map=injury_donut_color_map
    )

    # Custom hover template for pie chart
    pie_hover_template = (
        "<b>%{label}</b><br><br>"
        "Count: <b><span style='font-size:16px'>%{value:,}</span></b><br>"
        "Percentage: <b><span style='font-size:16px'>%{percent}</span></b><br>"
        "<extra></extra>"
    )

    # Slightly pull all slices to match prior behaviour
    injury_donut_fig.update_traces(
        textinfo='percent+label', 
        pull=[0.05] * len(pie_desired_order),
        hovertemplate=pie_hover_template
    )
    # Disable legend and keep existing donut hole/margins
    injury_donut_fig.update_layout(
        showlegend=False, 
        margin={'r':0,'t':40,'l':0,'b':0},
        height=350,
        autosize=True
    )

    # Calculate key indicators
    total_accidents = len(filtered_df)
    passengers_involved = int(filtered_df['no_of_traffic_units_involved'].sum())
    moderately_injured = int(filtered_df['no_moderately_injured'].sum())
    seriously_injured = int(filtered_df['no_seriously_injured'].sum())
    killed = int(filtered_df['no_killed'].sum())

    # Create trend chart (dual axis line chart)
    # Group by year and calculate totals, excluding 2018
    trend_data = filtered_df[filtered_df['year_of_crash'] != 2018].groupby('year_of_crash').agg({
        'crash_id': 'count',
        'no_killed': 'sum'
    }).reset_index()
    trend_data.columns = ['Year', 'Total Accidents', 'People Killed']

    # Create figure with secondary y-axis
    trend_fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add Total Accidents line
    trend_fig.add_trace(
        go.Scatter(
            x=trend_data['Year'],
            y=trend_data['Total Accidents'],
            name='Total Accidents',
            line=dict(color="#86a8da", width=3),
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate='<br><b><span style="font-size:16px">%{y:,}</span></b> accidents<extra></extra>'
        ),
        secondary_y=False
    )

    # Add People Killed line
    trend_fig.add_trace(
        go.Scatter(
            x=trend_data['Year'],
            y=trend_data['People Killed'],
            name='People Killed',
            line=dict(color='#ce0e25', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate='<br><b><span style="font-size:16px">%{y:,}</span></b> killed<extra></extra>'
        ),
        secondary_y=True
    )

    # Update axes
    trend_fig.update_xaxes(title_text="Year", gridcolor='#e0e0e0')
    trend_fig.update_yaxes(title_text="Total Accidents", secondary_y=False, gridcolor='#e0e0e0')
    trend_fig.update_yaxes(title_text="People Killed", secondary_y=True, gridcolor='#e0e0e0')

    trend_fig.update_layout(
        height=350,
        autosize=True,
        margin={'r': 0, 't': 40, 'l': 0, 'b': 0},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        plot_bgcolor='white'
    )

    # Create speed limit vs accidents chart (dual axis)
    # Filter data to exclude Unknown and only include 40-110 km/h
    speed_limits_to_include = ['40 km/h', '50 km/h', '60 km/h', '70 km/h', '80 km/h', '90 km/h', '100 km/h', '110 km/h']
    speed_filtered_df = filtered_df[filtered_df['speed_limit'].isin(speed_limits_to_include)].copy()
    
    # Group by speed limit and calculate total accidents and death rate
    speed_limit_data = speed_filtered_df.groupby('speed_limit').agg({
        'crash_id': 'count',
        'no_killed': 'sum',
        'no_of_traffic_units_involved': 'sum'
    }).reset_index()
    speed_limit_data.columns = ['Speed Limit', 'Total Accidents', 'Killed', 'Passengers Involved']
    
    # Calculate death rate (killed per passengers involved, as percentage)
    speed_limit_data['Death Rate'] = (speed_limit_data['Killed'] / speed_limit_data['Passengers Involved'] * 100).fillna(0)
    
    # Sort by speed limit value for proper ordering
    speed_order = ['40 km/h', '50 km/h', '60 km/h', '70 km/h', '80 km/h', '90 km/h', '100 km/h', '110 km/h']
    speed_limit_data['Speed Limit'] = pd.Categorical(speed_limit_data['Speed Limit'], categories=speed_order, ordered=True)
    speed_limit_data = speed_limit_data.sort_values('Speed Limit')

    # Create figure with secondary y-axis
    speed_limit_fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar chart for Total Accidents
    speed_limit_fig.add_trace(
        go.Bar(
            x=speed_limit_data['Speed Limit'],
            y=speed_limit_data['Total Accidents'],
            name='Total Accidents',
            marker_color='#86a8da',
            hovertemplate='<br>Accidents: <b><span style="font-size:15px">%{y:,}</span></b><extra></extra>'
        ),
        secondary_y=False
    )

    # Add line chart for Death Rate
    speed_limit_fig.add_trace(
        go.Scatter(
            x=speed_limit_data['Speed Limit'],
            y=speed_limit_data['Death Rate'],
            name='Death Rate (%)',
            line=dict(color='#ce0e25', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate='<br>Death Rate: <b><span style="font-size:15px">%{y:.2f}%</span></b><extra></extra>'
        ),
        secondary_y=True
    )

    # Update axes
    speed_limit_fig.update_xaxes(title_text="Speed Limit", gridcolor='#e0e0e0')
    speed_limit_fig.update_yaxes(title_text="Total Accidents", secondary_y=False, gridcolor='#e0e0e0')
    speed_limit_fig.update_yaxes(title_text="Death Rate (%)", secondary_y=True, gridcolor='#e0e0e0')

    speed_limit_fig.update_layout(
        height=350,
        autosize=True,
        margin={'r': 0, 't': 40, 'l': 0, 'b': 0},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        plot_bgcolor='white'
    )

    # Create location type bar chart (Top 5)
    location_counts = filtered_df['type_of_location'].value_counts().head(5).reset_index()
    location_counts.columns = ['Location Type', 'Count']
    location_counts = location_counts.sort_values('Count', ascending=True)  # Sort for better visualization

    # Calculate percentages
    total_location = location_counts['Count'].sum()
    location_counts['Percentage'] = (location_counts['Count'] / total_location * 100).round(1)

    location_bar_fig = px.bar(
        location_counts,
        y='Location Type',
        x='Count',
        orientation='h',
        labels={"Location Type": "Location Type", "Count": "Count of Incidents"},
        text='Count'
    )

    location_hover_template = (
        "<b>%{y}</b><br><br>"
        "Count: <b><span style='font-size:16px'>%{x:,}</span></b><br>"
        "Percentage: <b><span style='font-size:16px'>%{customdata[0]}%</span></b><br>"
        "<extra></extra>"
    )

    location_bar_fig.update_traces(
        hovertemplate=location_hover_template,
        customdata=location_counts[['Percentage']].values,
    )

    location_bar_fig.update_layout(
        showlegend=False,
        margin={'r': 0, 't': 40, 'l': 0, 'b': 0},
        height=350,
        autosize=True,
        plot_bgcolor='white',
        xaxis=dict(gridcolor='#e0e0e0', title='Number of Accidents'),
        yaxis=dict(title='')
    )

    # Create conurbation donut chart
    # Filter out 'Rest of NSW - Unknown' and create mapping for labels
    conurbation_df = filtered_df[filtered_df['conurbation_1'] != 'Rest of NSW - Unknown'].copy()
    
    # Mapping for region labels
    region_label_mapping = {
        'Syd-Newc-Woll Gtr conurbation': 'Metropolitan',
        'Rest of NSW - Rural': 'Rural',
        'Rest of NSW - Urban': 'Urban'
    }
    
    conurbation_counts = conurbation_df['conurbation_1'].value_counts().reset_index()
    conurbation_counts.columns = ['Region', 'Count']
    
    # Apply label mapping
    conurbation_counts['Label'] = conurbation_counts['Region'].map(region_label_mapping).fillna(conurbation_counts['Region'])

    conurbation_donut_fig = px.pie(
        conurbation_counts,
        names='Label',
        values='Count',
        hole=0.4,
        labels={"Label": "Region", "Count": "Count of Incidents"}
    )

    # Custom hover template for conurbation donut chart
    conurbation_hover_template = (
        "<b>%{label}</b><br><br>"
        "Count: <b><span style='font-size:16px'>%{value:,}</span></b><br>"
        "Percentage: <b><span style='font-size:16px'>%{percent}</span></b><br>"
        "<extra></extra>"
    )

    conurbation_donut_fig.update_traces(
        textinfo='percent+label',
        pull=[0.05] * len(conurbation_counts),
        hovertemplate=conurbation_hover_template
    )

    conurbation_donut_fig.update_layout(
        showlegend=False,
        margin={'r': 0, 't': 40, 'l': 0, 'b': 0},
        height=350,
        autosize=True
    )

    return map_fig, injury_donut_fig, trend_fig, speed_limit_fig, location_bar_fig, conurbation_donut_fig, f"{total_accidents:,}", f"{passengers_involved:,}", f"{moderately_injured:,}", f"{seriously_injured:,}", f"{killed:,}"

@app.server.route('/assets/nsw.svg')
def serve_nsw():
    return send_from_directory('.', 'assets/nsw.svg')

if __name__ == '__main__':
    app.run()
