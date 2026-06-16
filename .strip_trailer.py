import sys

msg = sys.stdin.read()
out = []
for line in msg.split("\n"):
    low = line.lower()
    if "claude" in low or "anthropic" in low:
        continue
    if "\U0001f916 generated with" in low or "generated with [claude" in low:
        continue
    out.append(line)
while out and out[-1].strip() == "":
    out.pop()
sys.stdout.write("\n".join(out) + "\n")
