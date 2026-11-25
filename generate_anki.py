#!/usr/bin/env python3
"""Build an Anki deck from one or more JSON language-learning data files.

Vocabulary is retained as a reference bank without cards by default.
Contextual practice creates the study cards; vocabulary cards can be enabled
explicitly.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import genanki

MODEL_ID = 1_847_302_655
DECK_ID = 1_847_302_652
DEFAULT_DATA = Path(__file__).parent / "data" / "bulgarian.json"

FIELDS = [
    "ID", "Bulgarian", "Transliteration", "English",
    "Bulgarian_Sentence", "English_Sentence", "Notes", "Topic",
    "MakeRecognition", "MakeRecall", "MakeSentence",
    "Cloze_Prompt", "Cloze_Answer", "Practice_Prompt", "Practice_Answer",
    "MakeComprehension", "MakeProduction", "MakeCloze", "MakeCorrection",
    "MakeDialogue", "MakeTranslationCloze",
]

CSS = """
.card { font-family: Arial, sans-serif; font-size: 22px; line-height: 1.55;
        text-align: center; color: #222; background: #fff; padding: 1em; }
.answer { margin-top: 1em; }
.hint { margin-top: .8em; font-size: 15px; color: #666; }
.prompt { white-space: pre-wrap; }
.bulgarian { font-size: 25px; }
"""

TEMPLATES = [
    ("Recognition", "MakeRecognition", "{{Bulgarian}}",
     "{{English}}<div class='hint'>{{Transliteration}}</div>"),
    ("Recall", "MakeRecall", "{{English}}",
     "<div class='bulgarian'>{{Bulgarian}}</div><div class='hint'>{{Transliteration}}</div>"),
    ("Sentence", "MakeSentence", "{{English_Sentence}}",
     "<div class='bulgarian'>{{Bulgarian_Sentence}}</div><div class='hint'>{{Transliteration}}</div>"),
    ("Comprehension", "MakeComprehension", "<div class='bulgarian'>{{Bulgarian}}</div>",
     "{{English}}<div class='hint'>{{Transliteration}}</div>"),
    ("Production", "MakeProduction", "{{English}}",
     "<div class='bulgarian'>{{Bulgarian}}</div><div class='hint'>{{Transliteration}}</div>"),
    ("Bulgarian cloze", "MakeCloze", "{{Cloze_Prompt}}",
     "<b>{{Cloze_Answer}}</b><div class='answer bulgarian'>{{Bulgarian}}</div>"
     "<div class='hint'>{{Transliteration}}<br>{{English}}</div>"),
    ("Error correction", "MakeCorrection", "{{Practice_Prompt}}",
     "<div class='bulgarian'>{{Practice_Answer}}</div>"
     "<div class='hint'>{{Transliteration}}<br>{{English}}</div>"),
    ("Dialogue", "MakeDialogue", "{{Practice_Prompt}}",
     "<div class='answer'>{{Practice_Answer}}</div>"
     "<div class='hint bulgarian'>{{Bulgarian}}</div><div class='hint'>{{Transliteration}}</div>"),
    ("English-cued cloze", "MakeTranslationCloze", "{{Practice_Prompt}}",
     "<b>{{Practice_Answer}}</b><div class='answer bulgarian'>{{Bulgarian}}</div>"
     "<div class='hint'>{{Transliteration}}<br>{{English}}</div>"),
]

PRACTICE_CATEGORIES = {
    "comprehension", "production", "cloze", "correction", "dialogue", "translation_cloze",
}


def build_model():
    templates = []
    for name, flag, front, back in TEMPLATES:
        templates.append({
            "name": name,
            "qfmt": f"{{{{#{flag}}}}}<div class='prompt'>{front}</div>{{{{/{flag}}}}}",
            "afmt": (
                "{{FrontSide}}<hr id='answer'>"
                f"{{{{#{flag}}}}}<div class='answer'>{back}</div>{{{{/{flag}}}}}"
                "{{#Notes}}<div class='hint'>{{Notes}}</div>{{/Notes}}"
                "{{#Topic}}<div class='hint'>Topic: {{Topic}}</div>{{/Topic}}"
            ),
        })
    return genanki.Model(
        MODEL_ID, "Bulgarian Learning - Anki A1",
        fields=[{"name": field} for field in FIELDS],
        templates=templates, css=CSS,
    )


def blank_fields():
    return [""] * len(FIELDS)


def put(fields, **values):
    indexes = {name: i for i, name in enumerate(FIELDS)}
    for name, value in values.items():
        fields[indexes[name]] = "" if value is None else str(value)
    return fields


def flag(fields, name):
    fields[FIELDS.index(name)] = "yes"


def validate_text(entry, keys, label):
    if not isinstance(entry, dict):
        raise ValueError(f"{label}: expected a JSON object")
    for key in keys:
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            raise ValueError(f"{label}: '{key}' is required and must be non-empty text")
    for key in ("translit", "notes"):
        if not isinstance(entry.get(key, ""), str):
            raise ValueError(f"{label}: '{key}' must be text")


def slug(value):
    value = re.sub(r"[^a-z0-9_]+", "_", value.casefold())
    return value.strip("_") or "general"


def load_data_files(paths):
    """Load and combine data files in the order supplied.

    Exact duplicate vocabulary entries are included only once. If the same
    Bulgarian expression has different content, loading fails so that data
    conflicts are resolved explicitly. Practice entries are concatenated;
    their IDs are checked globally when cards are created.
    """
    combined = {
        "schema_version": 3,
        "vocabulary": [],
        "practice": {},
    }
    vocabulary_by_key = {}

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON ({exc})") from exc

        if not isinstance(data, dict):
            raise ValueError(f"{path}: top-level JSON value must be an object")
        if data.get("schema_version") != 3:
            raise ValueError(f"{path}: expected JSON schema_version 3")

        vocabulary = data.get("vocabulary")
        if not isinstance(vocabulary, list):
            raise ValueError(f"{path}: expected 'vocabulary' to be a list")

        for position, entry in enumerate(vocabulary, 1):
            label = f"{path}: vocabulary entry {position}"
            validate_text(entry, ("bg", "en", "bg_sentence", "en_sentence"), label)
            key = re.sub(r"\s+", " ", entry["bg"].strip()).casefold()
            existing = vocabulary_by_key.get(key)
            if existing is None:
                vocabulary_by_key[key] = entry
                combined["vocabulary"].append(entry)
            elif existing != entry:
                raise ValueError(
                    f"{path}: conflicting duplicate vocabulary item '{entry['bg']}'. "
                    "Keep one canonical definition or make the entries consistent."
                )

        practice = data.get("practice", {})
        if not isinstance(practice, dict):
            raise ValueError(f"{path}: expected 'practice' to be an object")
        unknown_categories = set(practice) - PRACTICE_CATEGORIES
        if unknown_categories:
            raise ValueError(
                f"{path}: unknown practice categories: {', '.join(sorted(unknown_categories))}"
            )

        for category, entries in practice.items():
            if not isinstance(entries, list):
                raise ValueError(f"{path}: practice.{category} must be a list")
            combined["practice"].setdefault(category, []).extend(entries)

    if not paths:
        raise ValueError("No data files supplied")
    return combined


def add_vocabulary(deck, model, entries, cards):
    count = 0
    seen = set()
    for pos, entry in enumerate(entries, 1):
        label = f"vocabulary entry {pos}"
        validate_text(entry, ("bg", "en", "bg_sentence", "en_sentence"), label)
        key = re.sub(r"\s+", " ", entry["bg"].strip()).casefold()
        if key in seen:
            raise ValueError(f"{label}: duplicate vocabulary item '{entry['bg']}'")
        seen.add(key)
        f = blank_fields()
        stable_id = "vocab:" + key
        put(f, ID=stable_id, Bulgarian=entry["bg"], Transliteration=entry.get("translit", ""),
            English=entry["en"], Bulgarian_Sentence=entry["bg_sentence"],
            English_Sentence=entry["en_sentence"], Notes=entry.get("notes", ""),
            Topic=entry.get("topic", "general_a1"))
        for card in cards:
            flag(f, {"recognition": "MakeRecognition", "recall": "MakeRecall",
                     "sentence": "MakeSentence"}[card])
        guid = genanki.guid_for("bulgarian-anki:vocabulary:" + key)
        tags = ["bulgarian", "vocabulary", slug(entry.get("topic", "general_a1"))]
        deck.add_note(genanki.Note(model=model, fields=f, guid=guid, tags=tags))
        count += 1
    return count


def add_practice(deck, model, categories):
    count = 0
    type_config = {
        "comprehension": ("MakeComprehension", "bg", "en"),
        "production": ("MakeProduction", "en", "bg"),
        "cloze": ("MakeCloze", "prompt", "answer"),
        "correction": ("MakeCorrection", "prompt", "answer"),
        "dialogue": ("MakeDialogue", "prompt", "answer"),
        "translation_cloze": ("MakeTranslationCloze", "prompt", "answer"),
    }
    seen_ids = set()
    for category, entries in categories.items():
        if category not in type_config:
            raise ValueError(f"Unknown practice category: {category}")
        if not isinstance(entries, list):
            raise ValueError(f"practice.{category} must be a list")
        flag_name, front_key, back_key = type_config[category]
        for pos, entry in enumerate(entries, 1):
            stable_id = entry.get("id") if isinstance(entry, dict) else None
            if not isinstance(stable_id, str) or not stable_id.strip():
                raise ValueError(f"practice.{category} entry {pos}: stable 'id' required")
            if stable_id in seen_ids:
                raise ValueError(f"Duplicate practice id across input files: {stable_id}")
            seen_ids.add(stable_id)
            label = f"practice.{category}/{stable_id}"
            required = ("bg", "en") if category in ("comprehension", "production") else (
                "bg", "en", "prompt", "answer")
            validate_text(entry, required, label)
            f = blank_fields()
            put(f, ID=stable_id, Bulgarian=entry["bg"], Transliteration=entry.get("translit", ""),
                English=entry["en"], Bulgarian_Sentence=entry["bg"],
                English_Sentence=entry["en"], Notes=entry.get("notes", ""),
                Topic=entry.get("stage", "module_1_review"))
            if category == "cloze":
                put(f, Cloze_Prompt=entry["prompt"], Cloze_Answer=entry["answer"])
            else:
                put(f, Practice_Prompt=entry[front_key], Practice_Answer=entry[back_key])
            flag(f, flag_name)
            guid = genanki.guid_for(f"bulgarian-anki:practice:{category}:{stable_id}")
            tags = ["bulgarian", "practice", slug(category), slug(entry.get("stage", "module_1_review"))]
            deck.add_note(genanki.Note(model=model, fields=f, guid=guid, tags=tags))
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Build an Anki deck from one or more JSON data files"
    )
    parser.add_argument(
        "--data",
        type=Path,
        nargs="+",
        default=[DEFAULT_DATA],
        metavar="JSON",
        help="JSON data files to combine, in processing order (default: data/bulgarian.json)",
    )
    parser.add_argument("-o", "--output", type=Path, default=Path("bulgarian-anki.apkg"))
    parser.add_argument("--deck-name", default="Bulgarian")
    parser.add_argument(
        "--cards",
        nargs="*",
        choices=["recognition", "recall", "sentence"],
        default=[],
        help="Optional vocabulary card types; by default only contextual practice creates cards",
    )
    args = parser.parse_args()

    try:
        data = load_data_files(args.data)
        model = build_model()
        deck = genanki.Deck(DECK_ID, args.deck_name)
        vocabulary_count = add_vocabulary(deck, model, data["vocabulary"], set(args.cards))
        practice_count = add_practice(deck, model, data["practice"])
        genanki.Package(deck).write_to_file(str(args.output))
        print(
            f"Created {args.output}: 1 deck, {vocabulary_count + practice_count} notes "
            f"({vocabulary_count} unique vocabulary + {practice_count} contextual practice) "
            f"from {len(args.data)} data file(s)."
        )
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
