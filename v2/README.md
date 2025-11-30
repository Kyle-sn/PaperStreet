## Interactive Brokers Python API Architecture (EWrapper + EClient)
This project uses Interactive Brokers’ official Python API, which is structured around two core components:
- EWrapper — receives callbacks from TWS/Gateway
- EClient — sends requests to TWS/Gateway

For convenience, we combine them into a single class:
```python
class IBApp(EWrapper, EClient):
    def __init__(self):
        # self = the client AND the wrapper
        EClient.__init__(self, self)
        self.nextOrderId = None
```
This class is the main interface between my program and Interactive Brokers.

### How the Architecture Works
```pgsql
                    ┌──────────────────────────────┐
                    │  TWS / IB Gateway            │
                    │   (sends data + events)      │
                    └──────────────┬───────────────┘
                                   │ callbacks
                                   ▼
                      ┌────────────────────────┐
                      │       EWrapper         │
                      │  (I override these)    │
                      └──────────────┬─────────┘
                                     │ multiple inheritance
                                     ▼
                      ┌────────────────────────┐
                      │        IBApp           │
                      │ (both wrapper+client)  │
                      └──────────────┬─────────┘
                                     │ requests
                                     ▼
                      ┌────────────────────────┐
                      │        EClient         │
                      │  (I call these)        │
                      └────────────────────────┘


```

### What EWrapper Does
EWrapper defines all callback methods that IBKR automatically sends to my program:
- Connection events:
  - nextValidId
  - error
- Market data:
  - tickPrice
  - tickSize
  - historicalData
- Order lifecycle:
  - orderStatus
  - openOrder
  - execDetails
- Account/portfolio updates:
  - updatePortfolio
  - accountSummary

The base implementation in Python is literally:
```python
def tickPrice(...):
    pass  # does nothing
```
Override EWrapper Methods
I will override EWrapper methods to implement my own logic:
```python
def nextValidId(self, order_id):
    self.nextOrderId = order_id
    logger.info(f"Next order ID: {order_id}")
```
EWrapper is intended to be extended.

### What EClient Does
EClient provides all functions used to send requests to IBKR:
- connect()
- reqMktData()
- reqHistoricalData()
- placeOrder()
- cancelOrder()
- reqAccountSummary()

Example usage:
```python
app.reqMktData(1, contract, "", False, False, [])
```
EClient handles:
- Low-level network communication
- Message formatting
- Protocol sequence numbers
- Request throttling

You generally do not override EClient logic.