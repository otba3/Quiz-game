# Quiz-game

## Purchase points (API only)

Purchase points are issued as pending, one-time QR claims, separate from RFID
quiz points. Each paid purchase earns one point per complete QAR 10; amounts
support two decimal places, and fractions under QAR 10 do not carry over between
purchases. No new screen or sign-in flow has been added.

Set `PURCHASE_POINTS_STAFF_TOKEN` in the server environment before starting the
app. The staff endpoints return `503` until this token is configured and require
it in the `X-Staff-Token` header.

- `POST /api/purchase/earn` records a paid purchase. Send `amount_qar` (for
  example `"29.99"`) and a unique `purchase_reference` such as
  the POS receipt ID. The API calculates points and returns a one-time
  `claim_code` for staff to encode as a QR and give to
  the visitor. Purchases under QAR 10 earn zero points and do not produce a
  claim code. Reusing a receipt reference returns `409` rather than issuing a
  second claim.

Claim codes are random, stored as hashes, and remain pending for a later
account-redemption integration. The code is a bearer credential: treat it as
private, and only create claims after payment has been confirmed. The staff
endpoint is intended for a trusted staff/POS client; keep the staff token out of
public browser code. The returned code is a QR payload, not a QR image or a
website URL. The colleague's website will later need to exchange it securely
after the visitor signs in.