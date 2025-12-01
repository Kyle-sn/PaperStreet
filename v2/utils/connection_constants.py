# 1 = real-time, 3 = delayed
MARKET_DATA_TYPE = 3

# IP to connect to
BROKER_CONNECTION_IP = "127.0.0.1"

# Port to connect to: 7496 = prod | 7497 = paper account
BROKER_CONNECTION_PORT = 7497

# Broker API tick type string
TICK_STRING = "221"

# Symbol to request market data for
SYMBOL = "QQQ"

# Security type
SECURITY_TYPE = "STK"  # or "FUT"

# Exchange routing
EXCHANGE = "SMART"  # or "GLOBEX"

# Currency
CURRENCY = "USD"

# Positions connection client ID
#
POSITIONS_CLIENT_ID = 1

# Orders connection ID
# The Master Client ID is set in the Global Configuration and is used to distinguish the
# connecting Client ID used to pull order and orders data even from other API connections.
ORDERS_CLIENT_ID = 0

EXECUTIONS_REQUEST_ID = 1001

POSITIONS_REQUEST_ID = 2001
