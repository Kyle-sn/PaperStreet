# Python Trading System Guidelines

This project is a Python-based trading infrastructure that interacts with the Interactive Brokers API.

The codebase focuses on account monitoring, position tracking, and broker communication.

## Architecture Overview

The main application code is located in the `v2/` directory.

Important modules:

- `v2/ib_app.py`
  Core wrapper around the Interactive Brokers API. Other modules rely on this class for broker connectivity.

- `v2/positions/`
  Contains logic for retrieving and monitoring account positions and account summary data.

- `v2/utils/`
  Shared utilities including logging configuration and connection constants.

## Trading System Design Patterns

This project follows common event-driven trading architecture patterns.

Key patterns:

### Broker Connection Layer
Connections to Interactive Brokers are established through the IBApp class.

Typical flow:
1. Create IBApp instance
2. Connect using host, port, and clientId
3. Wait for nextValidId event
4. Begin event loop using `app.run()`

Agents should not modify this connection flow unless explicitly requested.

### Event-Driven Updates

The system relies on IB API callbacks and subscriptions.

Examples include:
- account summary updates
- portfolio updates
- position updates

Subscriptions are initiated through functions such as:
- `reqAccountSummary`
- `reqAccountUpdates`
- `reqPositions`

These trigger asynchronous updates handled by IBApp callbacks.

### Long-Running Event Loops

Scripts typically end with:

