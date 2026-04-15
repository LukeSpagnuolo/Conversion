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
from dash import dcc, html, Input, Output, State
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

external_scripts = [
    "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
]

app = dash.Dash(
    __name__,
    server=auth.server,
    external_stylesheets=external_stylesheets,
    external_scripts=external_scripts,
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

VIA_SPORT_REPORT_ORDER = [
    "Alpine Skiing",
    "Artistic Swimming",
    "Athletics",
    "Basketball",
    "Biathlon",
    "Canoe Kayak",
    "Cross Country Skiing",
    "Curling",
    "Cycling",
    "Field Hockey",
    "Figure Skating",
    "Freestyle Skiing",
    "Wrestling",
    "Rugby",
    "Sailing",
    "Snowboard",
    "Swimming",
    "Triathlon",
    "Volleyball",
    "Wheelchair Basketball",
    "Artistic Gymnastics",
    "Judo",
    "Wheelchair Athletics",
    "Wheelchair Rugby",
    "Wheelchair Tennis",
    "Diving",
    "Rowing",
]

REPORT_SPORT_LABELS = {
    "Canoe Kayak": "Canoe/Kayak",
    "Artistic Gymnastics": "Gymnastics",
}

PROGRAM_LEVELS = {
    "Prov Dev 3": 1,
    "Prov Dev 2": 2,
    "Prov Dev 1": 3,
    "Uncarded": 4,
    "SC Carded": 5,
}

NATIONAL_SOURCE_LEVELS = {"Prov Dev 3", "Prov Dev 2", "Prov Dev 1"}
NATIONAL_TARGET_LEVELS = {"Uncarded", "SC Carded"}

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    navbar_component.render() if navbar_component else html.Div(),

    html.Div(id="main-content", children=[
        dbc.Row([
            dbc.Col([
                dbc.Button("⬇ Download CSV", id="btn-download-csv", color="primary", className="me-2"),
                dbc.Button("⬇ Download Via Sport CSV", id="btn-download-via-sport-csv", color="success", className="me-2"),
                dbc.Button("🖨 Download PDF", id="btn-download-pdf", color="secondary"),
                dcc.Download(id="download-csv"),
                dcc.Download(id="download-via-sport-csv"),
                html.Div(id="pdf-dummy", style={"display": "none"}),
            ], style={"textAlign": "right"}),
        ], className="mb-3"),

        html.Div(id="pdf-content", children=[
        # Filters
        html.Div(id="pdf-filters", children=[
        dbc.Row([
            dbc.Col([
                html.Label("Select Sport(s):"),
                dcc.Dropdown(
                    id="sport-dropdown",
                    options=sport_options,
                    value=[],
                    multi=True,
                    clearable=True,
                    style={"width": "100%"},
                )
            ], xs=12, md=6),
            dbc.Col([
                html.Label("Select Years:"),
                dcc.Dropdown(
                    id="year-filter",
                    multi=True,
                    placeholder="Select one or more years",
                    style={"width": "100%"},
                )
            ], xs=12, md=6),
        ], className="mb-4"),

        html.Div([
            dcc.Checklist(
                id="has-2026-checkbox",
                options=[{"label": "Only athletes with 2026 as one of their years", "value": "2026"}],
                value=[],
                inputStyle={"margin-right": "10px"},
            )
        ], style={"marginBottom": "20px"}),
        ]),  # end pdf-filters

        # Charts & tables
        dcc.Graph(id="time-series-graph", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "500px"}),
        html.Div(id="conversion-summary"),
        html.Div(id="via-sport-report", style={"marginBottom": "18px"}),
        dcc.Graph(id="program-lines-graph", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
        dcc.Graph(id="program-composition-bar-chart", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
        dcc.Graph(id="cohort-pie-chart", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
        dcc.Graph(id="years-targeted-pie-chart", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
        dcc.Graph(id="program-pie-chart", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),

        html.Div(id="pdf-age-filter", children=[
            html.Label("Filter Age of Conversion Pie Chart by Program Level:"),
            dcc.Checklist(
                id="age-pie-program-filter",
                options=[{"label": p, "value": p} for p in
                         ["Prov Dev 3", "Prov Dev 2", "Prov Dev 1", "Uncarded", "SC Carded"]],
                value=[],
                inline=True,
            )
        ], style={"marginBottom": "15px"}),

        dcc.Graph(id="age-conversion-pie-chart", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
        ]),  # end pdf-content
    ], style={"padding": "0 12px", "maxWidth": "1400px", "margin": "0 auto", "overflowX": "hidden"}),

    footer_component.render() if footer_component else html.Div(),
], style={"paddingBottom": "90px"})

if navbar_component:
    navbar_component.register_callbacks(app)

app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return window.dash_clientside.no_update;
        var ids = [
            'pdf-filters',
            'conversion-summary',
            'via-sport-report',
            'time-series-graph',
            'program-lines-graph',
            'program-composition-bar-chart',
            'cohort-pie-chart',
            'years-targeted-pie-chart',
            'program-pie-chart',
            'pdf-age-filter',
            'age-conversion-pie-chart'
        ];
        var els = ids.map(function(id) { return document.getElementById(id); })
                     .filter(function(el) { return el !== null; });
        var pdf = new jspdf.jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        var pageW = pdf.internal.pageSize.getWidth();
        var pageH = pdf.internal.pageSize.getHeight();
        var margin = 8;
        var gap = 4;
        var usableW = pageW - 2 * margin;
        var usableH = pageH - 2 * margin;
        var cursorY = margin;
        var isFirst = true;
        els.reduce(function(promise, el) {
            return promise.then(function() {
                return html2canvas(el, { scale: 2, useCORS: true, backgroundColor: '#1a1a1a' }).then(function(canvas) {
                    if (canvas.width === 0 || canvas.height === 0) return;
                    var imgData = canvas.toDataURL('image/png');
                    var imgW = usableW;
                    var imgH = (canvas.height * imgW) / canvas.width;
                    /* if taller than a full page, scale down to fit */
                    if (imgH > usableH) {
                        imgH = usableH;
                        imgW = (canvas.width * imgH) / canvas.height;
                    }
                    var x = margin + (usableW - imgW) / 2;
                    /* new page if not enough vertical space */
                    if (!isFirst && cursorY + imgH > pageH - margin) {
                        pdf.addPage();
                        cursorY = margin;
                    }
                    pdf.addImage(imgData, 'PNG', x, cursorY, imgW, imgH);
                    cursorY += imgH + gap;
                    isFirst = false;
                });
            });
        }, Promise.resolve()).then(function() {
            pdf.save('conversion_report.pdf');
        });
        return window.dash_clientside.no_update;
    }
    """,
    Output("pdf-dummy", "children"),
    Input("btn-download-pdf", "n_clicks"),
    prevent_initial_call=True,
)

# ── Helpers ──────────────────────────────────────────────────────────────────
def _sports_label(selected_sports):
    if not selected_sports:
        return "No Sport Selected"
    if len(selected_sports) <= 3:
        return ", ".join(selected_sports)
    return f"{len(selected_sports)} sports"


def _sport_display_name(sport_name):
    return REPORT_SPORT_LABELS.get(sport_name, sport_name)


def _athlete_national_conversion_year(athlete_df):
    sorted_df = athlete_df.copy()
    sorted_df["_program_level"] = sorted_df["Program"].astype(str).str.strip().map(PROGRAM_LEVELS)
    sorted_df = sorted_df.sort_values(["_year_num", "_program_level"], kind="stable")
    previous_level = None
    previous_year = None
    for _, row in sorted_df.iterrows():
        current_year = row.get("_year_num")
        if pd.isna(current_year):
            continue
        current_program = str(row.get("Program", "")).strip()
        current_level = PROGRAM_LEVELS.get(current_program)
        if (
            previous_level in NATIONAL_SOURCE_LEVELS
            and current_level in NATIONAL_TARGET_LEVELS
            and previous_year is not None
            and int(current_year) > int(previous_year)
        ):
            return int(current_year)
        previous_level = current_level
        previous_year = current_year
    return None


def _build_via_sport_report_df(dff):
    if dff.empty:
        return pd.DataFrame()

    report_df = dff.copy()
    report_df["DOB_parsed"] = pd.to_datetime(report_df["Date of Birth"], errors="coerce")
    report_df["BirthYear"] = report_df["DOB_parsed"].dt.year
    report_df["_year_num"] = pd.to_numeric(report_df["Year"], errors="coerce")
    report_df = report_df[report_df["_year_num"].notna()].copy()

    if report_df.empty:
        return pd.DataFrame()

    latest_year = int(report_df["_year_num"].max())
    past_four_years_start = latest_year - 3

    athlete_rows = []
    group_cols = ["Sport", "First Name", "Last Name"]
    for (sport, first_name, last_name), athlete_df in report_df.groupby(group_cols, sort=False):
        athlete_years = athlete_df["_year_num"].dropna().astype(int)
        if athlete_years.empty:
            continue

        birth_year = athlete_df["BirthYear"].dropna().iloc[0] if athlete_df["BirthYear"].notna().any() else None
        gender_series = athlete_df["Gender"].dropna().astype(str).str.strip()
        gender = gender_series.iloc[0] if not gender_series.empty else ""
        years_targeted = pd.to_numeric(athlete_df["Years Targeted"], errors="coerce").max()
        converted_any = athlete_df["Convert Year"].astype(str).str.upper().eq("Y").any()

        recent_years = athlete_df[athlete_df["_year_num"].between(past_four_years_start, latest_year)]
        converted_recent = recent_years["Convert Year"].astype(str).str.upper().eq("Y").any()

        national_conversion_year = _athlete_national_conversion_year(athlete_df)
        national_recent = national_conversion_year is not None and past_four_years_start <= national_conversion_year <= latest_year

        age_value = float("nan")
        if birth_year is not None:
            age_value = int(athlete_years.max()) - int(birth_year)

        athlete_rows.append({
            "Sport": sport,
            "Gender": gender,
            "Age": age_value,
            "Years Targeted": years_targeted,
            "Converted Any": converted_any,
            "Converted Recent": converted_recent,
            "National Recent": national_recent,
        })

    athlete_summary = pd.DataFrame(athlete_rows)
    if athlete_summary.empty:
        return pd.DataFrame()

    report_rows = []
    selected_report_sports = [sport for sport in VIA_SPORT_REPORT_ORDER if sport in athlete_summary["Sport"].unique()]
    for sport in selected_report_sports:
        sport_df = athlete_summary[athlete_summary["Sport"] == sport].copy()
        enrolled = len(sport_df)
        converted_recent_count = int(sport_df["Converted Recent"].sum())
        converted_total = int(sport_df["Converted Any"].sum())
        national_recent_count = int(sport_df["National Recent"].sum())
        avg_years_targeted = sport_df["Years Targeted"].dropna().astype(float).mean()
        avg_age = sport_df["Age"].dropna().astype(float).mean()
        gender_counts = sport_df["Gender"].replace({"nan": ""}).value_counts()
        gender_text = f"{int(gender_counts.get('F', 0))}/{int(gender_counts.get('M', 0))}/{int(gender_counts.get('X', 0))}"

        report_rows.append({
            "Sport": _sport_display_name(sport),
            "Total athlete count in cohort": enrolled,
            "Conversion in past 4 years": converted_recent_count,
            "Percent of total enrolled converted in past 4 years": round((converted_recent_count / enrolled * 100), 1) if enrolled else None,
            "Conversion": converted_total,
            "Conversion to national past 4 years": national_recent_count,
            "Conversion to national percentage past 4 years": round((national_recent_count / enrolled * 100), 1) if enrolled else None,
            "Average years targeted": round(float(avg_years_targeted), 2) if pd.notna(avg_years_targeted) else None,
            "Average age": round(float(avg_age), 1) if pd.notna(avg_age) else None,
            "Gender numbers (F/M/X)": gender_text,
        })

    report_output = pd.DataFrame(report_rows)
    report_output.attrs["latest_year"] = latest_year
    return report_output


def _build_via_sport_report(dff):
    report_df = _build_via_sport_report_df(dff)
    if report_df.empty:
        return html.Div("No sport report data for the current filters.", style={"padding": "8px"})

    latest_year = report_df.attrs.get("latest_year")

    if report_df.empty:
        return html.Div("No selected sports match the via sport report list.", style={"padding": "8px"})

    report_table = html.Div(
        html.Table(
            [
                html.Thead([
                    html.Tr([
                        html.Th("Sport"),
                        html.Th("Total athlete count in cohort"),
                        html.Th("Conversion in past 4 years"),
                        html.Th("Percent of total enrolled converted in past 4 years"),
                        html.Th("Conversion"),
                        html.Th("Conversion to national past 4 years"),
                        html.Th("Conversion to national % past 4 years"),
                        html.Th("Average years targeted"),
                        html.Th("Average age"),
                        html.Th("Gender (F/M/X)"),
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(row["Sport"]),
                        html.Td(row["Total athlete count in cohort"]),
                        html.Td(row["Conversion in past 4 years"]),
                        html.Td(f"{row['Percent of total enrolled converted in past 4 years']:.1f}%" if row["Percent of total enrolled converted in past 4 years"] is not None else "—"),
                        html.Td(row["Conversion"]),
                        html.Td(row["Conversion to national past 4 years"]),
                        html.Td(f"{row['Conversion to national percentage past 4 years']:.1f}%" if row["Conversion to national percentage past 4 years"] is not None else "—"),
                        html.Td(f"{row['Average years targeted']:.2f}" if row["Average years targeted"] is not None else "—"),
                        html.Td(f"{row['Average age']:.1f}" if row["Average age"] is not None else "—"),
                        html.Td(row["Gender numbers (F/M/X)"]),
                    ])
                    for _, row in report_df.iterrows()
                ]),
            ],
            className="conversion-summary-table",
        ),
        style={"overflowX": "auto"},
    )

    caption = html.Div(
        f"Past 4 years are calculated from the latest year in the current filtered view ({latest_year})." if latest_year is not None else "Past 4 years are calculated from the current filtered view.",
        style={"padding": "0 8px 8px 8px", "fontSize": "0.9rem", "opacity": 0.85},
    )

    return html.Div([
        html.H3("Via Sport Report", style={"margin": "8px 0 6px 0"}),
        caption,
        report_table,
    ])


def _via_sport_report_csv(dff):
    report_df = _build_via_sport_report_df(dff)
    if report_df.empty:
        return None
    return report_df


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("download-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    State("sport-dropdown", "value"),
    State("has-2026-checkbox", "value"),
    State("year-filter", "value"),
    prevent_initial_call=True,
)
def download_filtered_csv(n_clicks, selected_sports, filter_2026, selected_years):
    if not selected_sports:
        return dash.no_update
    dff = df[df['Sport'].isin(selected_sports)].copy()
    if filter_2026 and "2026" in filter_2026:
        key_cols = ['First Name', 'Last Name', 'Sport']
        dff['_year_num'] = pd.to_numeric(dff['Year'], errors='coerce')
        has_2026 = dff.groupby(key_cols)['_year_num'].transform(lambda s: s.eq(2026).any())
        dff = dff[has_2026].drop(columns=['_year_num']).copy()
    if selected_years:
        dff = dff[dff['Year'].isin(selected_years)]
    return dcc.send_data_frame(dff.to_csv, "conversion_data_filtered.csv", index=False)


@app.callback(
    Output("download-via-sport-csv", "data"),
    Input("btn-download-via-sport-csv", "n_clicks"),
    State("sport-dropdown", "value"),
    State("has-2026-checkbox", "value"),
    State("year-filter", "value"),
    prevent_initial_call=True,
)
def download_via_sport_csv(n_clicks, selected_sports, filter_2026, selected_years):
    if not selected_sports:
        return dash.no_update

    dff = df[df['Sport'].isin(selected_sports)].copy()

    if filter_2026 and "2026" in filter_2026:
        key_cols = ['First Name', 'Last Name', 'Sport']
        dff['_year_num'] = pd.to_numeric(dff['Year'], errors='coerce')
        has_2026 = dff.groupby(key_cols)['_year_num'].transform(lambda s: s.eq(2026).any())
        dff = dff[has_2026].drop(columns=['_year_num']).copy()

    if selected_years:
        dff = dff[dff['Year'].isin(selected_years)]

    report_df = _via_sport_report_csv(dff)
    if report_df is None or report_df.empty:
        return dash.no_update

    return dcc.send_data_frame(report_df.to_csv, "via_sport_report.csv", index=False)


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
    Output("via-sport-report", "children"),
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
        return empty, msg, html.Div(), empty, empty, empty, empty, empty, empty

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

    via_sport_report = _build_via_sport_report(dff)

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
        yaxis2=dict(title="Avg Yrs Targeted", overlaying="y", side="right",
                    anchor="x", showgrid=False),
        yaxis3=dict(title="Conv. Rate (%)", overlaying="y", side="right",
                    anchor="free", position=1.0, tickformat=".0f", showgrid=False),
        xaxis=dict(title="Year", tickmode="linear", dtick=1, tickformat=".0f", gridcolor="#444",
                   domain=[0, 0.85]),
        legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
                    bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2),
        margin=dict(l=50, r=70, t=50, b=100),
        height=500,
        hovermode='x unified',
        autosize=True,
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

    summary_table = dbc.Row(
        [
            dbc.Col(
                html.Table([
                    html.Thead([html.Tr([html.Th("Metric"), html.Th("Average")])]),
                    html.Tbody(left_rows),
                ], className="conversion-summary-table"),
                xs=12, md=6,
            ),
            dbc.Col(
                html.Table([
                    html.Thead([html.Tr([html.Th("Metric"), html.Th("Average")])]),
                    html.Tbody(right_rows),
                ], className="conversion-summary-table"),
                xs=12, md=6,
            ),
        ],
        className="g-3 mb-3",
        align="start",
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
        margin=dict(l=40, r=30, t=50, b=60),
        height=400,
        autosize=True,
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
        margin=dict(l=40, r=30, t=50, b=40),
        height=400,
        autosize=True,
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
        margin=dict(l=30, r=30, t=50, b=40),
        height=400,
        autosize=True,
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
        margin=dict(l=30, r=30, t=50, b=40),
        height=400,
        autosize=True,
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
        margin=dict(l=30, r=30, t=50, b=40),
        height=400,
        autosize=True,
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
            margin=dict(l=30, r=30, t=50, b=40),
            height=400,
            autosize=True,
        )
    else:
        age_colors = [VIBRANT_PALETTE[i % len(VIBRANT_PALETTE)] for i in range(len(age_counts))]
        _total = age_counts.sum()
        _pct_text = [
            f"{int(a)} yr<br>{v/_total*100:.1f}%" if v / _total * 100 >= 2 else ""
            for a, v in zip(age_counts.index, age_counts.values)
        ]
        fig_age_pie = go.Figure(data=[go.Pie(
            labels=[f"{int(a)} yr" for a in age_counts.index],
            values=age_counts.values,
            text=_pct_text,
            textinfo='text',
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
            margin=dict(l=30, r=30, t=50, b=40),
            height=400,
            autosize=True,
        )

        return (fig_ts, summary_table, via_sport_report, fig_program_lines, fig_bar,
            fig_pie, fig_disp, fig_prog, fig_age_pie)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Local dev only — these vars are not used by Posit Connect (gunicorn handles binding)
    _host     = os.environ.get("APP_HOST", "127.0.0.1")
    _port     = int(os.environ.get("APP_PORT", "8050"))
    _debug    = os.environ.get("DEV_MODE", "false").lower() == "true"
    app.run(debug=_debug, host=_host, port=_port)
