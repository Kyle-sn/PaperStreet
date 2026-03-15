# PaperStreet Project Architecture

PaperStreet is a Python trading infrastructure project that interacts with the Interactive Brokers API.

## Key Directories

### v2/
Contains the main application code.

Important modules:

- v2/positions/
  Handles account position monitoring and account updates from Interactive Brokers.

- v2/utils/
  Utility modules including:
  - logging configuration
  - connection constants
  - shared helpers

- v2/ib_app.py
  Core Interactive Brokers API wrapper used across the project.

## Positions Module

Files inside `v2/positions` manage account data retrieval.

Example:

v2/positions/position_handler.py
- Connects to Interactive Brokers
- Requests account summary
- Subscribes to account updates
- Subscribes to position updates

Uses:
- IBApp class
- connection constants
- logging utilities

## Coding Standards

- Python project
- Modular structure under v2/
- Logging handled through utils.log_config
- Connection constants stored in utils.connection_constants
