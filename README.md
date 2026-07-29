# Bowhunting Newsletter

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
- **This is set up to run locally on your Windows PC**, not on a public
  server. That means: it can only accept signups and send newsletters while
  your PC is on, awake, and (if you want the public to actually reach the
  signup page) network-reachable. If you later want real public signups
  24/7, this same codebase can be deployed to a normal Python host (Render,
  Railway, PythonAnywhere, a VPS, etc.) — ask if you want help with that.

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
   python manage.py migrate
   python manage.py seed_states
   python manage.py createsuperuser
   ```

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
2. **General tab:** name it (e.g. "Bowhunting Newsletter — Aggregate").
3. **Triggers tab:** New → Weekly, pick a day/time (e.g. Monday 7:00 AM).
4. **Actions tab:** New → Action "Start a program" →
   Program: `C:\path\to\project\scripts\run_aggregate.bat`
   Start in: `C:\path\to\project`
5. Save. Repeat for a second task pointing at `run_send.bat`, scheduled a
   day or two later (e.g. Wednesday), so you have time to review/approve
   content in between.

Your PC needs to be on (not asleep) at the scheduled time for these to run.

## Subscriber limits

Each subscriber can select up to 3 states at signup (enforced in the
signup form). Re-submitting the signup form with a different email is
fine; re-submitting with the same email replaces their previous state
selections with the new ones.
