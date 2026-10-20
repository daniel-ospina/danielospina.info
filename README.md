# danielospina.info

Source for [danielospina.info](https://danielospina.info) — a plain static site.
No framework, no build step, no dependencies. What's in this repo is exactly what
Cloudflare serves.

Migrated off Squarespace in October 2026. Content (bio, talks, all eight blog
posts and their images) was carried over from the Squarespace export; the design
is new.

## Structure

```
index.html                 Home
about/index.html           About / biography
speaking/index.html        Speaking, testimonials, talk list
writing/index.html         Blog index (Tortoise blog + 2018 archive)
writing/<slug>/index.html  One directory per post
newsletter/index.html      Newsletter signup
book/index.html            Contact / booking
404.html                   Not-found page

assets/css/site.css        The whole design system (one file)
assets/js/site.js          ~80 lines: mobile nav, footer year, form behaviour
assets/img/                Images — all WebP, all self-hosted

_redirects                 Old Squarespace URLs -> new paths (301s)
_headers                   Security + cache headers
sitemap.xml, robots.txt
```

## Editing

Everything is hand-written HTML. Open a file and change the text.

**Shared chrome (nav + footer) is duplicated in each page.** There is no include
system by design — it keeps the site deployable as-is with zero tooling. If you
change the navigation, change it in every file:

```bash
grep -l 'class="nav"' index.html */index.html */*/index.html
```

Fonts come from Google Fonts (`Fraunces` for display, `Inter` for body). To go
fully self-hosted, download both families into `assets/fonts/` and replace the
`<link>` in each page's `<head>` with an `@font-face` block in `site.css`.

### Design tokens

All colour, type and spacing live in `:root` at the top of `assets/css/site.css`.
Note the two coral tokens: `--coral` (#d8462c) is for display-size text only,
`--coral-ink` (#bf3b22) is the WCAG-AA-safe variant used for small labels.

## Adding a blog post

1. `cp -r writing/ethical-disruption-is-possible writing/my-new-post`
2. In `writing/my-new-post/index.html` change `<title>`, the meta description,
   the canonical URL, the `<h1 class="post-title">`, and the body inside
   `<article class="article">`.
3. Add a row to `writing/index.html` (and optionally to the home page).
4. Add the URL to `sitemap.xml`.
5. Commit and push — Cloudflare deploys it.

## Images

All images are real WebP with a `.webp` extension, so Cloudflare serves the
correct `Content-Type`. The 1200×630 social card is `assets/img/og-image.jpg`
(JPEG on purpose — some link previewers still refuse WebP).

When adding an image, keep the `width` and `height` attributes on the `<img>`:
they reserve space and stop the page jumping as images load.

## Forms

Both forms (`/book/`, `/newsletter/`) are **not connected to a provider yet**.
Until they are, submitting shows an honest message pointing at LinkedIn rather
than pretending to send. To connect one, add the endpoint to the `<form>`:

```html
<form class="form" data-form="contact" method="post" action=""
      data-endpoint="https://formspree.io/f/XXXXXXXX">
```

`site.js` then sets the form's action and lets the browser POST normally. Any
provider that accepts a plain form POST works (Formspree, Buttondown, Kit,
Basin, Netlify Forms…).

## Deployment

Hosted on **Cloudflare Pages**, connected to this GitHub repo. Every push to
`main` deploys to production. No build command, no output directory — Cloudflare
serves the repo root.

`www.danielospina.info` redirects to the apex (`danielospina.info`) via a
Cloudflare Redirect Rule, so old `www` links land on the right pages.

Local preview:

```bash
python3 -m http.server 8907
# then open http://127.0.0.1:8907/
```

`_redirects`, `_headers` and the 404 page only take effect on Cloudflare.

## Outstanding

- [ ] **Contact + newsletter endpoints.** See *Forms* above.
- [ ] **Review the social links** in the footer and on `/book/` — they were
      carried over from the 2018 site (LinkedIn, Medium). Confirm they are
      current, and add anywhere else worth linking.
- [ ] **A portrait photo.** None existed in the Squarespace export, so the site
      is typographic. A good headshot would help the home and about pages.
- [ ] **The Team Design Canvas.** `/cipd` on the old site was an email-gated
      download; the file wasn't in the export. `/cipd` currently redirects to
      `/book/`. Re-add it if the file is recoverable.
- [ ] **`RnDAO` framing.** The About bio describes RnDAO in the present tense,
      carried over verbatim from the old site. Update if that's no longer current.

## License

Content (c) Daniel Ospina. All rights reserved.
