# Harbor: Phishing Website Detection

A web app that checks a URL and tells you whether it looks legitimate or phishing, and shows which signals led to the result.

<!-- Add a screenshot after you upload one to the repo:
![Harbor screenshot](screenshot.png)
-->

## How it works

1. You enter a URL.
2. The backend extracts 13 features from it (URL structure, domain age, DNS record, and more).
3. A trained Random Forest model classifies the URL as legitimate or phishing.
4. The page shows the verdict and each signal as pass, fail, or unclear.

## Features

- 13 URL and domain-based signals checked per link
- Random Forest classifier trained on labeled URL data
- JSON API (`/api/check`) that returns the verdict and every signal
- Responsive frontend with a URL breakdown (scheme, subdomain, domain) and a signal checklist
- Toggle between `http://` and `https://` for the input
- Original simple form-based page kept at `/classic`

## Signals checked

| Signal | What it looks at |
|---|---|
| Having_IP | Raw IP address used instead of a domain name |
| Having_@_symbol | "@" in the URL |
| URL_Length | Unusually long URLs |
| Sub_domains | Number of subdomains |
| Prefix_suffix_separation | Hyphen in the domain name |
| Redirection_//_symbol | "//" redirect inside the path |
| http_tokens | "http" or "https" text inside the domain |
| tiny_url | Known URL-shortening services |
| statistical_report | Hosts or IPs on a known suspicious list |
| age_domain | How old the domain is (WHOIS) |
| domain_registration_length | How long the domain is registered for (WHOIS) |
| dns_record | Whether the domain has a valid record |
| web_traffic | Traffic ranking (see Limitations) |

## Tech stack

Python, Flask, scikit-learn, pandas, BeautifulSoup, python-whois, HTML, Tailwind CSS, JavaScript

## Project structure

```
backend_final/
├── app.py                  Flask app and API routes
├── FeatureExtraction.py    Extracts the 13 features from a URL
├── Classifier.py           Trains the model and saves it
├── RandomForestModel.sav   Trained model
├── legitimate-urls.csv     Training data (legitimate URLs)
├── phishing-urls.csv       Training data (phishing URLs)
├── requirements.txt        Python dependencies
├── CHANGES.md              Bugs found and fixed
└── templates/              HTML pages
```

## Setup

Requires Python 3.8 or later.

```bash
git clone https://github.com/kv0011/Harbor.git
cd Harbor

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## API

**POST** `/api/check`

Request:
```json
{ "url": "https://example.com" }
```

Response:
```json
{
  "url": "https://example.com",
  "verdict": "legitimate",
  "verdict_label": "Legitimate",
  "signals": [
    { "key": "Having_IP", "label": "Host is a domain name, not a raw IP", "value": 0, "status": "pass" }
  ],
  "passed": 9,
  "total": 13
}
```

Each signal's `status` is `pass`, `fail`, or `warn` (unclear).

## Retraining the model

```bash
python Classifier.py
```

This reads both CSV files, trains a new Random Forest, prints the test accuracy, and overwrites `RandomForestModel.sav`. Retrain if you see a scikit-learn version warning when starting the app.

## Results

- Training data: 2,015 labeled URLs (1,017 legitimate, 998 phishing)
- Test accuracy: about 82% on a held-out 20% split

## Limitations

- The model is trained on a small dataset and will make mistakes. Do not use it as a security control.
- WHOIS and DNS signals need internet access. If a lookup times out or fails, those signals count against the URL, which can push a legitimate site toward a phishing verdict.
- The `web_traffic` signal always returns a neutral value. It originally used the Alexa ranking API, which was shut down in 2022.
- Some WHOIS servers return incomplete data, so results vary by domain and registrar.

## Fixes made to the original code

Details are in [CHANGES.md](CHANGES.md). The main ones:

- Fixed a column mismatch between training and prediction that caused errors or wrong results
- Fixed a crash on domains whose WHOIS dates include timezone information
- Replaced the dead Alexa API call
- Reduced three WHOIS lookups per request to one, with a timeout
- Added the JSON API and the new frontend

## Credits

The feature set and training data come from an open-source phishing website detection project. The backend fixes, JSON API, and frontend were added on top of it.

