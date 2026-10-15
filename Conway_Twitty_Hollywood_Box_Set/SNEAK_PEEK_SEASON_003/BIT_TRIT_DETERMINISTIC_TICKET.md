# Conway & Twitty — Deterministic BIT–TRIT Ticket 003

Created by Richard Stein. All Rights Reserved.

**Status:** Public-safe fictional programmatic ticket specification, not a blockchain transaction, minted token, cryptographic signature, or issued admission right. No private key or personal artwork included. This document supplements the canonical Season 003 Sneak Peek and Episode 319; it does not replace them.

## Fixed encoding

- Eight binary digits: integers 0–255, yielding 2^8 = 256 possibilities.
- Twelve ternary digits: integers 0–531440, yielding 3^12 = 531441 possibilities.
- Total ordered bit–trit pairs: 256 × 531441 = **136048896**.
- State index: `index = bit * 531441 + trit` (zero-based).
- Ticket: `BITTRIT-003-` followed by the state index padded with leading zeros to **9 decimal digits**.
- Binary representation: `bit.toString(2).padStart(8, '0')`.
- Ternary representation: `trit.toString(3).padStart(12, '0')`.
- The encoding is injective over the stated domains and deterministic. SHA-256 of exact UTF-8 ticket bytes is deterministic but does not establish authorship or a signature.

## Reference implementation (Python 3)

```python
import hashlib

TRIT_BASE = 3 ** 12
def ticket(bit: int, trit: int) -> dict:
    if type(bit) is not int or not 0 <= bit < 2**8:
        raise ValueError("bit must be an integer from 0 to 255")
    if type(trit) is not int or not 0 <= trit < TRIT_BASE:
        raise ValueError("trit must be an integer from 0 to 531440")
    index = bit * TRIT_BASE + trit
    label = f"BITTRIT-003-{index:09d}"
    n, digits = trit, []
    for _ in range(12):
        digits.append(str(n % 3))
        n //= 3
    return {
        "binary": f"{bit:08b}",
        "ternary": "".join(reversed(digits)),
        "index": index,
        "ticket": label,
        "sha256": hashlib.sha256(label.encode("utf-8")).hexdigest(),
    }

assert ticket(0, 0)["index"] == 0
assert ticket(255, 531440)["index"] == 136048895
```

## TCGE stage-game mapping

A separate 9×9 board has 81 cells; one locked bottom-right cell `R9C9=09` leaves 80 playable cells. The 80-move stage rule is **not** mathematically equivalent to the 136048896 bit–trit state space. No traversal or Latin-pair proof is claimed here.

## Original fictional dialogue

JASON: "Conway! I found the ticket!"

CONWAY: "Is it the Hollywood ticket?"

JASON: "Better. It's the deterministic programmatic BIT–TRIT ticket!"

TWITTY: "Jason, show us the numbers."

PETER: "Every bit–trit pair gets exactly one ticket number. No duplicates!"

TWITTY: "And the SHA?"

JASON: "We calculate SHA-256 from the ticket's exact UTF-8 bytes. Same ticket, same hash."

CONWAY: "That's the rule, Jason. But a hash isn't a signed ticket."

BABY: "YO!"

JASON: "Am I hired?"

CONWAY: "You're hired to print the tickets. You're still fired from the lights!"

*The red light stays on.*

**0 · HOLD** for token issuance, actual admission, signing, licensing, and additional distribution.
