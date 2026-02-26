#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversion Dashboard v2 — Posit Connect deployment

Authentication: DashAuthExternal (OAuth2 via Django OAuth Toolkit).
All credentials are supplied as environment variables set in Posit Connect's
Vars tab (or a local .env file for development).

Required env vars:
  SITE_URL             — base URL of the Django OAuth provider
  OAUTH_REDIRECT_PATH  — full public redirect URI registered on the provider
                         (the Posit Connect app URL + /redirect)
  CLIENT_ID            — OAuth2 client ID
  CLIENT_SECRET        — OAuth2 client secret

Optional (local dev only):
  APP_HOST             — listen address  (default: 127.0.0.1)
  APP_PORT             — listen port     (default: 8050)
  DEV_MODE             — enable debug mode (default: false)

Entry point for gunicorn / Posit Connect:
  gunicorn "Conversion_Dashboard_v2:server"
"""

import os
import base64
from pathlib import Path

from dash_auth_external import DashAuthExternal
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go

try:
    import dash_bootstrap_components as dbc
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    BOOTSTRAP_AVAILABLE = False

if BOOTSTRAP_AVAILABLE:
    from navbar import Navbar
    from footer import Footer

BASE_DIR = Path(__file__).resolve().parent

# ── OAuth / URL Config ──────────────────────────────────────────────────────
# Set these in Posit Connect's Vars tab (never hardcode secrets in production)
SITE_URL            = os.environ["SITE_URL"].rstrip("/")
OAUTH_REDIRECT_PATH = os.environ["OAUTH_REDIRECT_PATH"]
CLIENT_ID           = os.environ["CLIENT_ID"]
CLIENT_SECRET       = os.environ["CLIENT_SECRET"]

AUTH_URL  = f"{SITE_URL}/o/authorize"
TOKEN_URL = f"{SITE_URL}/o/token/"

# ── Auth setup ───────────────────────────────────────────────────────────────
auth = DashAuthExternal(
    AUTH_URL,
    TOKEN_URL,
    app_url=OAUTH_REDIRECT_PATH,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

external_stylesheets = [dbc.themes.UNITED] if BOOTSTRAP_AVAILABLE else []

app = dash.Dash(
    __name__,
    server=auth.server,
    external_stylesheets=external_stylesheets,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)


def _asset_image_src(asset_subpath: str) -> str:
    file_path = BASE_DIR / "assets" / asset_subpath
    if file_path.exists():
        suffix = file_path.suffix.lower()
        mime_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(suffix, "application/octet-stream")
        encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"
    return app.get_asset_url(asset_subpath)

navbar_component = None
footer_component = None
if BOOTSTRAP_AVAILABLE:
    logo_src = _asset_image_src("img/csi-pacific-logo-reverse.png")
    medal_src = _asset_image_src("img/csi-medal.png")
    navbar_component = Navbar(
        buttons=[{"label": "Dashboard", "url": "/"}],
        title="CSIP Conversion Dashboard",
        logo_src=logo_src,
    )
    footer_component = Footer(logo_src=logo_src, medal_src=medal_src)

# `server` is exposed at module level for Posit Connect / gunicorn:
#   gunicorn "Conversion_Dashboard_v2:server"
server = auth.server

# ── Data ─────────────────────────────────────────────────────────────────────
DF_PATH  = BASE_DIR / "Conversion_Data_2026_final.csv"
df = pd.read_csv(DF_PATH)

sports        = df['Sport'].sort_values().unique()
sport_options = [{"label": s, "value": s} for s in sports]

# ── Color / Theme ─────────────────────────────────────────────────────────────
COLOR_RED      = "#DC3545"
COLOR_BLACK    = "#1a1a1a"
COLOR_DARK_GRAY = "#2d2d2d"
COLOR_WHITE    = "#ffffff"

VIBRANT_PALETTE = [
    "#FF4444",  # Bright Red
    "#44FF44",  # Bright Green
    "#4488FF",  # Bright Blue
    "#FFBB00",  # Bright Orange
    "#FF00FF",  # Bright Magenta
]

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    navbar_component.render() if navbar_component else html.Div(),

    html.Div([
        # Filters
        html.Div([
            html.Div([
                html.Label("Select Sport(s):"),
                dcc.Dropdown(
                    id="sport-dropdown",
                    options=sport_options,
                    value=[],
                    multi=True,
                    clearable=True,
                    style={"width": "100%"},
                )
            ], className="filter-col filter-col-left"),

            html.Div([
                html.Label("Select Years:"),
                dcc.Dropdown(
                    id="year-filter",
                    multi=True,
                    placeholder="Select one or more years",
                    style={"width": "100%"},
                )
            ], className="filter-col"),
        ], className="filter-row"),

        html.Div([
            dcc.Checklist(
                id="has-2026-checkbox",
                options=[{"label": "Only athletes with 2026 as one of their years", "value": "2026"}],
                value=[],
                inputStyle={"margin-right": "10px"},
            )
        ], style={"marginBottom": "30px"}),

        # Charts & tables
        dcc.Graph(id="time-series-graph", className="dashboard-graph graph-timeseries", config={"responsive": True}),
        html.Div(id="conversion-summary"),
        dcc.Graph(id="program-lines-graph", className="dashboard-graph", config={"responsive": True}),
        dcc.Graph(id="program-composition-bar-chart", className="dashboard-graph", config={"responsive": True}),
        dcc.Graph(id="cohort-pie-chart", className="dashboard-graph", config={"responsive": True}),
        dcc.Graph(id="years-targeted-pie-chart", className="dashboard-graph", config={"responsive": True}),
        dcc.Graph(id="program-pie-chart", className="dashboard-graph", config={"responsive": True}),

        html.Div([
            html.Label("Filter Age of Conversion Pie Chart by Program Level:"),
            dcc.Checklist(
                id="age-pie-program-filter",
                options=[{"label": p, "value": p} for p in
                         ["Prov Dev 3", "Prov Dev 2", "Prov Dev 1", "Uncarded", "SC Carded"]],
                value=[],
                inline=True,
            )
        ], style={"marginBottom": "15px"}),

        dcc.Graph(id="age-conversion-pie-chart", className="dashboard-graph", config={"responsive": True}),
    ], className="dashboard-content", style={"padding": "0 24px", "maxWidth": "1400px", "margin": "0 auto"}),

    footer_component.render() if footer_component else html.Div(),
], style={"paddingBottom": "90px"})

if navbar_component:
    navbar_component.register_callbacks(app)

# ── Helpers ──────────────────────────────────────────────────────────────────
def _sports_label(selected_sports):
    if not selected_sports:
        return "No Sport Selected"
    if len(selected_sports) <= 3:
        return ", ".join(selected_sports)
    return f"{len(selected_sports)} sports"


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("year-filter", "options"),
    Output("year-filter", "value"),
    Input("sport-dropdown", "value"),
)
def update_year_dropdown(selected_sports):
    if not selected_sports:
        return [], []
    dff   = df[df['Sport'].isin(selected_sports)]
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
    Input("has-2026-checkbox", "value"),
    Input("year-filter", "value"),
    Input("age-pie-program-filter", "value"),
)
def update_graphs(selected_sports, filter_2026, selected_years, prog_filter):
    if not selected_sports:
        empty = go.Figure()
        msg   = html.Div("No sport(s) selected.", style={"padding": "8px"})
        return empty, msg, empty, empty, empty, empty, empty, empty

    dff = df[df['Sport'].isin(selected_sports)].copy()

    if "2026" in filter_2026:
        key_cols = ['First Name', 'Last Name', 'Sport']
        dff_year = dff.copy()
        dff_year['_year_num'] = pd.to_numeric(dff_year['Year'], errors='coerce')
        has_2026 = dff_year.groupby(key_cols)['_year_num'].transform(lambda s: s.eq(2026).any())
        dff = dff_year[has_2026].drop(columns=['_year_num']).copy()

    if selected_years:
        dff = dff[dff['Year'].isin(selected_years)]

    dff['DOB_parsed'] = pd.to_datetime(dff['Date of Birth'], errors='coerce')
    dff['BirthYear']  = dff['DOB_parsed'].dt.year

    # ── Time-series metrics ───────────────────────────────────────────────────
    grp = dff.groupby('Year', sort=True)

    unique_athletes  = grp.apply(
        lambda g: g[['First Name', 'Last Name']].drop_duplicates().shape[0]
    ).sort_index()
    converted        = grp['Convert Year'].apply(lambda col: col.eq('Y').sum()).sort_index()
    avg_targeted     = grp['Years Targeted'].mean().sort_index()
    conversion_rate  = (converted / unique_athletes * 100).fillna(0)

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=unique_athletes.index, y=unique_athletes.values,
        mode='lines+markers', name='Total Athletes', yaxis='y1',
    ))
    fig_ts.add_trace(go.Scatter(
        x=converted.index, y=converted.values,
        mode='lines+markers', name='Conversion Count', yaxis='y1',
    ))
    fig_ts.add_trace(go.Scatter(
        x=avg_targeted.index, y=avg_targeted.values,
        mode='lines+markers', name='Average Years Targeted', yaxis='y2',
        hovertemplate='%{y:.1f}',
    ))
    fig_ts.add_trace(go.Scatter(
        x=conversion_rate.index, y=conversion_rate.values,
        mode='lines+markers', name='Conversion Rate (%)', yaxis='y3',
        hovertemplate='%{y:.1f}%',
    ))
    fig_ts.update_layout(
        title=f"Time Series — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK,
        plot_bgcolor=COLOR_DARK_GRAY,
        font=dict(color=COLOR_WHITE),
        title_font=dict(color=COLOR_WHITE, size=16),
        yaxis=dict(title="Count of Athletes", showgrid=True, gridcolor="#444"),
        yaxis2=dict(title="Average Years Targeted", overlaying="y", side="right",
                    anchor="free", position=1.0, showgrid=True, gridcolor="#444"),
        yaxis3=dict(title="Conversion Rate (%)", overlaying="y", side="right",
                    anchor="free", position=0.95, tickformat=".0f", gridcolor="#444"),
        xaxis=dict(title="Year", tickmode="linear", dtick=1, tickformat=".0f", gridcolor="#444"),
        legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
                    bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2),
        margin=dict(l=60, r=120, t=60, b=100),
        hovermode='x unified',
    )
    fig_ts.data[0].line.color = VIBRANT_PALETTE[0]
    fig_ts.data[0].line.width = 3
    fig_ts.data[1].line.color = VIBRANT_PALETTE[1]
    fig_ts.data[1].line.width = 3
    fig_ts.data[2].marker.color = VIBRANT_PALETTE[2]
    fig_ts.data[2].line.color   = VIBRANT_PALETTE[2]
    fig_ts.data[2].line.width   = 3
    fig_ts.data[3].line.color   = VIBRANT_PALETTE[3]
    fig_ts.data[3].line.width   = 3

    # ── Summary metrics ────────────────────────────────────────────────────────
    dff_age = dff[dff['BirthYear'].notna() & dff['Year'].notna()]

    per_ath_years = (
        dff
        .groupby(['First Name', 'Last Name', 'Sport'])['Years Targeted']
        .max()
        .reset_index(name='years_targeted')
    )
    avg_years_targeted = per_ath_years['years_targeted'].mean() if not per_ath_years.empty else float('nan')
    n_years            = len(per_ath_years)

    per_ath_years_range = (
        dff
        .groupby(['First Name', 'Last Name', 'Sport'], as_index=False)
        .agg(first_year=('Year', 'min'), last_year=('Year', 'max'))
    )
    per_ath_dob = (
        dff_age
        .groupby(['First Name', 'Last Name', 'Sport'], as_index=False)
        .agg(birth_year=('BirthYear', 'first'))
    )
    per_ath = per_ath_years_range.merge(per_ath_dob, on=['First Name', 'Last Name', 'Sport'], how='inner')
    per_ath['age_first'] = per_ath['first_year'].astype(int) - per_ath['birth_year'].astype(int)
    per_ath['age_last']  = per_ath['last_year'].astype(int)  - per_ath['birth_year'].astype(int)

    if not per_ath.empty:
        avg_age_first = per_ath['age_first'].mean()
        avg_age_last  = per_ath['age_last'].mean()
        n_ath_age     = len(per_ath)
    else:
        avg_age_first = avg_age_last = float('nan')
        n_ath_age     = 0

    avg_conv      = converted.mean()
    avg_conv_rate = conversion_rate.mean()

    # CSS metrics
    per_ath_css = (
        dff
        .groupby(['First Name', 'Last Name'])
        .apply(lambda g: (g['CSS'] == 'YES').sum())
        .reset_index(name='css_count')
    )
    n_css_athletes   = int((per_ath_css['css_count'] > 0).sum())
    css_only         = per_ath_css[per_ath_css['css_count'] > 0]
    avg_years_in_css = css_only['css_count'].mean() if not css_only.empty else float('nan')
    n_css            = len(css_only)

    # CSS → conversion gap
    program_to_level = {'Prov Dev 3': 1, 'Prov Dev 2': 2, 'Prov Dev 1': 3, 'Uncarded': 4, 'SC Carded': 5}
    css_to_convert_gaps = []
    for athlete_name in dff['Full_Name'].unique():
        ath = dff[dff['Full_Name'] == athlete_name].sort_values('Year')
        css_years = ath[ath['CSS'] == 'YES']['Year']
        if css_years.empty:
            continue
        first_css = css_years.iloc[0]
        ath['prog_level'] = ath['Program'].map(program_to_level)
        high = ath[ath['prog_level'] >= 2]
        if high.empty:
            continue
        css_to_convert_gaps.append(int(high.iloc[0]['Year']) - int(first_css))

    if css_to_convert_gaps:
        avg_css_to_convert_gap = sum(css_to_convert_gaps) / len(css_to_convert_gaps)
        n_css_to_convert       = len(css_to_convert_gaps)
    else:
        avg_css_to_convert_gap = float('nan')
        n_css_to_convert       = 0

    summary_rows = [
        html.Tr([html.Td("Avg. Conversions"),            html.Td(f"{avg_conv:.1f}")]),
        html.Tr([html.Td("Avg. Conversion Rate"),        html.Td(f"{avg_conv_rate:.1f}%")]),
        html.Tr([html.Td("Avg. Age — First Targeted"),   html.Td(f"{avg_age_first:.1f} yrs" if n_ath_age else "—")]),
        html.Tr([html.Td("Avg. Age — Last Targeted"),    html.Td(f"{avg_age_last:.1f} yrs"  if n_ath_age else "—")]),
        html.Tr([html.Td("Avg. Years Targeted (per athlete)"), html.Td(f"{avg_years_targeted:.2f}" if n_years else "—")]),
        html.Tr([html.Td("CSS Athletes Count"),          html.Td(f"{n_css_athletes}" if n_css_athletes else "—")]),
        html.Tr([html.Td("Avg. Years in CSS (CSS athletes only)"), html.Td(f"{avg_years_in_css:.2f}" if n_css else "—")]),
        html.Tr([html.Td("CSS Converters Count (CSS → Prov Dev 2+)"), html.Td(f"{n_css_to_convert}" if n_css_to_convert else "—")]),
        html.Tr([html.Td("Avg. Years: CSS to Level Up (CSS athletes only)"), html.Td(f"{avg_css_to_convert_gap:.2f} yrs" if n_css_to_convert else "—")]),
    ]
    split_idx = (len(summary_rows) + 1) // 2
    left_rows = summary_rows[:split_idx]
    right_rows = summary_rows[split_idx:]

    summary_table = html.Div(
        [
            html.Table([
                html.Thead([html.Tr([html.Th("Metric"), html.Th("Average")])]),
                html.Tbody(left_rows),
            ], className="conversion-summary-table"),
            html.Table([
                html.Thead([html.Tr([html.Th("Metric"), html.Th("Average")])]),
                html.Tbody(right_rows),
            ], className="conversion-summary-table"),
        ],
        className="summary-grid",
        style={
            "gap": "12px",
            "alignItems": "start",
        },
    )

    # ── Program-level conversion lines ────────────────────────────────────────
    stack_order = ['Prov Dev 3', 'Prov Dev 2', 'Prov Dev 1', 'Uncarded', 'SC Carded']

    prog_year_conv = (
        dff[dff['Convert Year'] == 'Y']
        .groupby(['Year', 'Program'])
        .size()
        .reset_index(name='Count')
    )
    prog_line_pivot = (
        prog_year_conv
        .pivot(index='Year', columns='Program', values='Count')
        .fillna(0)
        .sort_index()
    )
    fig_program_lines = go.Figure()
    for idx, program in enumerate(stack_order):
        if program in prog_line_pivot.columns:
            fig_program_lines.add_trace(go.Scatter(
                x=prog_line_pivot.index, y=prog_line_pivot[program],
                mode='lines+markers', name=program,
                line=dict(color=VIBRANT_PALETTE[idx % len(VIBRANT_PALETTE)], width=3),
                marker=dict(size=8),
                hovertemplate='%{y:.0f}',
            ))
    fig_program_lines.update_layout(
        title=f"Converted Athletes by Program Level — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK, plot_bgcolor=COLOR_DARK_GRAY,
        font=dict(color=COLOR_WHITE), title_font=dict(color=COLOR_WHITE, size=16),
        xaxis=dict(title='Year', tickmode='linear', dtick=1, tickformat='.0f', gridcolor='#444'),
        yaxis=dict(title='Conversion Count', gridcolor='#444'),
        legend=dict(orientation='h', y=-0.2, bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2),
        margin=dict(l=50, r=50, t=60, b=60),
    )

    # ── Program composition stacked bar ───────────────────────────────────────
    program_year_data = (
        dff
        .groupby(['Year', 'Program'])
        .size()
        .reset_index(name='Count')
    )
    program_pivot = (
        program_year_data
        .pivot(index='Year', columns='Program', values='Count')
        .fillna(0)
        .sort_index()
    )
    fig_bar = go.Figure()
    for idx, program in enumerate(stack_order):
        if program in program_pivot.columns:
            fig_bar.add_trace(go.Bar(
                x=program_pivot.index, y=program_pivot[program],
                name=program,
                marker=dict(color=VIBRANT_PALETTE[idx % len(VIBRANT_PALETTE)]),
            ))
    fig_bar.update_layout(
        barmode='stack',
        title=f"Program Composition by Year — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK, plot_bgcolor=COLOR_DARK_GRAY,
        font=dict(color=COLOR_WHITE), title_font=dict(color=COLOR_WHITE, size=16),
        xaxis=dict(title='Year', tickmode='linear', dtick=1, tickformat='.0f', gridcolor='#444'),
        yaxis=dict(title='Athlete Count', gridcolor='#444'),
        legend=dict(
            orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
            bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2,
        ),
        margin=dict(l=50, r=50, t=60, b=40),
    )

    # ── Cohort scope for pies ──────────────────────────────────────────────────
    dff_pies = dff

    # Cohort conversion pie
    conv_by_athlete = (
        dff_pies
        .groupby(['First Name', 'Last Name'])['Convert Year']
        .apply(lambda col: col.eq('Y').any())
    )
    num_converted = int(conv_by_athlete.sum())
    num_never     = int(conv_by_athlete.shape[0] - num_converted)

    fig_pie = go.Figure(data=[go.Pie(
        labels=["Career Converter", "Never Converted"],
        values=[num_converted, num_never],
        hole=0.3, sort=False,
        marker=dict(colors=[VIBRANT_PALETTE[0], VIBRANT_PALETTE[1]]),
    )])
    fig_pie.update_layout(
        title_text=f"Cohort Conversion — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK, font=dict(color=COLOR_WHITE),
        title_font=dict(color=COLOR_WHITE, size=16),
        legend=dict(
            traceorder='normal', orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
            bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2, font=dict(color=COLOR_WHITE),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
    )

    # Years-targeted dispersion pie
    years_by_athlete = dff_pies.groupby(['First Name', 'Last Name'])['Years Targeted'].max()
    counts  = years_by_athlete.value_counts().sort_index()
    fig_disp = go.Figure(data=[go.Pie(
        labels=[f"{yr} yr" for yr in counts.index],
        values=counts.values,
        hole=0.3, sort=False,
        marker=dict(colors=VIBRANT_PALETTE),
    )])
    fig_disp.update_layout(
        title_text=f"Distribution of Years Targeted — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK, font=dict(color=COLOR_WHITE),
        title_font=dict(color=COLOR_WHITE, size=16),
        legend=dict(
            traceorder='normal', orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
            bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2, font=dict(color=COLOR_WHITE),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
    )

    # Program-level conversion pie
    prog_conv = (
        dff_pies[dff_pies['Convert Year'] == 'Y']
        .groupby('Program')
        .size()
        .sort_index()
    )
    program_colors = {
        'Prov Dev 3': VIBRANT_PALETTE[0],
        'Prov Dev 2': VIBRANT_PALETTE[1],
        'Prov Dev 1': VIBRANT_PALETTE[2],
        'Uncarded':   VIBRANT_PALETTE[3],
        'SC Carded':  VIBRANT_PALETTE[4],
    }
    colors = [program_colors.get(p, VIBRANT_PALETTE[0]) for p in prog_conv.index]
    fig_prog = go.Figure(data=[go.Pie(
        labels=prog_conv.index, values=prog_conv.values,
        hole=0.3, sort=False,
        marker=dict(colors=colors),
    )])
    fig_prog.update_layout(
        title_text=f"Conversion by Level — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK, font=dict(color=COLOR_WHITE),
        title_font=dict(color=COLOR_WHITE, size=16),
        legend=dict(
            traceorder='normal', orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
            bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2, font=dict(color=COLOR_WHITE),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
    )

    # Age-at-conversion pie
    conv_rows = dff_pies[dff_pies['Convert Year'] == 'Y'].copy()
    if prog_filter:
        conv_rows = conv_rows[conv_rows['Program'].isin(prog_filter)]
    conv_rows = conv_rows[conv_rows['BirthYear'].notna()]
    conv_rows['AgeAtConvert'] = conv_rows['Year'].astype(int) - conv_rows['BirthYear']
    age_counts = conv_rows.groupby('AgeAtConvert').size().sort_index()

    if age_counts.empty:
        fig_age_pie = go.Figure()
        fig_age_pie.update_layout(
            title_text="No data for selected filters",
            template="plotly_dark",
            paper_bgcolor=COLOR_BLACK, font=dict(color=COLOR_WHITE),
            title_font=dict(color=COLOR_WHITE, size=16),
            margin=dict(l=40, r=40, t=50, b=40),
        )
    else:
        age_colors = [VIBRANT_PALETTE[i % len(VIBRANT_PALETTE)] for i in range(len(age_counts))]
        fig_age_pie = go.Figure(data=[go.Pie(
            labels=[f"{int(a)} yr" for a in age_counts.index],
            values=age_counts.values,
            hole=0.3, sort=False,
            marker=dict(colors=age_colors),
        )])
        fig_age_pie.update_layout(
            title_text=f"Age at Conversion — {_sports_label(selected_sports)}",
            template="plotly_dark",
            paper_bgcolor=COLOR_BLACK, font=dict(color=COLOR_WHITE),
            title_font=dict(color=COLOR_WHITE, size=16),
            legend=dict(
                orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
                bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2, font=dict(color=COLOR_WHITE),
            ),
            margin=dict(l=40, r=40, t=50, b=40),
        )

    return (fig_ts, summary_table, fig_program_lines, fig_bar,
            fig_pie, fig_disp, fig_prog, fig_age_pie)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Local dev only — these vars are not used by Posit Connect (gunicorn handles binding)
    _host     = os.environ.get("APP_HOST", "127.0.0.1")
    _port     = int(os.environ.get("APP_PORT", "8050"))
    _debug    = os.environ.get("DEV_MODE", "false").lower() == "true"
    app.run(debug=_debug, host=_host, port=_port)
