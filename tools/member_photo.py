#!/usr/bin/env python3
"""Turn a new member photo into the WebP pair the site serves, plus its markup.

Every portrait on the site ships as two sizes - a 480 px copy and a full-width
copy capped at 1280 px - and the browser picks between them with srcset/sizes.
This script produces that pair and prints copy-paste HTML for the three places
a member can appear: the roll of members, the gallery grid, and the executive
cards.

Run it from anywhere inside the project:

    python tools/member_photo.py photos/ade.jpg --name "Ade Bello" \\
        --occupation "Trader"

    python tools/member_photo.py photos/chair.jpg --name "Ade Bello" \\
        --occupation "Trader" --role "Chairman" --bio "Chairs the house."

Then paste the printed block where it belongs and commit the two new .webp
files together with index.html. Existing files are never overwritten unless
you pass --force.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "members" / "webp"
SMALL_WIDTH = 480
MAX_WIDTH = 1280
SMALL_QUALITY = 72
FULL_QUALITY = 78

# Keep these in sync with the sizes="" values used in index.html.
SIZES = {
    "member": "(max-width:380px) 92vw, (max-width:640px) 45vw, (max-width:1040px) 30vw, 23vw",
    "leader": "(max-width:640px) 92vw, (max-width:1040px) 46vw, 30vw",
    "gallery": "(max-width:400px) 92vw, (max-width:640px) 45vw, (max-width:1080px) 31vw, 23vw",
}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        sys.exit("Could not build a file name from that name; pass --slug.")
    return slug


def load_rgb(path: Path):
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - environment issue
        sys.exit("Pillow is required: pip install Pillow")

    try:
        image = Image.open(path)
    except OSError as exc:
        sys.exit(f"Cannot read {path}: {exc}")

    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        flat = Image.new("RGB", image.size, (255, 255, 255))
        flat.paste(image, mask=image.split()[-1])
        return flat
    return image.convert("RGB")


def write_variants(image, slug: str, force: bool):
    from PIL import Image

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    small_w = min(SMALL_WIDTH, image.width)
    full_w = min(image.width, MAX_WIDTH)

    if small_w == full_w:
        # Source is already small: one untouched-size file is all we can offer.
        plan = [(f"{slug}-full.webp", full_w, FULL_QUALITY)]
    else:
        plan = [
            (f"{slug}-480.webp", small_w, SMALL_QUALITY),
            (f"{slug}-full.webp", full_w, FULL_QUALITY),
        ]

    written = []
    for filename, width, quality in plan:
        path = OUT_DIR / filename
        if path.exists() and not force:
            sys.exit(f"{path.relative_to(ROOT)} already exists - pass --force to overwrite")
        height = round(image.height * width / image.width)
        image.resize((width, height), Image.LANCZOS).save(
            path, "WEBP", quality=quality, method=6
        )
        written.append((path, width, path.stat().st_size))
    return written


def img_attributes(
    variants, context: str, alt: str, lazy: bool = True, raw_alt: bool = False
) -> str:
    src = f'src="{variants[-1][0].relative_to(ROOT).as_posix()}"'
    if len(variants) > 1:
        candidates = ", ".join(
            f"{path.relative_to(ROOT).as_posix()} {width}w" for path, width, _ in variants
        )
        src = f'{src} srcset="{candidates}"'
    loading = ' loading="lazy"' if lazy else ""
    alt_value = alt if raw_alt else html.escape(alt, quote=True)
    return f'{src} sizes="{SIZES[context]}" alt="{alt_value}"{loading}'


def member_card(name: str, occupation: str, attrs: str, delay: int) -> str:
    return f"""        <article class="member-card reveal" data-delay="{delay}">
          <div class="member-photo-wrap">
            <img class="member-photo" {attrs}>
          </div>
          <div class="member-card-body">
            <h4 class="member-name">{name}</h4>
            <span class="member-tag">Member</span>
            <p class="member-occ">{occupation}</p>
          </div>
        </article>"""


def gallery_tile(name: str, occupation: str, attrs: str) -> str:
    return (
        f'      <button class="g-item reveal" data-cat="members" '
        f'data-cap="{name} &mdash; {occupation}"><img {attrs}>'
        f'<span class="g-cap"><svg aria-hidden="true"><use href="#i-expand"/></svg>'
        f"{name}</span></button>"
    )


def leader_card(name: str, role: str, bio: str, attrs: str, delay: int) -> str:
    bio_line = bio or "Add one sentence on what this office does for the house."
    return f"""      <article class="leader-card reveal" data-delay="{delay}">
        <div class="leader-photo-wrap">
          <img class="leader-photo" {attrs}>
        </div>
        <div class="leader-card-body">
          <h3>{name}</h3>
          <p class="leader-role">{role}</p>
          <p class="leader-bio">{bio_line}</p>
        </div>
      </article>"""


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build the 480/full WebP pair for a member photo and print its markup."
    )
    parser.add_argument("photo", type=Path, help="path to the original photo")
    parser.add_argument("--name", required=True, help='display name, e.g. "Ade Bello"')
    parser.add_argument("--occupation", default="Member", help="occupation shown on cards")
    parser.add_argument(
        "--role",
        default=None,
        help='office held, e.g. "Chairman"; adds the executive card block',
    )
    parser.add_argument("--bio", default="", help="one line about the office (executives only)")
    parser.add_argument("--slug", default=None, help="file name stem (default: from --name)")
    parser.add_argument("--delay", type=int, default=1, help="reveal stagger slot, 1-5")
    parser.add_argument("--force", action="store_true", help="overwrite existing webp files")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    # Keep printed markup identical no matter the console code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    if not args.photo.is_file():
        sys.exit(f"No such photo: {args.photo}")
    if not (ROOT / "index.html").is_file():
        sys.exit(f"Run this inside the site project (no index.html in {ROOT})")

    slug = args.slug or slugify(args.name)
    name = html.escape(args.name)
    occupation = html.escape(args.occupation)
    role = html.escape(args.role) if args.role else None

    image = load_rgb(args.photo)
    variants = write_variants(image, slug, args.force)

    member_attrs = img_attributes(variants, "member", args.name)
    gallery_attrs = img_attributes(variants, "gallery", args.name)

    print(f"Source: {args.photo} - {image.width}x{image.height}")
    for path, width, size in variants:
        print(f"  wrote {path.relative_to(ROOT).as_posix()}  {width}px  {size / 1024:.0f} KB")

    print("\n--- 1) Roll of members: paste after the last .member-card ---\n")
    print(member_card(name, occupation, member_attrs, args.delay))

    print("\n--- 2) Gallery: paste beside the other member tiles ---\n")
    print(gallery_tile(name, occupation, gallery_attrs))

    if role:
        # &mdash; keeps the printed markup pure ASCII so it pastes cleanly
        # out of any Windows console or terminal.
        leader_alt = f'{html.escape(args.name, quote=True)} &mdash; {html.escape(args.role, quote=True)}'
        leader_attrs = img_attributes(variants, "leader", leader_alt, raw_alt=True)
        print("\n--- 3) Executive council: paste after the last .leader-card ---\n")
        print(leader_card(name, role, html.escape(args.bio), leader_attrs, args.delay))

    print("\nCommit the new .webp files together with index.html.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
