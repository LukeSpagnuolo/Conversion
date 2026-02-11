#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 08:15:09 2025

Conversion Dashboard

@author: lukespagnuolo
"""

import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import threading, webbrowser

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DF_PATH = BASE_DIR / "Conversion_Data_2025.csv"
df = pd.read_csv(DF_PATH)

sports = df['Sport'].sort_values().unique()
sport_options = [{"label": s, "value": s} for s in sports]

# — Column options for X/Y selectors (unused but keeping)
column_options = [{"label": col, "value": col} for col in df.columns]

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("CSIP Conversion Dashboard"),

    # Sport filter and year
    html.Div([
        html.Div([
            html.Label("Select Sport(s):"),
            dcc.Dropdown(
                id="sport-dropdown",
                options=sport_options,
                value=list(sports),          # default = ALL sports
                multi=True,                  # multi-select
                clearable=True,
                style={"width": "100%"}
            )
        ], style={"width": "48%", "marginRight": "4%"}),

        html.Div([
            html.Label("Select Years:"),
            dcc.Dropdown(
                id="year-filter",
                multi=True,
                placeholder="Select one or more years",
                style={"width": "100%"}
            )
        ], style={"width": "48%"})
    ], style={"display": "flex", "marginBottom": "30px"}),

    # Checkbox to limit cohort to athletes with any entry in 2025
    html.Div([
        dcc.Checklist(
            id="has-2025-checkbox",
            options=[{
                "label": "Only athletes with 2025 as one of their years",
                "value": "2025"
            }],
            value=[],
            inputStyle={"margin-right": "10px"}
        )
    ], style={"marginBottom": "30px"}),

    # Graphs and tables
    dcc.Graph(id="time-series-graph"),
    html.Div(id="conversion-summary"),
    dcc.Graph(id="program-lines-graph"),
    dcc.Graph(id="program-composition-bar-chart"),
    dcc.Graph(id="cohort-pie-chart"),
    dcc.Graph(id="years-targeted-pie-chart"),
    dcc.Graph(id="program-pie-chart"),

    html.Div([
        html.Label("Filter Age of Conversion Pie Chart by Program Level:"),
        dcc.Checklist(
            id="age-pie-program-filter",
            options=[{"label": p, "value": p} for p in
                     ['Prov Dev 2', 'Prov Dev 1', 'Uncarded', 'SC Carded']],
            value=[],
            inline=True
        )
    ], style={"marginBottom": "15px"}),

    dcc.Graph(id="age-conversion-pie-chart")
])

def _sports_label(selected_sports):
    if not selected_sports:
        return "No Sport Selected"
    if len(selected_sports) <= 3:
        return ", ".join(selected_sports)
    return f"{len(selected_sports)} sports"

@app.callback(
    Output("year-filter", "options"),
    Output("year-filter", "value"),
    Input("sport-dropdown", "value")
)
def update_year_dropdown(selected_sports):
    if not selected_sports:
        return [], []
    dff = df[df['Sport'].isin(selected_sports)]
    years = sorted(dff['Year'].dropna().astype(int).unique())
    return [{"label": str(y), "value": y} for y in years], years

@app.callback(
    Output("time-series-graph", "figure"),
    Output("conversion-summary", "children"),
    Output("program-lines-graph", "figure"),
    Output("program-composition-bar-chart", "figure"),
    Output("cohort-pie-chart", "figure"),
    Output("years-targeted-pie-chart", "figure"),
    Output("program-pie-chart", "figure"),
    Output("age-conversion-pie-chart", "figure"),
    Input("sport-dropdown", "value"),
    Input("has-2025-checkbox", "value"),
    Input("year-filter", "value"),
    Input("age-pie-program-filter", "value")
)
def update_graphs(selected_sports, filter_2025, selected_years, prog_filter):
    # Guard: nothing selected
    if not selected_sports:
        empty_fig = go.Figure()
        msg = html.Div("No sport(s) selected.", style={"padding": "8px"})
        return empty_fig, msg, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # Filter by sport(s)
    dff = df[df['Sport'].isin(selected_sports)].copy()

    # Filter by selected years
    if selected_years:
        dff = dff[dff['Year'].isin(selected_years)]

    # Time-series metrics by Year
    grp = dff.groupby('Year', sort=True)

    unique_athletes = grp.apply(
        lambda g: g[['First Name', 'Last Name']].drop_duplicates().shape[0]
    ).sort_index()

    converted = grp['Convert Year'].apply(lambda col: col.eq('Y').sum()).sort_index()
    avg_targeted = grp['Years Targeted'].mean().sort_index()
    conversion_rate = (converted / unique_athletes * 100).fillna(0)

    # Build time-series figure
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=unique_athletes.index, y=unique_athletes.values,
        mode='lines+markers', name='Total Athletes', yaxis='y1'
    ))
    fig_ts.add_trace(go.Scatter(
        x=converted.index, y=converted.values,
        mode='lines+markers', name='Conversion Count', yaxis='y1'
    ))
    fig_ts.add_trace(go.Scatter(
        x=avg_targeted.index, y=avg_targeted.values,
        mode='lines+markers', name='Average Years Targeted', yaxis='y2',
        hovertemplate='%{y:.1f}'
    ))
    fig_ts.add_trace(go.Scatter(
        x=conversion_rate.index, y=conversion_rate.values,
        mode='lines+markers', name='Conversion Rate (%)', yaxis='y3',
        hovertemplate='%{y:.1f}%'
    ))

    fig_ts.update_layout(
        title=f"Time Series — {_sports_label(selected_sports)}",
        yaxis=dict(title="Count of Athletes", showgrid=False),
        yaxis2=dict(
            title="Average Years Targeted",
            overlaying="y", side="right", anchor="free",
            position=1.0, showgrid=False
        ),
        yaxis3=dict(
            title="Conversion Rate (%)",
            overlaying="y", side="right", anchor="free",
            position=0.95, tickformat=".0f"
        ),
        xaxis=dict(title="Year", tickmode="linear", dtick=1, tickformat=".0f")
    )

    # ── Summary Table (now with avg age at first/last targeted) ─────────────
    # Build a clean per-athlete table within the *filtered* cohort
    dff_age = dff.copy()
    dff_age['DOB_parsed'] = pd.to_datetime(dff_age['Date of Birth'], errors='coerce')
    dff_age['BirthYear']  = dff_age['DOB_parsed'].dt.year
    dff_age = dff_age.dropna(subset=['BirthYear', 'Year'])
    
    # ── Avg. Years Targeted (per athlete) ─────────────────────────────
       # Use each athlete's max Years Targeted within the *filtered* cohort
    per_ath_years = (
           dff
           .groupby(['First Name', 'Last Name', 'Sport'])['Years Targeted']
           .max()
           .reset_index(name='years_targeted')
       )
    
    if not per_ath_years.empty:
           avg_years_targeted = per_ath_years['years_targeted'].mean()
           n_years = len(per_ath_years)
    else:
           avg_years_targeted = float('nan')
           n_years = 0

    # Group by athlete (and Sport to avoid collisions for same names in different sports)
    per_ath = (
        dff_age
        .groupby(['First Name', 'Last Name', 'Sport'], as_index=False)
        .agg(first_year=('Year', 'min'),
             last_year =('Year', 'max'),
             birth_year=('BirthYear', 'first'))
        .dropna(subset=['birth_year'])
    )
    per_ath['age_first'] = per_ath['first_year'].astype(int) - per_ath['birth_year'].astype(int)
    per_ath['age_last']  = per_ath['last_year'].astype(int)  - per_ath['birth_year'].astype(int)

    if not per_ath.empty:
        avg_age_first = per_ath['age_first'].mean()
        avg_age_last  = per_ath['age_last'].mean()
        n_ath_age     = len(per_ath)
    else:
        avg_age_first = float('nan')
        avg_age_last  = float('nan')
        n_ath_age     = 0

    # Existing averages
    avg_conv = converted.mean()
    avg_conv_rate = conversion_rate.mean()

    summary_table = html.Table([
        html.Thead([html.Tr([html.Th("Metric"), html.Th("Average")])]),
        html.Tbody([
            html.Tr([html.Td("Avg. Conversions"), html.Td(f"{avg_conv:.1f}")]),
            html.Tr([html.Td("Avg. Conversion Rate"), html.Td(f"{avg_conv_rate:.1f}%")]),
            html.Tr([html.Td("Avg. Age — First Targeted"),
                     html.Td(f"{avg_age_first:.1f} yrs" if n_ath_age else "—")]),
            html.Tr([html.Td("Avg. Age — Last Targeted"),
                     html.Td(f"{avg_age_last:.1f} yrs"  if n_ath_age else "—")]),

            # ⭐ New:
            html.Tr([html.Td("Avg. Years Targeted (per athlete)"),
                     html.Td(f"{avg_years_targeted:.2f}" if n_years else "—")]),
        ])
    ], className="conversion-summary-table")

    # Program-level conversion counts (lines)
    prog_year_conv = (
        dff[dff['Convert Year'] == 'Y']
        .groupby(['Year', 'Program'])[['First Name', 'Last Name']]
        .apply(lambda g: g.drop_duplicates().shape[0])
        .reset_index(name='Count')
    )

    prog_line_pivot = (
        prog_year_conv
        .pivot(index='Year', columns='Program', values='Count')
        .fillna(0)
        .sort_index()
    )

    stack_order = ['Prov Dev 2', 'Prov Dev 1', 'Uncarded', 'SC Carded']
    fig_program_lines = go.Figure()
    for program in stack_order:
        if program in prog_line_pivot.columns:
            fig_program_lines.add_trace(go.Scatter(
                x=prog_line_pivot.index,
                y=prog_line_pivot[program],
                mode='lines+markers',
                name=program,
                hovertemplate='%{y:.0f}'
            ))
    fig_program_lines.update_layout(
        title=f"Converted Athletes by Program Level — {_sports_label(selected_sports)}",
        xaxis=dict(title='Year', tickmode='linear', dtick=1, tickformat='.0f'),
        yaxis=dict(title='Conversion Count'),
        legend=dict(orientation='h', y=-0.2),
        margin=dict(l=50, r=50, t=60, b=60)
    )

    # Program Composition by Year (stacked bar)
    program_year_data = (
        dff
        .groupby(['Year', 'Program'])[['First Name', 'Last Name']]
        .apply(lambda g: g.drop_duplicates().shape[0])
        .reset_index(name='Count')
    )

    program_pivot = (
        program_year_data
        .pivot(index='Year', columns='Program', values='Count')
        .fillna(0)
        .sort_index()
    )

    fig_bar = go.Figure()
    for program in stack_order:
        if program in program_pivot.columns:
            fig_bar.add_trace(go.Bar(
                x=program_pivot.index,
                y=program_pivot[program],
                name=program
            ))
    fig_bar.update_layout(
        barmode='stack',
        title=f"Program Composition by Year — {_sports_label(selected_sports)}",
        xaxis=dict(title='Year', tickmode='linear', dtick=1, tickformat='.0f'),
        yaxis=dict(title='Athlete Count'),
        margin=dict(l=50, r=50, t=60, b=40)
    )

    # Cohort scope for pies
    if "2025" in filter_2025:
        dff_pies = dff.groupby(['First Name', 'Last Name']).filter(lambda g: (g['Year'] == 2025).any())
    else:
        dff_pies = dff

    # Cohort-wide conversion pie
    conv_by_athlete = (
        dff_pies
        .groupby(['First Name', 'Last Name'])['Convert Year']
        .apply(lambda col: col.eq('Y').any())
    )
    num_converted = int(conv_by_athlete.sum())
    num_never = int(conv_by_athlete.shape[0] - num_converted)

    fig_pie = go.Figure(data=[go.Pie(
        labels=["Career Converter", "Never Converted"],
        values=[num_converted, num_never],
        hole=0.3,
        sort=False
    )])
    fig_pie.update_layout(
        title_text=f"Cohort Conversion — {_sports_label(selected_sports)}",
        legend=dict(traceorder='normal'),
        margin=dict(l=40, r=40, t=50, b=40)
    )

    # Years-Targeted dispersion pie
    years_by_athlete = (
        dff_pies
        .groupby(['First Name', 'Last Name'])['Years Targeted']
        .max()
    )
    counts = years_by_athlete.value_counts().sort_index()
    labels = [f"{yr} yr" for yr in counts.index]
    values = counts.values

    fig_disp = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3, sort=False)])
    fig_disp.update_layout(
        title_text=f"Distribution of Years Targeted — {_sports_label(selected_sports)}",
        legend=dict(traceorder='normal'),
        margin=dict(l=40, r=40, t=50, b=40)
    )

    # Program-level conversion pie
    prog_conv = (
        dff_pies[dff_pies['Convert Year'] == 'Y']
        .groupby('Program')[['First Name', 'Last Name']]
        .apply(lambda g: g.drop_duplicates().shape[0])
        .sort_index()
    )
    fig_prog = go.Figure(data=[go.Pie(
        labels=prog_conv.index, values=prog_conv.values, hole=0.3, sort=False
    )])
    fig_prog.update_layout(
        title_text=f"Conversion by Level — {_sports_label(selected_sports)}",
        legend=dict(traceorder='normal'),
        margin=dict(l=40, r=40, t=50, b=40)
    )

    # Age-at-conversion pie (with optional program filter)
    conv_rows = dff_pies[dff_pies['Convert Year'] == 'Y'].copy()
    if prog_filter:
        conv_rows = conv_rows[conv_rows['Program'].isin(prog_filter)]

    conv_rows['DOB_parsed'] = pd.to_datetime(conv_rows['Date of Birth'], errors='coerce')
    conv_rows['BirthYear'] = conv_rows['DOB_parsed'].dt.year
    conv_rows['AgeAtConvert'] = conv_rows['Year'].astype(int) - conv_rows['BirthYear']

    age_counts = (
        conv_rows
        .groupby('AgeAtConvert')[['First Name', 'Last Name']]
        .apply(lambda g: g.drop_duplicates().shape[0])
        .sort_index()
    )

    if age_counts.empty:
        fig_age_pie = go.Figure()
        fig_age_pie.update_layout(
            title_text="No data for selected filters",
            margin=dict(l=40, r=40, t=50, b=40)
        )
    else:
        fig_age_pie = go.Figure(data=[go.Pie(
            labels=[f"{int(a)} yr" for a in age_counts.index],
            values=age_counts.values,
            hole=0.3,
            sort=False
        )])
        fig_age_pie.update_layout(
            title_text=f"Age at Conversion — {_sports_label(selected_sports)}",
            margin=dict(l=40, r=40, t=50, b=40)
        )

    return (fig_ts, summary_table, fig_program_lines, fig_bar,
            fig_pie, fig_disp, fig_prog, fig_age_pie)

# Open the Dash app in the default browser
threading.Timer(
    1,  # seconds to wait so the server is up
    lambda: webbrowser.open_new("http://127.0.0.1:8050/")
).start()

if __name__ == "__main__":
    app.run(debug=True)
