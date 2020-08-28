# CryptoFuturesPy
 The Python library for different implementations of a exchange interface for cryptocurrency futures trading

[![GitHub issues](https://img.shields.io/github/issues-raw/LeaveMyYard/CryptoFuturesPy?style=flat-square)](https://github.com/LeaveMyYard/CryptoFuturesPy/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/LeaveMyYard/CryptoFuturesPy?style=flat-square)](https://github.com/LeaveMyYard/CryptoFuturesPy/pulls)
[![License](https://img.shields.io/github/license/day8/re-frame.svg?style=flat-square)](LICENSE.txt)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

## Overview

One day, I was tried to be messing with different interfaces of Binance, Bitmex and etc so I desided to create an interface for them and to make some implementations.

So, there exists a Bitmex and a Binance Futures implementation now, but more are coming soon.

All code is written on Python 3.7 with typing specifications. 

## Installation

You can easily install it using 

`pip install crypto-futures-py`

and then access it in your Python code like that:

```python
from crypto_futures_py import BitmexExchangeHandler
```

<!-- ## Documentation 

The documentation is [available here](http://day8.github.io/re-frame/). -->

## Usage

Create an object of your wanted exchange and provide your keys for this exchange there.

```python
from crypto_futures_py import BitmexExchangeHandler

handler = BitmexExchangeHandler("publickey", "privatekey")
```

After that you can call it's methods to load data or to place orders:

```python
handler.start_kline_socket(lambda x: print(x), candle_type="1m", pair_name="XBTUSD")
```

All the methods are described in AbstractExchangeHandler and later would be in a separate documentation.

## TODO

- [x] Add Binance implementation
- [ ] Add a documentation
- [ ] Make websocket threads stoppable


## Licence

CryptoFuturesPy is [MIT licenced](LICENSE.txt)
