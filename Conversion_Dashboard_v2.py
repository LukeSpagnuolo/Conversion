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
df["_year_num"] = pd.to_numeric(df["Year"], errors="coerce")
df["DOB_parsed"] = pd.to_datetime(df["Date of Birth"], errors="coerce")
df["BirthYear"] = df["DOB_parsed"].dt.year
df["Full_Name"] = df["First Name"].astype(str).str.strip() + " " + df["Last Name"].astype(str).str.strip()
df["_program_level"] = df["Program"].astype(str).str.strip().map({
    "Prov Dev 3": 1,
    "Prov Dev 2": 2,
    "Prov Dev 1": 3,
    "Uncarded": 4,
    "SC Carded": 5,
})

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

NATIONAL_SOURCE_LEVELS = {1, 2, 3}
NATIONAL_TARGET_LEVELS = {4, 5}

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    navbar_component.render() if navbar_component else html.Div(),
    html.Div(id="global-loading-bar", className="global-loading-bar"),
    dcc.Download(id="download-via-sport-csv"),
    html.Div(id="main-content", children=[
        dcc.Tabs(id="dashboard-tabs", value="dashboard-tab", children=[
            dcc.Tab(label="Dashboard", value="dashboard-tab", children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Button("⬇ Download CSV", id="btn-download-csv", color="primary", className="me-2"),
                        dbc.Button("🖨 Download PDF", id="btn-download-pdf", color="secondary"),
                        dcc.Download(id="download-csv"),
                        html.Div(id="pdf-dummy", style={"display": "none"}),
                    ], style={"textAlign": "right"}),
                ], className="mb-3"),

                html.Div(id="pdf-content", children=[
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

                html.Div([
                    dcc.Checklist(
                        id="css-checkbox",
                        options=[{"label": "Only athletes with CSS = YES at any point in their history", "value": "css"}],
                        value=[],
                        inputStyle={"margin-right": "10px"},
                    )
                ], style={"marginBottom": "20px"}),
                ]),

                dcc.Graph(id="time-series-graph", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "500px"}),
                html.Div(id="conversion-summary"),
                html.Div(id="via-sport-report", style={"marginBottom": "18px"}),
                dcc.Graph(id="program-lines-graph", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
                dcc.Graph(id="provincial-to-national-bar-chart", config={"responsive": True}, style={"width": "100%", "minWidth": 0, "height": "400px"}),
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
                ]),
            ]),
            dcc.Tab(label="All Sports Table", value="all-sports-tab", children=[
                html.Div([
                    html.P("Generate the full via sport report across all sports and all data."),
                    dbc.Button("Generate All Sports Table", id="btn-generate-all-sports-table", color="danger", className="me-2 mb-3"),
                    dbc.Button("⬇ Download Via Sport CSV", id="btn-download-via-sport-csv", color="success", className="mb-3"),
                    dcc.Loading(html.Div(id="all-sports-table-output"), type="dot"),
                ], style={"padding": "16px 0"}),
            ]),
        ])
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
            'provincial-to-national-bar-chart',
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


def _sport_sort_key(sport_name):
    try:
        return VIA_SPORT_REPORT_ORDER.index(sport_name)
    except ValueError:
        return len(VIA_SPORT_REPORT_ORDER)


def _filter_dashboard_df(selected_sports, filter_2026, filter_css, selected_years):
    dff = df[df['Sport'].isin(selected_sports)].copy()

    if filter_2026 and "2026" in filter_2026:
        has_2026 = dff.groupby('Full_Name')['_year_num'].transform(lambda s: s.eq(2026).any())
        dff = dff[has_2026].copy()

    if filter_css and "css" in filter_css:
        key_cols = ['First Name', 'Last Name', 'Sport']
        has_css_yes = dff.groupby(key_cols)['CSS'].transform(
            lambda s: s.astype(str).str.upper().eq("YES").any()
        )
        dff = dff[has_css_yes].copy()

    if selected_years:
        dff = dff[dff['Year'].isin(selected_years)]

    return dff


def _athlete_national_conversion_year(athlete_df):
    if athlete_df.empty:
        return None

    working = athlete_df.copy()
    working = working[working["_year_num"].notna()].copy()
    if working.empty:
        return None

    # Per year, keep:
    # - the highest program level reached in that year
    # - whether that year is flagged as a conversion year at national level (4/5)
    by_year = (
        working
        .groupby("_year_num", as_index=False)
        .agg(
            year_best_level=("_program_level", "max"),
            national_conversion_year=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()),
        )
        .sort_values("_year_num")
    )

    # Keep only years where conversion happened and year level is national (4/5)
    national_candidates = by_year[
        by_year["national_conversion_year"]
        & by_year["year_best_level"].isin(NATIONAL_TARGET_LEVELS)
    ]

    if national_candidates.empty:
        return None

    year_to_level = dict(zip(by_year["_year_num"].astype(int), by_year["year_best_level"]))

    for _, row in national_candidates.iterrows():
        year = int(row["_year_num"])
        previous_level = year_to_level.get(year - 1)
        if previous_level in NATIONAL_SOURCE_LEVELS:
            return year

    return None


def _build_via_sport_report_df(dff):
    if dff.empty:
        return pd.DataFrame()

    report_df = dff.copy()
    report_df = report_df[report_df["_year_num"].notna()].copy()

    if report_df.empty:
        return pd.DataFrame()

    latest_year = int(report_df["_year_num"].max())
    past_four_years_start = latest_year - 3

    athlete_cols = ["Sport", "First Name", "Last Name"]

    current_year = report_df[report_df["_year_num"].eq(2026)].copy()
    if current_year.empty:
        return pd.DataFrame()

    current_year["Gender"] = current_year["Gender"].astype(str).str.strip().str.upper()
    current_year["age_2026"] = 2026 - current_year["BirthYear"]

    cohort_2026 = (
        current_year
        .groupby(athlete_cols, as_index=False)
        .agg(
            BirthYear=("BirthYear", "first"),
            Years_Targeted=("Years Targeted", "first"),
            Gender=("Gender", lambda s: s.iloc[0] if len(s) else ""),
            current_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()),
        )
    )
    cohort_2026["age_2026"] = 2026 - cohort_2026["BirthYear"]

    career_conversion = (
        report_df
        .groupby(athlete_cols, as_index=False)
        .agg(career_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()))
    )
    cohort_2026 = cohort_2026.merge(career_conversion, on=athlete_cols, how="left")

    recent_conversions = (
        report_df[report_df["_year_num"].ge(2022) & report_df["Convert Year"].astype(str).str.upper().eq("Y")]
        .groupby("Sport", as_index=False)
        .size()
        .rename(columns={"size": "Sum of Total conversion Since 2022"})
    )

    yearly = (
        report_df
        .groupby(athlete_cols + ["_year_num"], as_index=False)
        .agg(
            year_best_level=("_program_level", "max"),
            convert_year_flag=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()),
        )
        .sort_values(athlete_cols + ["_year_num"])
    )
    yearly["prev_year"] = yearly.groupby(athlete_cols)["_year_num"].shift(1)
    yearly["prev_level"] = yearly.groupby(athlete_cols)["year_best_level"].shift(1)
    yearly["is_national_conversion"] = (
        yearly["convert_year_flag"]
        & yearly["year_best_level"].isin(NATIONAL_TARGET_LEVELS)
        & yearly["prev_level"].isin(NATIONAL_SOURCE_LEVELS)
        & (yearly["_year_num"] == yearly["prev_year"] + 1)
    )
    national_recent = (
        yearly[yearly["_year_num"].ge(2022) & yearly["is_national_conversion"]]
        .groupby("Sport", as_index=False)
        .size()
        .rename(columns={"size": "Sum of Total Conversion Provincial to national since 2022"})
    )

    cohort_gender = (
        cohort_2026.groupby("Sport")["Gender"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    for gender in ["F", "M", "X"]:
        if gender not in cohort_gender.columns:
            cohort_gender[gender] = 0
    cohort_gender["Gender (F/M/X) - 2026 Cohort"] = cohort_gender.apply(
        lambda row: f"F: {int(row['F'])} / M: {int(row['M'])} / X: {int(row['X'])}",
        axis=1,
    )

    cohort_rollup = (
        cohort_2026
        .groupby("Sport", as_index=False)
        .agg(
            **{
                "TOTAL Athletes 2026 identified (Conv Data)": ("Sport", "size"),
                "Carrer conversion rate for 2026 cohort": ("career_converted", "mean"),
                "Average Years Targeted 2026 cohort (Career)": ("Years_Targeted", "mean"),
                "Average Age 2026 Cohort": ("age_2026", "mean"),
            }
        )
    )

    current_year_rollup = (
        current_year
        .groupby("Sport", as_index=False)
        .agg(current_total=("Sport", "size"), current_converted=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").sum()))
    )

    report_output = cohort_rollup.merge(current_year_rollup, on="Sport", how="left")
    report_output = report_output.merge(recent_conversions, on="Sport", how="left", suffixes=("", "_from_recent"))
    report_output = report_output.merge(national_recent, on="Sport", how="left")
    report_output = report_output.merge(cohort_gender[["Sport", "Gender (F/M/X) - 2026 Cohort"]], on="Sport", how="left")
    report_output["Carrer conversion rate for 2026 cohort"] = (
        report_output["Carrer conversion rate for 2026 cohort"] * 100
    ).round(1)
    report_output["2026 conversion Rate (Current Year convert / Current year total)"] = (
        (report_output["current_converted"] / report_output["current_total"] * 100)
        .fillna(0)
        .round(1)
    )
    report_output["Average Years Targeted 2026 cohort (Career)"] = report_output["Average Years Targeted 2026 cohort (Career)"].round(2)
    report_output["Average Age 2026 Cohort"] = report_output["Average Age 2026 Cohort"].round(1)
    report_output["TOTAL Athletes 2026 identified (Conv Data)"] = report_output["TOTAL Athletes 2026 identified (Conv Data)"].astype(int)
    report_output["Sum of Total conversion Since 2022"] = report_output["Sum of Total conversion Since 2022"].fillna(0).astype(int)
    report_output["Sum of Total Conversion Provincial to national since 2022"] = report_output["Sum of Total Conversion Provincial to national since 2022"].fillna(0).astype(int)
    report_output["Gender (F/M/X) - 2026 Cohort"] = report_output["Gender (F/M/X) - 2026 Cohort"].fillna("F: 0 / M: 0 / X: 0")

    report_output = report_output[
        [
            "Sport",
            "TOTAL Athletes 2026 identified (Conv Data)",
            "Sum of Total conversion Since 2022",
            "Sum of Total Conversion Provincial to national since 2022",
            "2026 conversion Rate (Current Year convert / Current year total)",
            "Carrer conversion rate for 2026 cohort",
            "Average Years Targeted 2026 cohort (Career)",
            "Average Age 2026 Cohort",
            "Gender (F/M/X) - 2026 Cohort",
        ]
    ].sort_values("Sport", key=lambda s: s.map(_sport_sort_key)).reset_index(drop=True)

    report_output["Sport"] = report_output["Sport"].map(_sport_display_name)

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
                        html.Th("TOTAL Athletes 2026 identified (Conv Data)"),
                        html.Th("Sum of Total conversion Since 2022"),
                        html.Th("Sum of Total Conversion Provincial to national since 2022"),
                        html.Th("2026 conversion Rate (Current Year convert / Current year total)"),
                        html.Th("Carrer conversion rate for 2026 cohort"),
                        html.Th("Average Years Targeted 2026 cohort (Career)"),
                        html.Th("Average Age 2026 Cohort"),
                        html.Th("Gender (F/M/X) - 2026 Cohort"),
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(row["Sport"]),
                        html.Td(row["TOTAL Athletes 2026 identified (Conv Data)"]),
                        html.Td(row["Sum of Total conversion Since 2022"]),
                        html.Td(row["Sum of Total Conversion Provincial to national since 2022"]),
                        html.Td(f"{row['2026 conversion Rate (Current Year convert / Current year total)']:.1f}%" if row["2026 conversion Rate (Current Year convert / Current year total)"] is not None else "—"),
                        html.Td(f"{row['Carrer conversion rate for 2026 cohort']:.1f}%" if row["Carrer conversion rate for 2026 cohort"] is not None else "—"),
                        html.Td(f"{row['Average Years Targeted 2026 cohort (Career)']:.2f}" if row["Average Years Targeted 2026 cohort (Career)"] is not None else "—"),
                        html.Td(f"{row['Average Age 2026 Cohort']:.1f}" if row["Average Age 2026 Cohort"] is not None else "—"),
                        html.Td(row["Gender (F/M/X) - 2026 Cohort"]),
                    ])
                    for _, row in report_df.iterrows()
                ]),
            ],
            className="conversion-summary-table",
        ),
        style={"overflowX": "auto"},
    )

    caption = html.Div(
        (
            f"2026 cohort metrics use 2026 rows only; the 2022+ conversion metrics are based on the current filtered view ({latest_year})."
        ) if latest_year is not None else "2026 cohort metrics use 2026 rows only; the 2022+ conversion metrics are based on the current filtered view.",
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
    State("css-checkbox", "value"),
    State("year-filter", "value"),
    prevent_initial_call=True,
)
def download_filtered_csv(n_clicks, selected_sports, filter_2026, filter_css, selected_years):
    if not selected_sports:
        return dash.no_update
    dff = _filter_dashboard_df(selected_sports, filter_2026, filter_css, selected_years)
    return dcc.send_data_frame(dff.to_csv, "conversion_data_filtered.csv", index=False)


@app.callback(
    Output("download-via-sport-csv", "data"),
    Input("btn-download-via-sport-csv", "n_clicks"),
    prevent_initial_call=True,
)
def download_via_sport_csv(n_clicks):
    report_df = _via_sport_report_csv(df)
    if report_df is None or report_df.empty:
        return dash.no_update

    return dcc.send_data_frame(report_df.to_csv, "via_sport_report_all_sports.csv", index=False)


@app.callback(
    Output("all-sports-table-output", "children"),
    Input("btn-generate-all-sports-table", "n_clicks"),
    prevent_initial_call=True,
)
def generate_all_sports_table(n_clicks):
    report = _build_via_sport_report(df)
    return report


@app.callback(
    Output("year-filter", "options"),
    Output("year-filter", "value"),
    Input("sport-dropdown", "value"),
    Input("has-2026-checkbox", "value"),
)
def update_year_dropdown(selected_sports, filter_2026):
    if not selected_sports:
        return [], []
    dff = _filter_dashboard_df(selected_sports, filter_2026, [], None)
    years = sorted(dff['Year'].dropna().astype(int).unique())
    return [{"label": str(y), "value": y} for y in years], years


@app.callback(
    Output("time-series-graph", "figure"),
    Output("conversion-summary", "children"),
    Output("via-sport-report", "children"),
    Output("program-lines-graph", "figure"),
    Output("provincial-to-national-bar-chart", "figure"),
    Output("program-composition-bar-chart", "figure"),
    Output("cohort-pie-chart", "figure"),
    Output("years-targeted-pie-chart", "figure"),
    Output("program-pie-chart", "figure"),
    Output("age-conversion-pie-chart", "figure"),
    Input("sport-dropdown", "value"),
    Input("has-2026-checkbox", "value"),
    Input("css-checkbox", "value"),
    Input("year-filter", "value"),
    Input("age-pie-program-filter", "value"),
)
def update_graphs(selected_sports, filter_2026, filter_css, selected_years, prog_filter):
    if not selected_sports:
        empty = go.Figure()
        msg   = html.Div("No sport(s) selected.", style={"padding": "8px"})
        return empty, msg, html.Div(), empty, empty, empty, empty, empty, empty, empty

    dff = _filter_dashboard_df(selected_sports, filter_2026, filter_css, selected_years)

    via_sport_report = _build_via_sport_report(dff)

    # ── Time-series metrics ───────────────────────────────────────────────────
    grp = dff.groupby('Year', sort=True)

    unique_athletes  = dff.drop_duplicates(['Year', 'First Name', 'Last Name']).groupby('Year').size().sort_index()
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

    # ── Provincial -> national conversion stacked bar ───────────────────────
    athlete_cols = ["Sport", "First Name", "Last Name"]
    yearly_levels = (
        dff
        .groupby(athlete_cols + ["_year_num"], as_index=False)
        .agg(
            year_best_level=("_program_level", "max"),
            convert_year_flag=("Convert Year", lambda s: s.astype(str).str.upper().eq("Y").any()),
        )
        .sort_values(athlete_cols + ["_year_num"])
    )
    yearly_levels["prev_year"] = yearly_levels.groupby(athlete_cols)["_year_num"].shift(1)
    yearly_levels["prev_level"] = yearly_levels.groupby(athlete_cols)["year_best_level"].shift(1)
    yearly_levels["is_provincial_to_national"] = (
        yearly_levels["convert_year_flag"]
        & yearly_levels["year_best_level"].isin(NATIONAL_TARGET_LEVELS)
        & yearly_levels["prev_level"].isin(NATIONAL_SOURCE_LEVELS)
        & (yearly_levels["_year_num"] == yearly_levels["prev_year"] + 1)
    )

    prov_to_nat = yearly_levels[yearly_levels["is_provincial_to_national"]].copy()
    level_labels = {4: "Uncarded", 5: "SC Carded"}
    prov_to_nat["Target Level"] = prov_to_nat["year_best_level"].map(level_labels)

    prov_to_nat_counts = (
        prov_to_nat
        .groupby(["_year_num", "Target Level"], as_index=False)
        .size()
        .rename(columns={"_year_num": "Year", "size": "Count"})
        .sort_values("Year")
    )

    fig_prov_nat = go.Figure()
    for idx, target_level in enumerate(["Uncarded", "SC Carded"]):
        segment = prov_to_nat_counts[prov_to_nat_counts["Target Level"] == target_level]
        fig_prov_nat.add_trace(go.Bar(
            x=segment["Year"],
            y=segment["Count"],
            name=target_level,
            marker=dict(color=VIBRANT_PALETTE[3 + idx]),
        ))

    fig_prov_nat.update_layout(
        barmode="stack",
        title=f"Provincial to National Conversions by Level — {_sports_label(selected_sports)}",
        template="plotly_dark",
        paper_bgcolor=COLOR_BLACK,
        plot_bgcolor=COLOR_DARK_GRAY,
        font=dict(color=COLOR_WHITE),
        title_font=dict(color=COLOR_WHITE, size=16),
        xaxis=dict(title="Year", tickmode="linear", dtick=1, tickformat=".0f", gridcolor="#444"),
        yaxis=dict(title="Conversion Count", gridcolor="#444"),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", y=-0.2, yanchor="top",
            bgcolor=COLOR_DARK_GRAY, bordercolor=COLOR_RED, borderwidth=2,
        ),
        margin=dict(l=40, r=30, t=50, b=40),
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

    return (
        fig_ts,
        summary_table,
        via_sport_report,
        fig_program_lines,
        fig_prov_nat,
        fig_bar,
        fig_pie,
        fig_disp,
        fig_prog,
        fig_age_pie,
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Local dev only — these vars are not used by Posit Connect (gunicorn handles binding)
    _host     = os.environ.get("APP_HOST", "127.0.0.1")
    _port     = int(os.environ.get("APP_PORT", "8050"))
    _debug    = os.environ.get("DEV_MODE", "false").lower() == "true"
    app.run(debug=_debug, host=_host, port=_port)
