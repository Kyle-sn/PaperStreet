# PaperStreet Project Architecture

PaperStreet is a Python trading infrastructure project that interacts with the Interactive Brokers API.

## Key Directories

### root directory
Contains the main application code.

Important modules:

- positions/
  Handles account position monitoring and account updates from Interactive Brokers.

- utils/
  Utility modules including:
  - logging configuration
  - connection constants
  - shared helpers

- ib_app.py
  Core Interactive Brokers API wrapper used across the project.

## Positions Module

Files inside `positions` manage account data retrieval.

Example:

positions/position_handler.py
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
- Modular structure under the root directory
- Logging handled through utils.log_config
- Connection constants stored in utils.connection_constants
