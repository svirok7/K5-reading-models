import os
from pathlib import Path

from sarvamai import SarvamAI

# Load the single key from the adjacent .env without another dependency.
for line in Path(__file__).with_name(".env").read_text().splitlines():
    name, separator, value = line.partition("=")
    if separator and name.strip() == "SARVAM_API_KEY":
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))

key = os.environ.get("SARVAM_API_KEY", "").strip()
if not key:
    raise SystemExit("Paste your SARVAM_API_KEY into .env first.")

client = SarvamAI(api_subscription_key=key)
response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(response.choices[0].message.content)
