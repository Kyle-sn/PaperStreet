# Trading System Rules

This project implements a Python-based trading system using the Interactive Brokers API.

These rules define **how trading-related code must behave**, independent of specific file structure.

---

# Core Principles

- The system is **event-driven**, not request/response based
- Broker communication is **asynchronous**
- State is updated via **callbacks and subscriptions**
- Trading logic must be **deterministic and observable**

---

# Broker Interaction Rules

All communication with Interactive Brokers must:

- go through a centralized broker interface (e.g., IBApp)
- follow the IB API connection lifecycle
- respect asynchronous event handling

## Connection Lifecycle (Invariant)

The connection flow follows this pattern:

1. Initialize client
2. Connect to IB
3. Wait for `nextValidId`
4. Start event loop (`run()`)

Do not modify this lifecycle unless explicitly instructed.

---

# Event-Driven Architecture

The system relies on IB API callbacks.

Examples of event sources:

- account summary updates
- position updates
- portfolio updates

## Rules

- Do not convert event-driven flows into polling loops
- Do not block the event loop
- Do not assume synchronous responses from IB API calls

---

# State Management

Account and position state must:

- be updated only from IB callbacks
- reflect the latest broker data
- avoid duplication or conflicting sources of truth

Avoid:

- manually overriding broker state
- caching values without update mechanisms

---

# Order Safety Rules (Critical)

When implementing trading or order logic:

- Never submit duplicate orders unintentionally
- Always log order submissions
- Ensure order parameters are explicit and validated

If order behavior is unclear:
- do not guess
- ask for clarification

---

# Logging Requirements

All trading-related actions must be logged.

This includes:

- connection events
- subscription requests
- incoming updates
- order submissions

Use the shared logging utilities.

Do not introduce custom logging systems.

---

# Long-Running Processes

Trading scripts typically run as long-lived processes.

Rules:

- do not prematurely terminate event loops
- do not add blocking logic after `run()`
- ensure graceful handling of long-running execution

---

# Code Design Rules

When implementing trading-related logic:

- keep broker interaction separate from business logic
- prefer small, testable functions
- avoid hidden side effects
- make data flow explicit

---

# When Modifying Trading Code

Always:

- preserve event-driven behavior
- maintain compatibility with IB API patterns
- reuse existing infrastructure

Never:

- introduce synchronous assumptions
- bypass the broker interface
- create parallel connection logic

---

# Handling Uncertainty

If trading behavior or system design is unclear:

- do not invent logic
- do not assume missing components
- ask for clarification
