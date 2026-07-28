from flask import Flask, render_template, request, jsonify

import FeatureExtraction
from FeatureExtraction import MODEL_FEATURE_COLUMNS
import pickle

app = Flask(__name__)

# Load the trained model once at startup instead of on every request --
# pickle.load() was previously called inside getURL(), re-reading the
# ~220KB file from disk on every single form submission.
with open('RandomForestModel.sav', 'rb') as model_file:
    RFmodel = pickle.load(model_file)


# Human-readable label for each raw feature column, shown in the frontend
# checklist. Keeping this next to MODEL_FEATURE_COLUMNS (imported above)
# means the two can never drift out of order with each other.
SIGNAL_LABELS = {
    'Having_@_symbol':             'No "@" symbol in the URL',
    'Having_IP':                   'Host is a domain name, not a raw IP',
    'Prefix_suffix_separation':    'No hyphen-padded brand name in the domain',
    'Redirection_//_symbol':       'No suspicious "//" redirect in the path',
    'Sub_domains':                 'Subdomain depth looks normal',
    'URL_Length':                  'URL length is not suspicious',
    'age_domain':                  'Domain is not newly registered',
    'dns_record':                  'Domain resolves to a valid DNS record',
    'domain_registration_length':  'Domain registered for a reasonable duration',
    'http_tokens':                 'No "http" token trick in the domain',
    'statistical_report':          'Not on a known suspicious host/IP list',
    'tiny_url':                    'Not a known link-shortening service',
    'web_traffic':                 'Traffic ranking check',
}

# Each raw feature value is 0 (legitimate-like), 1 (phishing-like), or
# 2 (suspicious / couldn't determine) -- map those to the three states the
# frontend checklist displays.
STATUS_BY_VALUE = {0: 'pass', 1: 'fail', 2: 'warn'}


def build_signal_report(feature_row):
    """
    Turns one row of the model's feature DataFrame into a list of
    {key, label, value, status} dicts for the frontend checklist, in the
    same order as MODEL_FEATURE_COLUMNS.
    """
    signals = []
    for col in MODEL_FEATURE_COLUMNS:
        value = int(feature_row[col])
        signals.append({
            'key': col,
            'label': SIGNAL_LABELS.get(col, col),
            'value': value,
            'status': STATUS_BY_VALUE.get(value, 'warn'),
        })
    return signals


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/classic')
def classic():
    # The original simple form-based UI, kept around for comparison.
    return render_template("home.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/api/check', methods=['POST'])
def api_check():
    """
    JSON API used by the Harbor frontend's live checker.
    Request:  {"url": "https://example.com"}
    Response: {"url": ..., "verdict": "legitimate"|"phishing",
               "verdict_label": "Legitimate"|"Phishing",
               "signals": [...], "passed": int, "total": int}
    """
    payload = request.get_json(silent=True) or {}
    url = (payload.get('url') or '').strip()

    if not url:
        return jsonify({'error': 'Please enter a URL to check.'}), 400

    # The frontend's input box only collects everything after "https://",
    # so add the scheme back on if the caller didn't include one.
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        data = FeatureExtraction.getAttributess(url)
        predicted_value = RFmodel.predict(data)
    except Exception as exc:
        app.logger.exception("Failed to classify URL: %s", url)
        return jsonify({
            'error': f'Could not analyze that URL ({exc.__class__.__name__}). Please check it and try again.'
        }), 422

    feature_row = data.iloc[0]
    signals = build_signal_report(feature_row)
    passed = sum(1 for s in signals if s['status'] == 'pass')

    is_phishing = bool(predicted_value[0] == 1)
    return jsonify({
        'url': url,
        'verdict': 'phishing' if is_phishing else 'legitimate',
        'verdict_label': 'Phishing' if is_phishing else 'Legitimate',
        'signals': signals,
        'passed': passed,
        'total': len(signals),
    })


@app.route('/getURL', methods=['GET', 'POST'])
def getURL():
    # Kept for the /classic form, which does a plain HTML POST rather than
    # calling the JSON API.
    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            return render_template("home.html", error="Please enter a URL to check.")

        try:
            data = FeatureExtraction.getAttributess(url)
            predicted_value = RFmodel.predict(data)
        except Exception as exc:
            app.logger.exception("Failed to classify URL: %s", url)
            return render_template(
                "home.html",
                error=f"Could not analyze that URL ({exc.__class__.__name__}). Please check it and try again."
            )

        value = "Legitimate" if predicted_value[0] == 0 else "Phishing"
        return render_template("home.html", error=value)

    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True)
