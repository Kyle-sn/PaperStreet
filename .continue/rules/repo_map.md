# Repository Map

## Core Files

- ib_app.py
  Central Interactive Brokers interface

## Key Directories

- positions/
  Position and account update handling

- orders/
  Order types and order management

- utils/
  Logging, constants, helpers

## Important Entry Points

- positions/position_handler.py
  Handles account subscriptions and updates related to positions

- orders/order_handler.py
  Handles account subscriptions and updates related to orders

## Common Imports

- from utils.log_config import setup_logger
- from utils.connection_constants import *