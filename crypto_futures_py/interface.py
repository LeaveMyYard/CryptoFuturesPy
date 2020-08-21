"""
    This module contains an abstract class (interface) for standartising
    the work with the cryptocurrency exchange (AbstractExchangeHandler)
"""

from __future__ import annotations

import abc
import base64
import hashlib
import random
import threading
import pandas as pd
import typing
from dataclasses import dataclass
from datetime import datetime


class AbstractExchangeHandler(metaclass=abc.ABCMeta):
    def __init__(self, public_key: str, private_key: str):
        self._public_key = public_key
        self._private_key = private_key

    @staticmethod
    @abc.abstractmethod
    def get_pairs_list() -> typing.List[str]:
        ...

    @dataclass
    class KlineCallback:
        time: datetime
        open: float
        high: float
        low: float
        close: float
        volume: float
        message: typing.Any

    @abc.abstractmethod
    def start_kline_socket(
        self,
        on_update: typing.Callable[[AbstractExchangeHandler.KlineCallback], None],
        candle_type: str,
        pair_name: str,
    ) -> None:
        ...

    @dataclass
    class PriceCallback:
        price: float

    @abc.abstractmethod
    def start_price_socket(
        self,
        on_update: typing.Callable[[AbstractExchangeHandler.PriceCallback], None],
        pair_name: str,
    ) -> None:
        ...

    @dataclass
    class OrderUpdate:
        orderID: str
        client_orderID: str
        status: str
        price: float
        average_price: float
        fee: float
        fee_asset: str
        volume: float
        volume_realized: float
        time: datetime
        message: typing.Any

    @dataclass
    class PositionUpdate:
        symbol: str
        size: float
        value: float
        entry_price: float
        liquidation_price: float

    @dataclass
    class BalanceUpdate:
        balance: float

    UserUpdate = typing.Union[OrderUpdate, PositionUpdate, BalanceUpdate]

    @abc.abstractmethod
    def start_user_update_socket(
        self, on_update: typing.Callable[[AbstractExchangeHandler.UserUpdate], None]
    ) -> None:
        ...

    def start_kline_socket_threaded(
        self,
        on_update: typing.Callable[[AbstractExchangeHandler.KlineCallback], None],
        candle_type: str,
        pair_name: str,
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self.start_kline_socket, args=[on_update, candle_type, pair_name]
        )
        thread.setDaemon(True)
        thread.start()
        return thread

    def start_price_socket_threaded(
        self,
        on_update: typing.Callable[[AbstractExchangeHandler.PriceCallback], None],
        pair_name: str,
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self.start_price_socket, args=[on_update, pair_name]
        )
        thread.setDaemon(True)
        thread.start()
        return thread

    def start_user_update_socket_threaded(
        self,
        on_update: typing.Callable[
            [typing.Union[AbstractExchangeHandler.OrderUpdate]], None
        ],
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self.start_user_update_socket, args=[on_update]
        )
        thread.setDaemon(True)
        thread.start()
        return thread

    @abc.abstractmethod
    async def load_historical_data(
        self, symbol: str, candle_type: str, amount: int
    ) -> pd.DataFrame:
        ...

    @dataclass
    class NewOrderData:
        orderID: str
        client_orderID: str

    @abc.abstractmethod
    async def create_order(
        self,
        symbol: str,
        side: str,
        price: typing.Optional[float],
        volume: float,
        client_ordID: typing.Optional[str] = None,
    ) -> AbstractExchangeHandler.NewOrderData:
        ...

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        client_ordID: typing.Optional[str] = None,
    ) -> AbstractExchangeHandler.NewOrderData:
        return await self.create_order(
            symbol=symbol,
            side=side,
            price=None,
            volume=volume,
            client_ordID=client_ordID,
        )

    @abc.abstractmethod
    async def create_orders(
        self,
        symbol: str,
        data: typing.List[typing.Tuple[str, float, float, typing.Optional[str]]],
    ) -> typing.List[AbstractExchangeHandler.NewOrderData]:
        ...

    @abc.abstractmethod
    async def cancel_order(
        self,
        order_id: typing.Optional[str] = None,
        client_orderID: typing.Optional[str] = None,
    ) -> None:
        ...

    @abc.abstractmethod
    async def cancel_orders(self, orders: typing.List[int]) -> None:
        ...

    @staticmethod
    def generate_client_order_id() -> str:
        return base64.b32encode(
            hashlib.sha1(
                bytes(str(datetime.now()) + str(random.randint(0, 1000)), "utf-8")
            ).digest()
        ).decode("ascii")
