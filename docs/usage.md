# Usage guide

Right now there are two implementations of `AbstractExchangeHandler`:
* `BinanceFuturesExchangeHandler`
* `BitmexExchangeHandler`

They have the same functionality and all of the examples, being shown using `BinanceFuturesExchangeHandler` should be able to be used with other ones.

## Handler creation

To make requests you have to create a handler object, providing your keys data:

```python
from crypto_futures_py import BinanceFuturesExchangeHandler

# Provide your keys here
handler = BinanceFuturesExchangeHandler("public_key", "private_key")
```

Now, we are able to use handler object to make some requests.

## Requests

### Orders

To place one limit order use create_order function:

```python
data = handler.create_order(
    symbol="BTCUSDT",
    side="BUY",
    price=10000,
    volume=0.001,
    client_ordID=handler.generate_client_order_id()
)
```

Keep in mind, that volume asset is defined by an exchange you are using.

To create multiple orders in one request use:

```python
data = handler.create_orders(
    symbol="BTCUSDT",
    data=[
        ("BUY", 10000, 0.001),
        ("SELL", 1000, 0.001),
        ("BUY", 200, 0.1, handler.generate_client_order_id())
    ]
)
```


## Sockets