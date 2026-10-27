#!/usr/bin/env python3
"""Create a local, deterministic ten-minute written interview-practice worksheet."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROLES = (
    "software-engineer",
    "product-manager",
    "designer",
    "data-analyst",
    "customer-success",
)
FIELDS = {"id", "role", "prompt", "followups", "evidence_check", "common_pitfall"}
SCHEDULE = (
    ("00:00-01:00", "Choose a real example", 60),
    ("01:00-04:00", "Write an initial answer", 180),
    ("04:00-07:00", "Answer the three follow-ups", 180),
    ("07:00-09:00", "Audit the evidence", 120),
    ("09:00-10:00", "Revise one claim and choose a next step", 60),
)


def load_cards():
    """Load and validate the bundled dataset; never read the current directory."""
    path = Path(__file__).resolve().with_name("cards.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError("Unsupported cards.json schema version")
    cards = document.get("cards")
    if not isinstance(cards, list) or len(cards) != 20:
        raise ValueError("cards.json must contain exactly 20 cards")
    ids = set()
    for card in cards:
        if not isinstance(card, dict) or set(card) != FIELDS:
            raise ValueError("Each card must have the documented six fields")
        for field in FIELDS - {"followups"}:
            if not isinstance(card[field], str) or not card[field].strip():
                raise ValueError("Card text fields must be non-empty strings")
        if card["role"] not in ROLES or card["id"] in ids:
            raise ValueError("Cards must have supported roles and unique IDs")
        ids.add(card["id"])
        followups = card["followups"]
        if (not isinstance(followups, list) or len(followups) != 3
                or any(not isinstance(item, str) or not item.strip() for item in followups)):
            raise ValueError("Each card must have three non-empty follow-ups")
    if Counter(card["role"] for card in cards) != Counter({role: 4 for role in ROLES}):
        raise ValueError("Each supported role must have four cards")
    return cards


def choose_card(cards, role, seed):
    """Stable selection for the same dataset, role and integer seed."""
    if role not in ROLES:
        raise ValueError("Unsupported role: " + role)
    pool = [card for card in cards if card["role"] == role]
    if not pool:
        raise ValueError("No cards for role: " + role)
    # Hash ordering avoids reliance on Python's randomized hash or PRNG versions.
    def rank(card):
        value = f'{role}|{seed}|{card["id"]}'.encode("utf-8")
        return hashlib.sha256(value).digest(), card["id"]
    return min(pool, key=rank)


def render_session(card, seed):
    """Return a worksheet, not a timer or an assessment of an answer."""
    role = card["role"].replace("-", " ").title()
    followups = "\n".join(f'{i}. {question}' for i, question in enumerate(card["followups"], 1))
    return f"""# Interview evidence cards: ten-minute written practice

Role: {role}
Card: {card["id"]}
Seed: {seed}

These are original practice prompts, not validated employer interview questions.
Use your own timer. This worksheet does not run a timer, record answers or grade you.
Keep employer, customer and personal details out of shared notes.

## {SCHEDULE[0][0]} | {SCHEDULE[0][1]}

Choose a work, study, volunteer or personal-project example you can describe honestly.
Note your responsibility and the people who did the other work. If you have no
matching experience, label a hypothetical response clearly; do not invent a history.

## {SCHEDULE[1][0]} | {SCHEDULE[1][1]}

{card["prompt"]}

Write four to six sentences. Separate what happened from what you inferred.
Leave a placeholder for any detail you cannot remember.

## {SCHEDULE[2][0]} | {SCHEDULE[2][1]}

Spend one minute on each question.

{followups}

## {SCHEDULE[3][0]} | {SCHEDULE[3][1]}

{card["evidence_check"]}

Mark each important claim:
- Supported: I can identify a source or a specific observation.
- Uncertain: I remember it, but need to check.
- Missing: I do not have the evidence.

These are reminders for your own review, not a score of interview readiness.
Common pitfall: {card["common_pitfall"]}

## {SCHEDULE[4][0]} | {SCHEDULE[4][1]}

Rewrite one overstated or vague sentence. Keep the uncertainty where it belongs.
Record one next step: what to verify, where to look, and when to check it.
Your result is a revised answer plus a short evidence-to-check list.
"""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print a reproducible ten-minute written practice worksheet. No network or grading.",
    )
    parser.add_argument("--role", required=True, choices=ROLES, help="Role to practise")
    parser.add_argument("--seed", required=True, type=int, help="Integer seed; keep it to repeat the selection")
    parser.add_argument(
        "--export", type=Path, metavar="PATH",
        help="Also save Markdown to this explicit NEW file; parent directory must exist",
    )
    args = parser.parse_args(argv)
    try:
        card = choose_card(load_cards(), args.role, args.seed)
        session = render_session(card, args.seed)
        if args.export is not None:
            destination = args.export.expanduser()
            with destination.open("x", encoding="utf-8", newline="\n") as output:
                output.write(session)
        sys.stdout.write(session)
        if args.export is not None:
            print(f"Saved Markdown to {destination}", file=sys.stderr)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
