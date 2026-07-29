# Bowhunting Newsletter

A static site for a bowhunting newsletter: a home page with a subscribe
form and an archive of past issues, plus one issue page per send.

## Structure

- `index.html` — home page, subscribe form, list of past issues
- `issues/` — one HTML file per newsletter issue
- `css/style.css` — site styling
- `js/main.js` — subscribe form handling

## Running locally

No build step. Open `index.html` directly in a browser, or serve the
folder locally:

```
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Adding a new issue

1. Copy `issues/2026-07-29.html` to a new file named `issues/YYYY-MM-DD.html`.
2. Update the title, date, and content.
3. Add a `<li>` entry linking to it at the top of the issue list in `index.html`.

## Deploying

This is a plain static site, so it can be hosted as-is on GitHub Pages,
Netlify, Vercel, or any static host — no build process required.

## Subscribe form

The subscribe form in `index.html` is a placeholder. Wire `js/main.js`
(or the form's `action`) up to an email service (e.g. Mailchimp, Buttondown,
ConvertKit) to actually collect subscribers.
