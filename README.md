# Quiz-game

## Fonts

The game uses the locally installed Lyon Text and Lyon Display desktop fonts
for English, and Lyon Arabic Text for Arabic. Install the supplied desktop
fonts on the kiosk; font files are intentionally not bundled with the web app.
If a font is not installed, the browser uses its system sans-serif fallback.

## Purchase points and cashier demo

Purchase points are issued as pending, one-time QR claims, separate from RFID
quiz points. Each paid purchase earns one point per complete QAR 10; amounts
support two decimal places, and fractions under QAR 10 do not carry over between
purchases. The cashier demo is available at `/cashier`.

Install dependencies and start the app in PowerShell:

```powershell
py -m pip install -r requirements.txt
$env:PURCHASE_POINTS_STAFF_TOKEN = "choose-a-demo-staff-token"
py game/app.py
```

Open `http://localhost:5000/cashier`; the staff token field is prefilled with
`presentation-test`, so staff do not need to type it for a demo. Enter a price
and select **Yes, paid** to issue the QR. Selecting **No** keeps QR issuance
disabled. The cashier automatically creates a unique receipt reference for each
sale. The server token must match the value in the page field; the staff
endpoint returns `503` until the token is configured and requires it in the
`X-Staff-Token` header.

- `POST /api/purchase/earn` records a paid purchase. Send `amount_qar` (for
  example `"29.99"`) and a unique `purchase_reference` such as
  the POS receipt ID, plus `"paid": true`. The API calculates points and
  returns a one-time `claim_code` and locally generated QR image for staff to
  give to the visitor. Purchases under QAR 10 earn zero points and do not
  produce a claim code. Reusing a receipt reference returns `409` rather than
  issuing a second claim.

Claim codes are random, stored as hashes, and remain pending for a later
account-redemption integration. The code is a bearer credential: treat it as
private, and only create claims after payment has been confirmed. The staff
endpoint is intended for a trusted staff/POS client; keep the staff token out of
public browser code. The current demo QR contains the claim code only; it does
not yet open the colleague's website or credit a signed-in visitor account.

The QR is generated locally by the app and is not sent to an external QR
service. `presentation-test` is a public demo credential, not a production
secret. Anyone who can reach the demo cashier can issue test claims; use it only
on a trusted presentation network and replace the demo token with proper staff
authentication before any real deployment.

## Quiz leaderboards

The quiz category screen includes daily and monthly leaderboards for both
categories. Daily scores count each correctly answered question only once per
RFID card and category, up to 12 points per day. Monthly scores add the saved
scores from every quiz completed during the current calendar month. Leaderboard
names are anonymous, stable visitor labels; no account connection is used.
Five sample visitors are included for presentations by default. Set
`LEADERBOARD_DEMO_MODE=false` to hide them.