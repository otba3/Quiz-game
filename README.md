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

## Admin dashboard and visitor statistics

The admin signs in with the reserved code `adm1n1` by default. Only the admin
code reveals the Dashboard button, and the dashboard API checks it on every
request. The admin account is stored separately from visitor accounts in the
local `data/visitor_scores.db`; its code cannot be generated for a visitor.
To set or change the code and display name, start the app once with:

```bash
ADMIN_ACCOUNT_CODE=ZXCV12 ADMIN_DISPLAY_NAME="Museum Manager" python3 game/app.py
```

Use a six-character ASCII letter/digit code that is not already used by a
visitor. The values are saved in the database on startup. After stopping the
app, start it normally without the variables; the saved admin account remains:

```bash
python3 game/app.py
```

To change it later, run the first command again with the new values. If an
automatic startup service still sets either variable, its configured value
will overwrite the corresponding saved value at each startup; update or remove
those settings before changing the account. The application refuses to start
if the code conflicts with a visitor account and leaves the saved data intact.
The code is stored in the local database, so restrict access to that file and
keep backups of it; changing the admin account does not erase visitor scores.

All visitors see the compact statistics line in this order:
`feedback / completed quizzes / completed quizzes today / average score out of
6 / average feedback rating out of 5`. The dashboard displays the same metrics
with labels. “Players” counts completed quiz sessions (including guest games),
not unique people, since guests are anonymous. Average scores use completed
quizzes; the feedback average uses submitted 1–5 ratings. These records are
stored locally in `data/visitor_scores.db`. Anonymous guest scores are recorded
only for these statistics; guests do not receive saved account scores or points.
Existing account quiz sessions are included automatically when the app starts
with the dashboard update. Historical scores above 6 are counted as plays but
excluded from the `/6` average because their question count is unknown. Past
guest games without records cannot be recovered.

On the admin dashboard, select **Average score** to see anonymous account
comparisons. Each row groups the first two quizzes for one account, category,
and local date; a dash means a second quiz has not been completed. The change
is the second score minus the first. Later attempts are not included in that
row, and guest plays cannot be paired because they have no account identity.
Select **Average feedback rating** to see how many submitted ratings fall into
each value from 1 to 5, including guest feedback. Both detail pages require the
admin code and include all available history.

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
  existing account code without creating an account; the reserved admin code
  signs in with the admin role.
- `POST /api/account/save` links quiz scores and points to the looked-up
  account.
- `GET /api/admin/dashboard` returns dashboard statistics only when called
  with the configured code in the `X-Admin-Code` header.

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