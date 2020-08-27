"""
    This module contains an implementation for Binance Futures (BinanceFuturesExchangeHandler)
"""


import pandas as pd
import typing
import json
import logging
import pandas as pd

from datetime import datetime

from . import futurespy as fp
from . import AbstractExchangeHandler


class BinanceFuturesExchangeHandler(AbstractExchangeHandler):
    exchange_information = fp.MarketData().exchange_info()

    def __init__(self, public_key, private_key):
        super().__init__(public_key, private_key)
        self._client = fp.Client(
            testnet=False, api_key=self._public_key, sec_key=self._private_key
        )

        self._orderId_dict = {}
        self._clOrderId_dict = {}

        self.logger = logging.Logger(__name__)

    def start_kline_socket(
        self,
        on_update: typing.Callable[[AbstractExchangeHandler.KlineCallback], None],
        candle_type: str,
        pair_name: str,
    ) -> None:
        def _on_update(message):
            candle = message["k"]
            on_update(
                self.KlineCallback(
                    time=pd.to_datetime(candle["t"], unit="ms"),
                    open=float(candle["o"]),
                    high=float(candle["h"]),
                    low=float(candle["l"]),
                    close=float(candle["c"]),
                    volume=float(candle["v"]),
                    final=candle["x"],
                    message=message,
                )
            )

        ws = fp.WebsocketMarket(
            symbol=pair_name,
            on_message=lambda _, message: _on_update(message),
            interval=candle_type,
        )
        ws.candle_socket()

    def start_price_socket(
        self,
        on_update: typing.Callable[[AbstractExchangeHandler.PriceCallback], None],
        pair_name: str,
    ) -> None:
        def _on_update(message):
            on_update(self.PriceCallback(float(message["p"])))

        ws = fp.WebsocketMarket(
            symbol=pair_name, on_message=lambda _, message: _on_update(message),
        )
        ws.mark_price_socket()

    def start_user_update_socket(
        self, on_update: typing.Callable[[AbstractExchangeHandler.UserUpdate], None]
    ) -> None:
        super().start_user_update_socket(on_update)

        def _on_update_recieved(message: typing.Dict[str, typing.Any]) -> None:
            if message["e"] == "ACCOUNT_UPDATE":
                for balance in message["a"]["B"]:
                    on_update(
                        self.BalanceUpdate(balance=balance["wb"], symbol=balance["a"])
                    )
                for position in message["a"]["P"]:
                    on_update(
                        self.PositionUpdate(
                            symbol=position["s"],
                            size=position["pa"],
                            value=position["pa"] * position["ep"],
                            entry_price=position["ep"],
                            liquidation_price=float("nan"),  # TODO
                        )
                    )

            elif message["e"] == "ORDER_TRADE_UPDATE":
                event = message["o"]
                order_data = dict(
                    orderID=str(event["i"]),
                    client_orderID=str(event["c"]),
                    status=event["X"],
                    symbol=event["s"],
                    price=float(event["p"]),
                    average_price=float(event["ap"]),
                    fee=float(event["n"]) if "n" in event else 0,
                    fee_asset=event["N"] if "N" in event else "",
                    volume=float(event["q"]),
                    volume_realized=float(event["z"]),
                    time=pd.to_datetime(event["T"], unit="ms"),
                    message=message,
                )

                self._register_order_data(order_data)
                on_update(self.OrderUpdate(**order_data))

        self._client.user_update_socket(
            on_message=lambda ws, message: _on_update_recieved(json.loads(message)),
            on_close=lambda x: self.start_user_update_socket(on_update),
        )

    def _round_price(
        self, symbol: str, price: typing.Optional[float]
    ) -> typing.Optional[float]:
        for d in self.exchange_information["symbols"]:
            if d["symbol"] == symbol:
                price_precision = d["pricePrecision"]
                break
        else:
            raise ValueError(f"{symbol} is not in exchange info")

        return None if price is None else round(price, price_precision)

    _T = typing.TypeVar("_T", float, None)

    def _round_volume(self, symbol: str, volume: _T) -> _T:
        for d in self.exchange_information["symbols"]:
            if d["symbol"] == symbol:
                quantity_precision = d["quantityPrecision"]
                break
        else:
            raise ValueError(f"{symbol} is not in exchange info")

        if (
            not isinstance(volume, float)
            and not isinstance(volume, int)
            and volume is not None
        ):
            raise ValueError

        return (
            None
            if volume is None
            else round(typing.cast(float, volume), quantity_precision)
        )

    @staticmethod
    def get_pairs_list() -> typing.List[str]:
        """get_pairs_list Returns all available pairs on exchange

        Returns:
            typing.List[str]: The list of symbol strings
        """

        return [
            pair["symbol"]
            for pair in BinanceFuturesExchangeHandler.exchange_information["symbols"]
        ]

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
        marketDataLoader = fp.MarketData(
            symbol=symbol, interval=candle_type, testnet=False
        )
        data = marketDataLoader.load_historical_candles(count=amount).iloc[:-1]
        data = data[["Date", "Open", "High", "Low", "Close", "Volume"]]

        return data

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

        if client_ordID is None:
            if price is not None:
                result = self._client.new_order(
                    symbol=symbol,
                    side=side.upper(),
                    orderType="LIMIT",
                    quantity=self._round_volume(symbol, volume),
                    price=self._round_price(symbol, price),
                    timeInForce="GTX",  # POST ONLY
                )
            else:
                result = self._client.new_order(
                    symbol=symbol,
                    side=side.upper(),
                    quantity=self._round_volume(symbol, volume),
                    orderType="MARKET",
                )
        else:
            self._user_update_pending(
                client_ordID,
                self._round_price(symbol, price),
                self._round_volume(symbol, volume),
                symbol,
                side.upper(),
            )
            if price is not None:
                result = self._client.new_order(
                    newClientOrderId=client_ordID,
                    symbol=symbol,
                    side=side.upper(),
                    orderType="LIMIT",
                    quantity=self._round_volume(symbol, volume),
                    price=self._round_price(symbol, price),
                    timeInForce="GTX",  # POST ONLY
                )
            else:
                result = self._client.new_order(
                    newClientOrderId=client_ordID,
                    symbol=symbol,
                    quantity=self._round_volume(symbol, volume),
                    side=side.upper(),
                    orderType="MARKET",
                )

        try:
            return AbstractExchangeHandler.NewOrderData(
                orderID=result["orderId"], client_orderID=result["clientOrderId"]
            )
        except:
            if client_ordID is not None:
                self._user_update_failed(client_ordID)
                return AbstractExchangeHandler.NewOrderData(
                    orderID="", client_orderID=client_ordID
                )
            else:
                raise

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
        orders: typing.List[typing.Dict[str, typing.Union[str, float]]] = [
            {
                "symbol": symbol,
                "side": order_data[0].upper(),
                "type": "LIMIT",
                "quantity": self._round_volume(symbol, order_data[2]),
                "price": typing.cast(float, self._round_price(symbol, order_data[1])),
                # "timeInForce" : "GTX" # POST ONLY
            }
            if len(order_data) == 3 or order_data[3] is None
            else {
                "clOrdID": order_data[3],
                "symbol": symbol,
                "side": order_data[0].upper(),
                "type": "LIMIT",
                "quantity": self._round_volume(symbol, order_data[2]),
                "price": typing.cast(float, self._round_price(symbol, order_data[1])),
                # "timeInForce" : "GTX" # POST ONLY
            }
            for order_data in data
        ]
        for order in orders:
            self._user_update_pending(
                client_orderID=str(order["clOrdID"]),
                price=float(order["price"]),
                volume=float(order["quantity"]),
                symbol=str(order["symbol"]),
                side=str(order["side"]),
            )

        results = []
        orders_list = self._split_list(lst=orders, size=5)
        for tmp_orders_list in orders_list:
            results.append(self._client.place_multiple_orders(tmp_orders_list))

        return [
            AbstractExchangeHandler.NewOrderData(
                orderID=result["orderID"], client_orderID=result["clOrdID"]
            )
            for result in results
        ]

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

        self._user_update_pending_cancel(
            order_id=order_id, client_orderID=client_orderID
        )

        if order_id is not None and order_id in self._order_table_id:
            self._client.cancel_order(
                symbol=self._order_table_id[order_id]["symbol"], orderId=order_id
            )
        elif client_orderID is not None and client_orderID in self._order_table_clid:
            self._client.cancel_order(
                symbol=self._order_table_clid[client_orderID]["symbol"],
                orderId=client_orderID,
                clientID=True,
            )
        else:
            raise ValueError(
                "Either order_id of client_orderID should be sent, but both are None"
            )

    @staticmethod
    def _split_list(lst, size):
        return [lst[i : i + size] for i in range(0, len(lst), size)]

    async def cancel_orders(self, orders: typing.List[str]) -> None:
        """cancel_orders Cancels a lot of orders in one requets

        If the exchange does not support it, should create a parallel http requests, but it should be warned in docstring.

        Args:
            orders (typing.List[str]): The list of server's order_ids.
        """

        for order_id in orders:
            self._user_update_pending_cancel(order_id=order_id)

        to_cancel_dict: typing.Dict[str, typing.List[str]] = {}

        for order in orders:
            order_symbol: str = self._order_table_id[order]["symbol"]
            if order_symbol not in to_cancel_dict:
                to_cancel_dict[order_symbol] = []
            to_cancel_dict[order_symbol].append(order)

        results = []
        for symbol in to_cancel_dict.keys():
            tmp_list = self._split_list(to_cancel_dict[symbol], 10)
            for lst in tmp_list:
                result = self._client.cancel_multiple_orders(
                    symbol=symbol, orderIdList=lst
                )
                results.append(result)
