# CSIP Conversion Dashboard

A Plotly Dash application that visualises athlete carding conversion data. Deployed on **Posit Connect**.

## Repository structure

```
Conversion_Dashboard_v2.py   ← main app (Posit Connect entry point)
Conversion_Data_2026_final.csv ← dataset
requirements.txt             ← Python dependencies
manifest.json                ← Posit Connect deployment manifest
.env.example                 ← template for local environment variables
scripts/                     ← data-wrangling scripts used to build the dataset
  data/                      ← intermediate / source data files
```

## Running locally

```bash
pip install -r requirements.txt

# Copy and fill in your credentials
cp .env.example .env
# Edit .env with your actual SITE_URL, CLIENT_ID, CLIENT_SECRET, OAUTH_REDIRECT_PATH

python Conversion_Dashboard_v2.py
# or
gunicorn "Conversion_Dashboard_v2:server"
```

## Deploying to Posit Connect

1. Set the following **environment variables** in the app's *Vars* tab on Posit Connect (do **not** hardcode them):
   - `SITE_URL` — base URL of your Django OAuth provider
   - `OAUTH_REDIRECT_PATH` — the full public redirect URI (your Connect app URL + `/redirect`)
   - `CLIENT_ID`
   - `CLIENT_SECRET`

2. Deploy using `rsconnect` or the Connect UI, or push the `manifest.json`:
   ```bash
   rsconnect deploy manifest manifest.json
   ```

## Required environment variables

| Variable | Description |
|---|---|
| `SITE_URL` | Base URL of the Django OAuth provider |
| `OAUTH_REDIRECT_PATH` | Full redirect URI registered on the OAuth provider |
| `CLIENT_ID` | OAuth2 client ID |
| `CLIENT_SECRET` | OAuth2 client secret |
