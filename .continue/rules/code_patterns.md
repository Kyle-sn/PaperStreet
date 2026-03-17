# Preferred Code Patterns

## Logging

Always use:

from utils.log_config import setup_logger

logger = setup_logger(__name__)

---

## IB Usage

Always reuse IBApp.

Do not create new IB clients.

---

## Structure

Prefer:

- small functions
- explicit parameters
- no hidden state

Avoid:

- large monolithic functions
- implicit globals