# sft-300-v2 correction log

Frozen revision; independent model approval of v2 is pending. Human review remains pending. The full original-corpus audit found only the four issues below.

| ID | Exact content change |
|---|---|
| pilot-057 | Final child turn: `what about rain` → `what does it do` |
| pilot-065 | Final child turn: `the cold one` → `the other one` |
| pilot-096 | Final child turn: `and what about cheese` → `and what about that` |
| pilot-186 | Target: `Look under the mat. You put it there.` → `Look under the mat.` |

For 186, sentence counts are now `[4]`; the now-unused `it`, `put`, `there`, and `you` evidence entries were removed; the external rationale still identifies the supported `mat` and `box` spellings. Every changed review row has version-specific revision metadata. No revision metadata was added to other rows.

All three changed final child turns remain short inputs. Every existing input-length bucket, ID, history flag, system message, and historical assistant turn is preserved. All other 296 data rows are byte-identical. changes.jsonl records exact original and revised row objects and line strings for both files.
