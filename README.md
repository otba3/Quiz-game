# Quiz-game

## Fonts

The game uses the locally installed ABC Diatype font for English and ABC
Diatype Arabic for Arabic, including their regular and bold styles. Install
these fonts on the kiosk; font files are intentionally not bundled with the
web app. If a font is not installed, the browser uses its system sans-serif
fallback.

## Account codes

Visitors can enter an existing account code or create an account before
starting the quiz. New accounts require a display name (up to 40 characters)
and receive a randomly generated six-character uppercase code using letters
and digits. The code is shown after account creation; visitors should write it
down because it is needed to use that account again. There is no password,
account recovery, or external account service.

Scores, quiz sessions, daily question points, and point transactions are all
linked to the account's stable internal ID in the local SQLite database at
`data/visitor_scores.db`. The account code is used to look up that ID; it is
not duplicated into score or points records. Existing account codes and their
saved results remain usable after the schema upgrade. New account display
names appear on daily and monthly leaderboards; older accounts without a name
continue to use an anonymous visitor label. Display names are public on the
leaderboard and must be unique, ignoring case and surrounding whitespace.
Account codes are the only means of accessing an account, so
restrict access to the kiosk and its database.

Reward points are awarded in pairs per category: the first quiz waits for the
second, which awards their combined score; the third waits for the fourth,
which awards the average of those two scores rounded down. No further reward
points are awarded in that category until the next day.

Visitors have 30 seconds to enter a code or start account creation; they can
also choose guest mode immediately. The timer pauses while creating an account.
When it expires, the game continues as a guest. Guest scores are shown but not
saved.

After an account quiz, Play again returns to category selection; Exit logs out
and returns to the landing page. Guests return to the landing page when they
choose Play again. Any non-home screen returns to the landing page after two
minutes without input.

The local account API is:

- `POST /api/account/create` with `{"display_name": "..."}` creates an account
  and returns its code once.
- `POST /api/account/login` with `{"account_code": "......"}` checks an
  existing account code without creating an account.
- `POST /api/account/save` links quiz scores and points to the looked-up
  account.

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
The result screen also shows today's average across account-linked quiz
attempts, scaled to 12 questions; guest scores are not included because they
are not saved.