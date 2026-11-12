# Quiz-game

## Fonts

The game uses the locally installed Lyon Text and Lyon Display desktop fonts
for English, and Lyon Arabic Text for Arabic. Install the supplied desktop
fonts on the kiosk; font files are intentionally not bundled with the web app.
If a font is not installed, the browser uses its system sans-serif fallback.

## Account codes

After choosing a language, visitors can enter an account code before starting
the quiz. They have 30 seconds; they can also choose guest mode immediately.
When the timer expires, the game continues as a guest. Guest scores are shown
but not saved.

Scores for entered codes are stored locally on the Pi in
`data/visitor_scores.db`. The Pi accepts any non-empty code up to 128 characters
and uses it as a local account identifier; it does not check or synchronize
with an external account service. Leading and trailing spaces are trimmed.
Keep access to the Pi and its database restricted if account codes identify
visitors.

Install dependencies and start the app:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python3 game/app.py
```

## Quiz leaderboards

The quiz category screen includes daily and monthly leaderboards for both
categories. Daily scores count each correctly answered question only once per
account and category, up to 12 points per day. Monthly scores add the saved
scores from every quiz completed during the current calendar month. Leaderboard
names are anonymous, stable visitor labels. Five sample visitors are included
for presentations by default. Set `LEADERBOARD_DEMO_MODE=false` to hide them.