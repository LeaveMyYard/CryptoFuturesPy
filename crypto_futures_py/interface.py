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

        self._user_update_callbacks: typing.List[
            typing.Callable[[AbstractExchangeHandler.UserUpdate], None]
        ] = []

        self._order_table_id: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        self._order_table_clid: typing.Dict[str, typing.Dict[str, typing.Any]] = {}

    @staticmethod
    @abc.abstractmethod
    def get_pairs_list() -> typing.List[str]:
        """get_pairs_list Returns all available pairs on exchange

        Returns:
            typing.List[str]: The list of symbol strings
        """
        ...

    @dataclass
    class KlineCallback:
        time: datetime
        open: float
        high: float
        low: float
        close: float
        volume: float
        final: bool
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
        symbol: str
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
        symbol: str

    UserUpdate = typing.Union[OrderUpdate, PositionUpdate, BalanceUpdate]

    @abc.abstractmethod
    def start_user_update_socket(
        self, on_update: typing.Callable[[AbstractExchangeHandler.UserUpdate], None]
    ) -> None:
        self._user_update_callbacks.append(on_update)

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
        """load_historical_data Loads historical klines from exchange

        Args:
            symbol (str): Pair name
            candle_type (str): Exchange specific type of candles ("1m" for example)
            amount (int): Number of klines to load

        Returns:
            pd.DataFrame: Dataframe with columns: Date, Open, High, Low, Close, Volume
        """
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
        """create_order Place one limit or market order

        Args:
            symbol (str): Pair name, for which to place an order
            side (str): "Buy" or "Sell"
            price (typing.Optional[float]): If the price is set, the price for limit order. Else - market order.
            volume (float): The volume of the order
            client_ordID (typing.Optional[str], optional): Client order_id. 
                Could be generated using generate_client_order_id(). Defaults to None.

        Returns:
            AbstractExchangeHandler.NewOrderData: Data of the resulting order.
        """
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
        """create_orders Create a lot of orders from one request (if the exchange supports it)

        If the exchange does not support it, should create a parallel http requests, but it should be warned in docstring.

        Args:
            symbol (str): Pair name, for which to place orders
            data (typing.List[typing.Tuple[str, float, float, typing.Optional[str]]]): The list of tuple params like in
                create_order() - (side, price, volume, client_ordID), except price should not be None.

        Returns:
            typing.List[AbstractExchangeHandler.NewOrderData]: List of results
        """
        ...

    @abc.abstractmethod
    async def cancel_order(
        self,
        order_id: typing.Optional[str] = None,
        client_orderID: typing.Optional[str] = None,
    ) -> None:
        """cancel_order Cancel one order via order_id or client_orderID

        Either order_id or client_orderID should be sent.
        If both are sent, will use order_id.

        Args:
            order_id (typing.Optional[str], optional): Server's order id. Defaults to None.
            client_orderID (typing.Optional[str], optional): Client's order id. Defaults to None.
        """
        ...

    @abc.abstractmethod
    async def cancel_orders(self, orders: typing.List[str]) -> None:
        """cancel_orders Cancels a lot of orders in one requets

        If the exchange does not support it, should create a parallel http requests, but it should be warned in docstring.

        Args:
            orders (typing.List[str]): The list of server's order_ids.
        """
        ...

    @staticmethod
    def generate_client_order_id() -> str:
        return base64.b32encode(
            hashlib.sha1(
                bytes(str(datetime.now()) + str(random.randint(0, 1000)), "utf-8")
            ).digest()
        ).decode("ascii")

    def _register_order_data(self, order_data: typing.Dict[str, typing.Any],) -> None:
        self._order_table_id[order_data["orderID"]] = order_data
        self._order_table_clid[order_data["client_orderID"]] = order_data

    def _user_update_pending(
        self,
        client_orderID: str,
        price: typing.Optional[float],
        volume: float,
        symbol: str,
        side: str,
    ) -> None:
        volume_side = 1 if side.lower() == "buy" else -1
        event = self.OrderUpdate(
            orderID="",
            client_orderID=client_orderID,
            status="PENDING",
            symbol=symbol,
            price=price if price is not None else float("nan"),
            average_price=float("nan"),
            fee=0,
            fee_asset="XBT",
            volume=volume * volume_side,
            volume_realized=0,
            time=datetime.now(),
            message={},
        )
        for callback in self._user_update_callbacks:
            callback(event)

    def _user_update_pending_cancel(
        self,
        order_id: typing.Optional[str] = None,
        client_orderID: typing.Optional[str] = None,
    ) -> None:
        if order_id is not None:
            order_data = self._order_table_id[order_id].copy()
        elif client_orderID is not None:
            order_data = self._order_table_clid[client_orderID].copy()
        else:
            raise ValueError(
                "Either order_id of client_orderID should be sent, but both are None"
            )

        order_data["status"] = "PENDING_CANCEL"
        order_data["time"] = datetime.now()

        for callback in self._user_update_callbacks:
            callback(self.OrderUpdate(**order_data))
