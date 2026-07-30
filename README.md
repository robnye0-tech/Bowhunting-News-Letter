# Broadhead Brief

A Django app for a weekly, state-by-state bowhunting newsletter. Subscribers
pick up to 3 states and get a weekly email per state covering law changes,
proposed law changes, public land updates, and EHD reports — plus a
curated product list for that state. Built to run on your own Windows PC.

## What's automated vs. what needs a human

Be aware of this before relying on it:

- **Content aggregation is semi-automated, not fully automatic.** There is
  no single reliable data source for "bow hunting law changes + EHD reports
  + public land updates" across all 50 states. The `aggregate_content`
  command polls RSS feeds you configure per state and drops new articles in
  as **drafts**. Nothing gets emailed until a human reviews and approves
  those drafts (and/or adds items by hand) in the admin.
- **You have to find and add the RSS feeds yourself.** I tried to
  pre-populate real, verified feed URLs for you, but this build environment's
  network access to state `.gov` sites is blocked, so I couldn't confirm any
  URLs were real without risking feeding you made-up ones. See "Adding
  content sources" below — no sources ship pre-loaded.
- **Many state agencies don't have RSS at all.** For those states, skip
  aggregation and just add `ContentItem`s manually in the admin each week.
- **The product list is fully manual**, by design (you add products per
  state each week in the admin).
- **Local Windows use and real 24/7 hosting are both supported.** Day-to-day
  development happens on your PC with SQLite. When you're ready to go
  public, see "Deploying to a real host" below — the same codebase deploys
  to a normal Python host without changes, it just needs a few extra
  environment variables set.
- **The watch bot (`run_watch_bot`) is a generic change detector, not a
  smart reader.** It flags "this page's text changed since last time," for
  both RSS and plain agency pages. It cannot tell *what* changed or whether
  it matters — every state site is laid out differently. A human still
  needs to read every flagged item before it goes in the newsletter. See
  "The watch bot" below.
- **Only "launched" states are offered on the signup form.** All 51 states
  exist in the database (so you can prep content sources ahead of time),
  but the public can only pick from states you've explicitly launched —
  see "Launching states" below. Don't offer a state before you have a real
  content pipeline for it; an empty inbox every week is worse than not
  offering it yet.

## Tech stack

- **Django** — web app + built-in admin (used as the curation dashboard)
- **SQLite** — database (a single file, no separate server to install)
- **Resend** — sends the actual emails (falls back to printing emails to
  the console if you haven't set up Resend yet, so you can test everything
  locally first)
- **feedparser** — reads RSS/Atom feeds for content aggregation

## Project structure

```
config/                  Django project settings/URLs
newsletter/
  models.py               State, Subscriber, Subscription, ContentSource,
                           ContentItem, Product, NewsletterIssue
  admin.py                 Admin dashboard (this IS your curation UI)
  views.py / urls.py       Public signup / confirm / unsubscribe pages
  emails.py                Resend sending helper (with console fallback)
  templates/newsletter/    Signup pages + HTML email templates
  management/commands/
    seed_states.py           Populate all 50 states + DC
    aggregate_content.py     Pull RSS sources into draft ContentItems
    send_weekly_newsletter.py  Compile + send approved content per state
scripts/
  run_aggregate.bat        Windows Task Scheduler target
  run_send.bat              Windows Task Scheduler target
```

## Setup on Windows

1. **Install Python 3.11+** from [python.org](https://www.python.org/downloads/)
   if you don't have it. During install, check "Add Python to PATH".

2. **Open PowerShell (or Command Prompt) in the project folder** and create
   a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   You'll need to run `.venv\Scripts\activate` again every time you open a
   new terminal to work on this project.

3. **Create your `.env` file:**

   ```powershell
   copy .env.example .env
   ```

   Open `.env` in a text editor. At minimum, set `DJANGO_SECRET_KEY` to any
   long random string. Leave `RESEND_API_KEY` blank for now — emails will
   just print to your terminal instead of sending, so you can test
   everything first.

4. **Set up the database and an admin login:**

   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   python manage.py seed_states
   python manage.py createsuperuser
   ```

   `makemigrations` generates the database schema from `models.py` (this
   only needs to be re-run when models change, e.g. after pulling an
   update to this repo); `migrate` actually creates the tables.

   Follow the prompts to set an admin username/password.

5. **Run it:**

   ```powershell
   python manage.py runserver
   ```

   - Public signup page: http://127.0.0.1:8000/
   - Admin/curation dashboard: http://127.0.0.1:8000/admin/

## Weekly editorial workflow

1. Run `python manage.py aggregate_content` (or let Task Scheduler run
   `scripts\run_aggregate.bat`) early in the week. This pulls new articles
   from any active content sources into the admin as **drafts**.
2. Go to `/admin/newsletter/contentitem/`, review the drafts, set each
   item's **category** (Law change / Proposed law change / Public land
   update / EHD report / General), edit the title/summary if needed, then
   select the good ones and use the **"Approve selected items for send"**
   action. You can also add items by hand here — click "Add content item".
3. Go to `/admin/newsletter/product/` and add this week's curated product
   picks per state.
4. Run `python manage.py send_weekly_newsletter` (or let Task Scheduler run
   `scripts\run_send.bat`). For each state with approved content and/or
   products for the current week, it emails every confirmed subscriber of
   that state and marks the week as sent. Re-running it is safe — states
   already sent for the week are skipped.
   - Add `--dry-run` to see recipient counts without actually sending
     anything, useful for checking your work first.

## Launching states

Only launched states show up on the public signup form and get processed
by `send_weekly_newsletter`. All 51 states exist in the database from
`seed_states`, but none start out launched — you turn them on deliberately
as you build out a real content pipeline for each.

```powershell
python manage.py launch_states ME NH VT NY CT RI NJ PA
```

Run it again anytime with more codes to expand later — states already
launched are left alone, so it's always safe to re-run. To pull a state
back off the signup form, uncheck its **Is launched** box in
`/admin/newsletter/state/` (it's editable right in the list view).

## Adding content sources

Go to `/admin/newsletter/contentsource/` → "Add content source" and enter:
a state, a label (e.g. "Ohio DNR News"), and the RSS/Atom feed URL.

To find real feed URLs: check the state wildlife/game agency's newsroom or
press-release page for an RSS/XML link, or try appending `/feed/` or
`/rss.xml` to their news section URL (works for many WordPress-based
sites). Not every state publishes one — if a state has no usable feed,
just skip aggregation for it and add that state's `ContentItem`s by hand
each week instead. The [Bureau of Land Management's RSS page](https://www.blm.gov/info/RSS-feeds)
is also worth checking for public-land content in BLM-heavy western states.

For states with no RSS feed at all, add a **"Plain page (watched for
changes)"** source instead (same admin screen) — point it at the agency's
news/regulations page. See "The watch bot" below for how that gets checked.

## The watch bot

`run_watch_bot` is a bot you start and stop yourself. Start it and leave it
running in a terminal window; it checks every active content source (RSS
feeds *and* plain pages) on a timer until you close the window or press
Ctrl+C.

```powershell
python manage.py run_watch_bot
```

or double-click `scripts\start_watch_bot.bat`.

What it does with what it finds:

- **RSS sources** — same as `aggregate_content`: new articles become draft
  `ContentItem`s in the admin.
- **Plain page sources** — it fetches the page, strips it down to visible
  text, and compares that text to what it saw last time:
  - **First time checking a source:** nothing to compare yet, so it just
    records a baseline and writes a snapshot file. No draft item yet.
  - **Unchanged since last check:** does nothing.
  - **Changed since last check:** writes a snapshot file to
    `scraped_updates\<STATE_CODE>\` (created automatically) with the page
    text, and creates a draft `ContentItem` in the admin so it flows into
    the normal review/approve pipeline alongside RSS finds.

**Be clear about what this is and isn't.** It's a generic change detector —
"this page's text is different than last time" — not a system that reads
and understands the page. Every state agency site is laid out differently,
so it can't reliably tell "the deer season dates changed" from "they added
a banner ad." Every flagged page still needs a human to actually read it
and decide whether/how it belongs in the newsletter, same as everything
else in this project. It also won't see JavaScript-rendered content (some
modern agency sites build their page with JS after load) — if a source
keeps reporting "no readable text," that's likely why.

Options:

```powershell
python manage.py run_watch_bot --once              # single pass and exit (good for Task Scheduler)
python manage.py run_watch_bot --interval 12        # check every 12 hours instead of the 6-hour default
python manage.py run_watch_bot --out my_folder      # write snapshots somewhere else
```

## Setting up real email sending (Resend)

1. Create a free account at [resend.com](https://resend.com).
2. Verify a sending domain (or use their test domain while developing).
3. Create an API key and put it in `.env` as `RESEND_API_KEY=...`.
4. Set `DEFAULT_FROM_EMAIL` in `.env` to an address on your verified domain.

Once `RESEND_API_KEY` is set, `aggregate_content`/confirmation emails and
`send_weekly_newsletter` will actually send instead of printing to the
console.

## Scheduling with Windows Task Scheduler

Since this runs on your own PC, use Task Scheduler to run the weekly jobs
automatically:

1. Open **Task Scheduler** → **Create Task**.
2. **General tab:** name it (e.g. "Broadhead Brief — Aggregate").
3. **Triggers tab:** New → Weekly, pick a day/time (e.g. Monday 7:00 AM).
4. **Actions tab:** New → Action "Start a program" →
   Program: `C:\path\to\project\scripts\run_aggregate.bat`
   Start in: `C:\path\to\project`
5. Save. Repeat for a second task pointing at `run_send.bat`, scheduled a
   day or two later (e.g. Wednesday), so you have time to review/approve
   content in between.

Your PC needs to be on (not asleep) at the scheduled time for these to run.

## Deploying to a real host

The app is ready to deploy as-is to a normal Python host — see the
"Getting a domain and going live" walkthrough for the actual step-by-step.
The pieces that make it deployable, for reference:

- **`Procfile`** — standard convention most Python hosts read: runs
  migrations + `collectstatic` on each deploy (`release`), then serves the
  app with gunicorn (`web`).
- **Database** — reads a `DATABASE_URL` environment variable if one is set
  (via `dj-database-url`); falls back to the same local SQLite file when
  it isn't. Some hosts inject `DATABASE_URL` into your app automatically
  when you attach Postgres; on Render's plain dashboard flow (used below)
  you copy/paste it in yourself — one extra step, still no code changes.
- **Static files** — served directly by the app via `whitenoise`, so you
  don't need a separate static file host or CDN.
- **Security settings** — `SECURE_SSL_REDIRECT` and related cookie flags
  turn on automatically once `DJANGO_DEBUG=False`; they're off locally so
  they never interfere with `runserver` on your PC.

Required environment variables in production (same names as `.env`, just
set through your host's dashboard instead of a `.env` file):

| Variable | Production value |
|---|---|
| `DJANGO_SECRET_KEY` | A long random string (different from your local one) |
| `DJANGO_DEBUG` | `False` |
| `ALLOWED_HOSTS` | Your domain, e.g. `broadheadbrief.com` |
| `SITE_BASE_URL` | `https://` + your domain |
| `RESEND_API_KEY` | Your real Resend API key |
| `DEFAULT_FROM_EMAIL` | An address on your Resend-verified domain |
| `DATABASE_URL` | On Render: the Postgres instance's Internal Database URL, pasted in manually |

The weekly `aggregate_content` / `run_watch_bot` / `send_weekly_newsletter`
jobs still need to run on a schedule once you're live. Two ways to do that
— see "Getting a domain and going live" below for the recommended one:

- **Keep Task Scheduler running locally** (recommended to start) — point
  your local `.env`'s `DATABASE_URL` at the production Postgres database
  and keep using Windows Task Scheduler exactly as before. The jobs run on
  your PC but read/write the same live database the public site uses, so
  nothing about your weekly workflow changes. No extra cost.
- **Move the jobs to the host's own scheduler** (e.g. Render Cron Jobs) —
  fully cloud-based, but costs extra per job (Render: ~$1/month minimum
  each) and `run_watch_bot`'s `scraped_updates` snapshot files won't
  persist between runs on most hosts' default (ephemeral) disks, since
  each cron run gets a fresh container — only the draft `ContentItem`s it
  also creates in the database would survive. Worth it later if you want
  to stop relying on your PC being on; not necessary to start.

## Getting a domain and going live (Cloudflare + Render)

Concrete step-by-step for the combination recommended above. Render has a
free web service tier and a free-for-90-days Postgres tier; Cloudflare
Registrar sells domains at wholesale price with no markup.

### 1. Register your domain (Cloudflare)

1. Go to the [Cloudflare dashboard](https://dash.cloudflare.com/) → **Domain
   Registration** → **Register Domains**, search for the name you want.
2. Fill in registrant contact info, choose a payment method, accept the
   Domain Registration Agreement, and complete the purchase.
3. Check your email and verify the registrant address — ICANN requires
   this before the domain fully activates.
4. That's it for now — you'll point its DNS at Render in step 4.

### 2. Push this repo to GitHub

Render deploys from a GitHub repo. If you haven't already, make sure your
latest code (including everything from this session) is pushed to your
GitHub repo — Render will connect to it directly.

### 3. Create the Render web service + database

1. Sign up at [render.com](https://render.com) (you can sign in with
   GitHub, which also makes connecting the repo one click).
2. **New +** → **PostgreSQL**. Give it a name, leave the free plan
   selected, create it. Once it's up, Render shows an **Internal Database
   URL** and an **External Database URL** — you'll use both later.
3. **New +** → **Web Service** → connect your GitHub repo.
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi`
5. Under **Environment**, add the variables from the table above:
   `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `RESEND_API_KEY`,
   `DEFAULT_FROM_EMAIL`. For `DATABASE_URL`, paste the **Internal Database
   URL** from the Postgres instance you created. Leave `ALLOWED_HOSTS` and
   `SITE_BASE_URL` for the next step, once you know your final domain.
6. Deploy. Render gives you a working `https://your-service.onrender.com`
   URL immediately, before your custom domain is even connected — good for
   confirming the deploy actually works.
7. Set `ALLOWED_HOSTS` to that `onrender.com` hostname for now and redeploy
   if the site doesn't load; you'll add your real domain to it next.

### 4. Connect your domain

1. In the Render web service → **Settings** → **Custom Domain**, add your
   domain (both `yourdomain.com` and `www.yourdomain.com` if you want
   both). Render shows you the DNS records it needs (usually a `CNAME` for
   `www` and an `A`/`ALIAS` record for the bare domain).
2. In Cloudflare → your domain → **DNS**, add those exact records Render
   gave you.
3. Back in the Render **Environment** tab, update:
   - `ALLOWED_HOSTS` → `yourdomain.com,www.yourdomain.com`
   - `SITE_BASE_URL` → `https://yourdomain.com`
4. Redeploy. DNS can take anywhere from a few minutes to a few hours to
   propagate — Render's dashboard shows when the certificate/domain check
   passes.

### 5. Finish setup on the live site

1. Creating your admin login needs a one-off command, not a web page: open
   the Render web service's **Shell** tab and run
   `python manage.py createsuperuser`, then follow the prompts.
2. In that same Shell tab, run `python manage.py seed_states` once to
   populate all 50 states + DC in the production database.
3. Visit `https://yourdomain.com/admin/` and log in with the superuser you
   just created.
4. Locally, regenerate the QR code against the real domain:
   `python manage.py generate_signup_qr --url https://yourdomain.com/`.
5. Point your local `.env`'s `DATABASE_URL` at the Postgres instance's
   **External Database URL** (shown on that database's page in the Render
   dashboard), so your existing Windows Task Scheduler jobs
   (`run_aggregate.bat`, `start_watch_bot.bat`, `run_send.bat`) read/write
   the live database instead of your local SQLite file.

## Signup QR code

Generate a QR code that links straight to the signup page (the home page
already asks for email + up to 3 states in one step, so there's nothing
extra to build — the QR just needs to point there):

```powershell
python manage.py generate_signup_qr
```

This saves a PNG to `qr_codes/signup_qr.png`, encoding `SITE_BASE_URL`
(from `.env`) + the signup page path.

**Before printing or sharing it anywhere**, make sure `SITE_BASE_URL` in
`.env` is set to a real, public domain — not `http://127.0.0.1:8000`.
A QR code encoding a localhost address will only work on devices on your
own machine; nobody scanning it from a flyer or a shop counter will reach
your site. The command warns you if it detects a local address. Once you
have real hosting set up (see the note in "What's automated vs. what needs
a human" above), update `SITE_BASE_URL` and re-run the command to get a
working code.

Options:

```powershell
python manage.py generate_signup_qr --url https://example.com/         # encode a different URL
python manage.py generate_signup_qr --out marketing\qr.png             # custom output path
```

**Always test-scan the generated PNG with your phone before printing or
distributing it.**

## Subscriber limits

Each subscriber can select up to 3 states at signup (enforced in the
signup form). Re-submitting the signup form with a different email is
fine; re-submitting with the same email replaces their previous state
selections with the new ones.
