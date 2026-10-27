# Interview evidence cards

Twenty original prompts for a ten-minute written practice session. Pick a role, answer one prompt, work through three follow-ups and revise one claim after checking its evidence. The useful output is a more precise answer and a short list of facts to verify.

These are **practice materials, not validated employer interview questions**. They do not predict interview results, assess employability or provide hiring recommendations. No interviewing experience, credential or success rate is claimed for the author.

## Use the cards without installing anything

Open `index.html` in a browser, choose a role from the page links and read any card. All twenty cards are present in the HTML; no JavaScript, account or interview service is required.

Use a separate timer and your own paper or private notes:

1. **00:00–01:00:** choose an example you can describe honestly and identify your contribution.
2. **01:00–04:00:** write four to six sentences answering the prompt.
3. **04:00–07:00:** answer each of the three follow-ups for one minute.
4. **07:00–09:00:** use the evidence check. Mark claims supported, uncertain or missing.
5. **09:00–10:00:** revise one sentence and write one concrete verification step.

An example from study, volunteering or a personal project is fine. If you lack matching experience, label a hypothetical response; do not present it as something you did. You are not expected to disclose confidential records to practise.

**Synthetic example:** A customer-success practice note says, “Training increased adoption.” The only evidence is that four of six invited colleagues attended a session. A more accurate sentence is, “Four colleagues attended; I have not checked whether they completed the setup task.” The next step is to check the agreed setup milestone. The attendance number and scenario are invented to illustrate the distinction.

## Run the Python CLI

Requires **Python 3.9 or later** and only the standard library. Keep `drill.py` and `cards.json` in the same directory.

```sh
python drill.py --role software-engineer --seed 17
python drill.py --role customer-success --seed 42
python drill.py --role designer --seed -3 --export my-practice.md
python drill.py --help
```

On Windows, `py -3` can replace `python` if that is how Python is installed.

Supported role values:

- `software-engineer`
- `product-manager`
- `designer`
- `data-analyst`
- `customer-success`

The CLI prints **one** ten-minute worksheet, including all three follow-ups. It does not run a countdown, ask for answers or evaluate them. The same role, integer seed and dataset produce exactly the same card and worksheet; changing the seed may still select the same card because each role has four. Selection uses SHA-256 ordering of role, seed and card ID, not a network service.

Output goes to standard output. `--export PATH` additionally creates UTF-8 Markdown at the exact path you provide, relative to the current working directory unless absolute. The parent directory must already exist. Existing files are refused, including an existing empty file; choose another name to avoid overwriting work. A bad role, non-integer seed, missing data file or invalid export destination produces a nonzero exit status and an error.

## Data and maintenance

`cards.json` has `schema_version: 1` and a `cards` array. There are four cards per role. Each card has:

| Field | Meaning |
| --- | --- |
| `id` | Stable unique identifier |
| `role` | One of the five role values above |
| `prompt` | Initial practice question |
| `followups` | Exactly three further questions |
| `evidence_check` | A concrete way to inspect the claims in your answer |
| `common_pitfall` | One mistake to watch for |

The static page contains the full dataset as readable content. If a card changes, update both `cards.json` and `index.html`; the tests check their consistency. Changing card IDs or the available set can change seed selection. There is no claim that this collection covers every interview topic.

Run the checks from the project directory:

```sh
python -B -m unittest discover -s tests -v
```

Tests exercise dataset structure and balance, real CLI execution for every role, repeatability, selection coverage, explicit export, overwrite refusal and invalid input. They also check that the page contains the cards and the intended ordinary link. No installation or internet access is needed.

## Privacy and affiliation

The CLI makes **no network requests**, reads only the bundled dataset and writes only an explicitly requested export. It never asks for a resume, answer, name or email. Your terminal may retain output; an export is a plain local file. Keep private material out of files you share or publish.

The HTML has no JavaScript, forms, analytics, third-party fonts or remote asset dependencies. A hosting provider may receive normal page-request logs. Following an external link is a separate visit governed by the destination's policies.

This resource is published by the team behind MockLive / MakeInterview. The page links to that team's educational guide for context. The exercise works independently and makes no promise about the current availability of any AI interview service.

The page follows the existing public interview-follow-up checklist's simple documentation layout: a centered text column, role anchors, headings and code examples. The prompts and written drill here are new; they are not a STAR worksheet or a reproduced article.
