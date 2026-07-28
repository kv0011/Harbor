# Changes made to the backend

## 1. Fixed a crash-causing bug: wrong columns fed to the model
`app.py` built the model's input by dropping 3 columns *by position*
(`data.columns[[0,3,5]]`) to match the training data. The training CSVs'
columns were in alphabetical order; the live app's columns were in a
different order — so it dropped the wrong 3 columns, leaving text columns
(`Domain`, `Path`) in the data handed to `RFmodel.predict()`. Current
scikit-learn raises `could not convert string to float` on that.

**Fix:** `FeatureExtraction.py` now defines one shared, named list,
`MODEL_FEATURE_COLUMNS`, that both `Classifier.py` (training) and
`getAttributess()` (inference) use to select columns *by name*. They can
no longer silently drift apart.

## 2. Removed a dead external dependency
`web_traffic()` called the Alexa Traffic Rank API (`data.alexa.com`),
which Amazon shut down in May 2022. It now returns a neutral fallback
value (`2`) instead of throwing an unhandled network error on every
request.

## 3. Removed redundant WHOIS lookups
Three separate feature functions (`domain_registration_length`,
`age_domain`, `dns_record`) each independently queried WHOIS for the
same domain, tripling network latency per request. WHOIS is now looked
up once per request in `getAttributess()` and shared across all three.

## 4. Added a hard timeout on WHOIS lookups
The `whois` library has no reliable built-in timeout — it can retry
against multiple servers internally. `_safe_whois()` now runs the lookup
in a worker thread with a hard wall-clock cap (6s default), so a
slow/unresponsive WHOIS server can no longer stall a request
indefinitely.

## 5. Retrained the model
Retrained `RandomForestModel.sav` against the corrected feature columns
using the current scikit-learn version (avoids old-pickle
version-compatibility issues down the line). ~82% accuracy on held-out
test data (403 examples): see console output of `Classifier.py`.

## 6. `app.py` cleanup
- Model is now loaded once at startup instead of on every request.
- Errors during feature extraction (bad input, network hiccups) now show
  a friendly message instead of a raw 500 error page.
- Empty URL submissions are handled explicitly.

## 7. Added `requirements.txt`
Pins the packages this app actually needs (`Flask`, `pandas`,
`scikit-learn`, `beautifulsoup4`, `python-whois`, `lxml`) — none of these
were declared anywhere in the original repo.

## 8. Removed `Classifier2.py`
This was a dead, broken scratch file (undefined variables, typos) never
imported by `app.py`. Left out of this package to avoid confusion; the
original is still in your uploaded zip if you want to look at it.

## 9. Minor
Fixed `SyntaxWarning: invalid escape sequence` on the two big regex
literals (should have been raw strings `r'...'` — no behavior change).
