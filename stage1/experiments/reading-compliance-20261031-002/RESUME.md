# Resume after Colab GPU usage limit

Verified 31 October 2026 at 16:52 UTC: Colab reports “You cannot currently connect to a GPU due to usage limits in Colab.” The previous runtime is disconnected. No purchase or hardware/precision substitution is authorized.

The unchanged-300 run completed 114 updates, all three checkpoint reloads, and 34 raw responses per epoch. The current comparator also has 34 raw responses, including one preserved truncation. The expanded run has 185 logged updates but retained resumable epoch checkpoints only at 75 and 150. Resume from checkpoint-150, replaying the final 75 updates; do not treat logged updates as resumable state.

Use the sealed notebook and kit after free T4 access returns. Re-establish its allocator-before-torch setup, verified kit, dependency checks, offline tests and existing Drive mount. Preserve the Drive output directory. In cell 5, set:

```python
ONLY = 'expanded600'
RESUME = OUTPUT / 'expanded600/full/checkpoints/checkpoint-150'
```

Then execute cell 6. The existing executor checks identity, model bytes, environment parity and retained checkpoint hashes before restoring optimizer/scheduler/scaler/RNG. It preserves completed comparator and same300 responses. Resume is not verified until these live gates and final training/reload gates succeed. Large adapter/optimizer files are retained in Drive; their present listings do not substitute for full byte verification on resume.

Drive output: https://drive.google.com/drive/folders/1GP8CDHTPPSm8JYFCVGKY37UqrdaJjcLa

Notebook: https://colab.research.google.com/drive/1gqdgp3o34M-f9nPTNI5xQ_vAS8kSrmTj?authuser=1

After expanded training and its three generations finish, run cells 7–8 for verified loss plots and blinded review packaging. Review all seven response groups (238 raw responses), with candidate identities concealed until independent ratings are sealed. Only then summarize, select, and conditionally execute the two repeat seeds. The full primary comparison and adoption decision remain pending. Human data review also remains pending.

The sealed README and manifest describe preparation-time state. status.json and this continuation record describe the later execution state; sealed artifacts have not been rewritten.
