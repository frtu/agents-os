# Config

Defaults, overridable by invocation parameter or environment variable.

| Setting | Default | Override |
| --- | --- | --- |
| Workspace root | `~/Workspaces` | positional arg > `WORKSPACES_ROOT` env var > default |
| Origin vault | folder named `global-inbox` in the root | `--origin {name}` |
| Transcript location | `{vault}/vault/raw/transcripts/**` or `{vault}/raw/transcripts/**` (both layouts probed) | — |
| Transcript extension | `.md` only | edit `TRANSCRIPT_EXTS` in `scan_inbox.py` |

## Matching rule

A transcript counts as **copied** when a file in a target vault has the same
name after: stripping the leading `YYYY-MM-DD` date stamp, lower-casing, and
collapsing `-`/`_`/spacing. Sub-folder location in the target is irrelevant
(the category is chosen when proposing, not when matching).
