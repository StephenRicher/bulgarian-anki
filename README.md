# Bulgarian Anki

A Python-based Anki deck generator for Bulgarian language learning, featuring vocabulary, contextual exercises and structured practice.

## Features

- Generate Anki decks from structured JSON data.
- Combine multiple data files into a single deck.
- Support vocabulary reference notes and active practice cards.
- Include transliteration, translations, example sentences and grammatical explanations.
- Validate input data and detect conflicting or duplicate entries.
- Configure which vocabulary card types are generated.

## Requirements

- Python 3.12+
- Poetry
- Anki (to study the generated deck)

## Setup

Clone the repository and install the dependencies:

```bash
git clone <repository-url>
cd bulgarian-anki
poetry install
```

## Usage

Generate a deck using the default data file:

```bash
poetry run python generate_anki.py
```

Specify one or more JSON data files:

```bash
poetry run python generate_anki.py \
    --data data/bulgarian.json data/additional-practice.json
```

The input files are combined into a single deck. Existing source files are not modified.

### Vocabulary cards

By default, vocabulary entries are included as reference notes without generating cards.

To generate vocabulary cards, specify one or more card types:

```bash
poetry run python generate_anki.py --cards recognition recall sentence
```

| Type | Description |
|---|---|
| `recognition` | Bulgarian to English |
| `recall` | English to Bulgarian |
| `sentence` | Practice using vocabulary in context |

### Output

The generated deck is saved as:

```text
bulgarian-anki.apkg
```

Import this file into Anki to study the deck.

## Data format

Deck content is stored in JSON files under `data/`.

Each file uses schema version `3` and contains:

- `schema_version`: schema version number.
- `description`: description of the material.
- `vocabulary`: list of vocabulary entries.
- `practice`: collection of exercises organised by category.
- `design_notes`: optional notes about the learning material and its structure.

### Vocabulary

Each vocabulary entry uses the following fields:

| Field | Description |
|---|---|
| `bg` | Bulgarian word or expression in Cyrillic |
| `translit` | Bulgarian transliteration using Latin characters |
| `en` | English meaning |
| `bg_sentence` | Example sentence in Bulgarian |
| `en_sentence` | English translation of the example sentence |
| `notes` | Relevant grammatical, linguistic or usage information |
| `topic` | Descriptive topic used to organise the material |

### Practice

Practice material is organised into six categories:

| Category | Purpose |
|---|---|
| `comprehension` | Understand Bulgarian sentences, passages and dialogues |
| `production` | Produce Bulgarian from English prompts or contextual situations |
| `cloze` | Complete missing words or grammatical forms in Bulgarian |
| `correction` | Identify and correct mistakes in Bulgarian |
| `dialogue` | Practise conversational exchanges and appropriate responses |
| `translation_cloze` | Translate English prompts into Bulgarian, with missing or prompted elements |

Each practice entry has a unique, stable `id`. Entries use category-appropriate fields such as `bg`, `en`, `prompt`, `answer`, `translit`, `notes` and `stage`. Follow the structures used in the existing data rather than introducing new fields or alternative formats.

Practice entries should contain enough information to support the relevant exercise and its explanation. Where applicable, include transliteration and substantive grammatical notes.

## Adding material

New learning material should be added as a separate JSON file under `data/`, rather than modifying existing files.

For example:

```text
data/
├── bulgarian.json
├── additional-practice.json
└── lesson-material.json
```

Each file can contain vocabulary, practice exercises, or both. Empty sections should be represented by empty lists or objects.

Pass the files to the generator using `--data`.

Vocabulary entries are deduplicated by their Bulgarian text. Conflicting entries are rejected rather than silently overwritten. Practice entries must have unique IDs across the combined input files.

## Generating new learning material with an LLM

The following prompt prefix defines the expected structure and learning approach. Paste it into a conversation before providing new lesson material, vocabulary, grammar points or themes.

### Reusable prompt prefix

```text
You are helping develop a structured Bulgarian language-learning
curriculum and generate compatible data for an existing Anki deck.

Your task is to produce a NEW, standalone JSON data file containing
high-quality learning material based on the additional context I
provide after this prompt.

The output must be compatible with the existing Python Anki
generator. Follow the schema and learning principles below exactly.

## 1. Output format

Return valid JSON only, without Markdown fences, commentary or
additional explanation.

Use this top-level structure:

{
  "schema_version": 3,
  "description": "A concise description of this material",
  "vocabulary": [],
  "practice": {
    "comprehension": [],
    "production": [],
    "cloze": [],
    "correction": [],
    "dialogue": [],
    "translation_cloze": []
  },
  "design_notes": []
}

Do not change the schema version, field names, category names or
overall structure.

Include all six practice categories, even when a category is empty.

## 2. Vocabulary schema

Each vocabulary entry must use exactly these fields:

{
  "bg": "Bulgarian word or expression in Cyrillic",
  "translit": "Bulgarian transliteration using Latin characters",
  "en": "English meaning",
  "bg_sentence": "Natural Bulgarian example sentence",
  "en_sentence": "Accurate English translation",
  "notes": "Relevant grammatical or usage explanation",
  "topic": "Descriptive topic identifier"
}

Requirements:

- Use standard contemporary Bulgarian.
- Always include the Bulgarian Cyrillic form.
- Provide consistent Latin transliteration.
- Use natural English translations rather than unnecessarily
  literal translations.
- Example sentences should demonstrate how the expression is
  actually used.
- Include relevant grammatical information in notes, such as
  gender, plural forms, verb conjugation, aspect, prepositions
  or irregularities.
- Use an empty string for notes when no explanation is necessary.
- Use descriptive, consistent topic names.
- Avoid adding vocabulary simply to increase the number of entries.
  Introduce words when they are useful for the learning material.

## 3. Practice schema

Practice entries must have a unique, stable "id".

Use the existing category-specific structure and field conventions
of the supplied reference data. Do not invent alternative schemas,
rename fields or add unnecessary metadata.

The six categories have distinct purposes:

### comprehension

Test understanding of Bulgarian.

Use natural sentences, short passages and dialogues. Questions
should assess meaning, details, grammar or interpretation rather
than simply asking for word-for-word translation.

### production

Require the learner to produce Bulgarian.

Use English prompts, contextual situations or communicative
intentions. Answers should demonstrate natural Bulgarian
construction, not merely isolated vocabulary recall.

### cloze

Test vocabulary and grammar through missing words or forms.

The learner should have to identify the appropriate word,
conjugation, grammatical form or construction from context.

### correction

Present plausible Bulgarian sentences containing errors.

Require the learner to identify and correct the errors.
Explanations should identify what was wrong and why the
correction is necessary.

### dialogue

Develop conversational competence through realistic exchanges.

Use natural questions, responses and follow-up interactions.
Include appropriate greetings, requests, answers and
conversational conventions where relevant.

### translation_cloze

Use English prompts that require Bulgarian translation,
with a particular word or grammatical construction to supply.

Test the ability to construct Bulgarian rather than simply
recognise a translation.

## 4. Pedagogical expectations

The primary objective is to develop practical Bulgarian
language competence, not to build a dictionary.

Prioritise how the language is introduced and used in context.

Learning material should progressively move from simple
recognition towards independent comprehension and production.

Use a balanced mixture of:

- Bulgarian-to-English comprehension.
- English-to-Bulgarian sentence production.
- Vocabulary and grammar cloze exercises.
- Error identification and correction.
- Question formation and answering.
- Short dialogues and conversational exchanges.
- Short passages that integrate multiple concepts.

Do not treat these as six unrelated collections of exercises.
They should reinforce the same underlying vocabulary,
grammar and communicative concepts from different angles.

Introduce new vocabulary naturally where it helps explain
or practise a concept. Do not make isolated vocabulary
the default learning activity.

Build on previously introduced material wherever possible.
Reuse familiar words and grammatical structures in new
contexts to reinforce retention.

Vary sentence structures and contexts. Avoid producing
many exercises that differ only by swapping one noun or verb.

## 5. Explanations and answer quality

Answers must be educational, not merely provide the correct
Bulgarian sentence.

Where relevant, explain:

- Why the answer is correct.
- Why a particular grammatical form is required.
- Noun gender and agreement.
- Verb conjugation and tense.
- Word order and sentence construction.
- The use of prepositions and articles.
- Differences between similar expressions.
- Why a plausible alternative would be incorrect or less natural.

Include transliteration where it helps the learner read or
produce Bulgarian.

Keep explanations concise but substantive. The learner should
be able to understand the underlying rule rather than simply
memorise the answer.

## 6. Difficulty and progression

Use the supplied lesson material and existing data to determine
the appropriate level.

Do not introduce advanced grammar or vocabulary without a
clear reason.

Progressively increase complexity by combining familiar
concepts, rather than introducing several unfamiliar concepts
in every exercise.

A good exercise should challenge the learner to apply what
they have learned, not depend on knowledge that has not yet
been introduced.

## 7. IDs and duplication

Every practice entry must have a unique, descriptive, stable ID.

IDs must not be reused across practice categories or existing
data files.

Do not duplicate existing vocabulary entries. Treat different
grammatical forms or genuinely distinct meanings carefully:
only create separate entries when they provide meaningful
learning value.

Avoid duplicating existing practice exercises or creating
superficially different versions of the same question.

If existing data is supplied, use it as the reference for
previously covered material, vocabulary, grammar, IDs and
difficulty.

Never modify or reproduce the existing source data. Generate
only the new material requested.

## 8. Final validation

Before returning the JSON, check that:

- The JSON is syntactically valid.
- The top-level structure is exact.
- All vocabulary entries contain the required fields.
- All practice entries follow the existing category structures.
- Every practice ID is unique.
- Bulgarian text uses correct Cyrillic spelling.
- Transliteration is consistent.
- English translations are accurate.
- Exercises have clear prompts and unambiguous answers.
- Explanations teach the relevant grammar or usage.
- The material is appropriately challenging and contextually
  integrated.
- No unnecessary duplicates have been introduced.

Return one complete JSON object suitable for saving as a new
file under data/.

I will now provide the additional lesson material, vocabulary,
grammar points, themes and any existing reference data.
```

### Recommended workflow

1. Start a new LLM conversation.
2. Paste the reusable prompt prefix.
3. Provide the existing `data/bulgarian.json` as reference material, so the model can avoid duplication and understand the current progression.
4. Add the new lesson notes, vocabulary, grammar points or themes.
5. Save the returned JSON as a new file under `data/`.
6. Generate the combined Anki deck using `--data`.

## Project structure

```text
bulgarian-anki/
├── data/
│   └── bulgarian.json
├── generate_anki.py
├── pyproject.toml
├── poetry.lock
├── .gitignore
└── README.md
```
