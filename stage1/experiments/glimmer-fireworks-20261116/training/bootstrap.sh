#!/bin/sh
set -eu
TRAINING_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PIN=74e103ab4249d508912ccf264793e655980eead0
VENDOR="$TRAINING_DIR/vendor/cookbook"
if [ ! -d "$VENDOR/.git" ]; then
  mkdir -p "$TRAINING_DIR/vendor"
  git clone --filter=blob:none --no-checkout https://github.com/fw-ai-external/cookbook.git "$VENDOR"
fi
if [ "$(git -C "$VENDOR" rev-parse HEAD)" != "$PIN" ]; then
  git -C "$VENDOR" fetch origin "$PIN"
fi
git -C "$VENDOR" checkout --detach "$PIN"
python3 -m venv "$TRAINING_DIR/.venv"
"$TRAINING_DIR/.venv/bin/python" -m pip install --disable-pip-version-check uv==0.9.10
UV_PROJECT_ENVIRONMENT="$TRAINING_DIR/.venv" "$TRAINING_DIR/.venv/bin/uv" sync --frozen --project "$VENDOR/training" --python "$TRAINING_DIR/.venv/bin/python"
"$TRAINING_DIR/.venv/bin/python" -m pip freeze > "$TRAINING_DIR/installed-requirements.txt"
"$TRAINING_DIR/.venv/bin/python" "$TRAINING_DIR/train.py" plan
