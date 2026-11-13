# Humble Brothers' Club, Ikirun — website

Single-page static site: everything (markup, CSS, JS, icons) lives in
`index.html`. It is published from `main` by GitHub Pages at
<https://www.humblebrothersclub.com.ng>.

Preview locally from the project root:

```bash
python -m http.server 8000    # then open http://127.0.0.1:8000
```

## Adding a member

1. Run the helper with the member's photo:

   ```bash
   python tools/member_photo.py photos/new-member.jpg \
       --name "Ade Bello" --occupation "Trader"
   ```

   Add `--role "Chairman" --bio "Chairs the house."` for an office holder.
   It writes `assets/members/webp/<slug>-480.webp` and `<slug>-full.webp` (a
   single `-full` file if the photo is already under 480 px) and prints the
   markup for the roll of members, the gallery and (if `--role` is given) the
   executive cards.

2. Paste the printed blocks into `index.html`: the member card after the last
   `member-card`, the gallery tile beside the other member tiles, and the
   leader card after the last `leader-card`.

3. Commit the two new `.webp` files together with `index.html`, then push.

All portraits are served as a 480 px and a full-width WebP pair picked by
`srcset`/`sizes`, so don't add plain `<img src="….jpg">` tags by hand. The
original JPEGs stay in `assets/members/` as sources; they are not loaded by the
page.

## Not published

`members folders/` (source photos and hand-written member notes) and
`backups/` are listed in `.gitignore` and must stay out of the repo — they
contain personal phone numbers.
