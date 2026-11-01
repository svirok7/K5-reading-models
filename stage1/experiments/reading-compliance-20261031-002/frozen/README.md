# Frozen diagnostic cases

Frozen before successor data authoring. This is a development/diagnostic set, not unseen test evidence. No held-out test file or archived test contents were opened. The historical overlapping 13-case replay is not a source.

`cases.jsonl` contains only inference prompt/messages, identifiers, hashes, seeds, and provenance. `candidates.jsonl` preserves all 45 candidate inference inputs. Separate source and review files retain saved annotations and overlap decisions; never pass these to inference. Historical assistant messages are preserved exactly even when false or unsafe; they are context, not target answers. The current full Prompt B is used for every case.

Sources: all 20 existing dev cases and exactly 25 saved UI records whose Qwen adapter path ends in runs/qwen-sft300-v2-lora-allocator-20261030-008/adapter. SQLite opened with mode=ro. Source UI bodies are preserved as the exact stored serialized JSON; dev records are canonical snapshots and the original file hash is in the manifest. No SFT responses are used as expected answers.

Manual semantic review compared each of 45 complete histories with every one of 300 original training histories. The review records nearest concrete evidence and reasons for retention/exclusion. Shared generic skills (memory, empathy, topic changes) or safety category alone do not count as near overlap; same concrete situation/answer or greeting paraphrase does. Fish legs/running is conservatively excluded as closely related locomotion. Exact full-history duplicates are excluded, preserving the first source order (dev before chronological UI). Matching final child text with materially distinct histories remains distinct. Exclusion reasons and original candidate records are preserved.

Canonical JSON uses UTF-8, ensure_ascii=False, sort_keys=True, separators=(comma,colon), one LF per record. prompt_hash is SHA256 of exact prompt UTF-8. input_hash is SHA256 of canonical JSON {prompt,messages}. seed=(42+int(SHA256(case_id UTF-8).hexdigest()[:8],16)) modulo 2**32. Generation is pinned in manifest. File hashes cover immutable artifacts; manifest.sha256 seals manifest.json. File mode 0444 is an additional accidental-write guard, not a cryptographic immutability claim.

Reviewer is the separately delegated GPT-6.1 Sol/high session requested by the user; no automated judge/API call was used to invent semantic review.
