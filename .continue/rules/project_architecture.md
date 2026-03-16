# PaperStreet Project Architecture

PaperStreet is a Python trading infrastructure project that interacts with the Interactive Brokers API.

The system focuses on **account monitoring, position tracking, and broker communication**.

---

# Core Architecture Principles

The project follows these architectural rules:

- Broker communication is centralized through `ib_app.py`
- Modules should **not directly implement IB API clients**
- Logging must use the shared logging utilities in `utils`
- Connection constants must come from `utils.connection_constants`
- Modules should remain **loosely coupled and reusable**

Avoid introducing unnecessary dependencies between modules.

---

# Repository Structure

## Root Directory

The root directory contains the primary application modules.

Important components:

- `ib_app.py`  
  Core wrapper around the Interactive Brokers API.

- `positions/`  
  Handles account position monitoring and account updates.

- `utils/`  
  Shared utilities used across the project.

---

# Important Modules

## ib_app.py

Central Interactive Brokers API wrapper.

Responsibilities:

- manage IB API connection
- handle client lifecycle
- provide reusable broker interface

All IB API communication should go through this module.

Other modules should **not implement their own IB API clients**.

---

## positions/

Responsible for retrieving and monitoring account state.

Typical responsibilities:

- request account summary
- subscribe to account updates
- subscribe to position updates

Example file:

`positions/position_handler.py`

This module typically:

- connects to Interactive Brokers
- subscribes to account updates
- processes position updates

Dependencies:

- `IBApp`
- `utils.connection_constants`
- `utils.log_config`

---

## utils/

Shared utilities used across the system.

Common utilities include:

- logging configuration
- connection constants
- shared helper functions

Examples:

- `utils.log_config`
- `utils.connection_constants`

---

# Import Conventions

Modules should import shared utilities using explicit imports.

Example:
