"""
    This module contains an implementation for Binance Futures (BinanceFuturesExchangeHandler)
"""


import pandas as pd
import typing
import logging

import futurespy as fp

from . import AbstractExchangeHandler


class BinanceFuturesExchangeHandler(AbstractExchangeHandler):
    
    
    def __init__(self, public_key, private_key):
        super().__init__(public_key, private_key)
        self._client = fp.Client(
            test=False, api_key=self._public_key, api_secret=self._private_key
        )
        
        self._orderId_dict = {}
        self._clOrderId_dict = {}
        
        self.logger = logging.Logger(__name__)
        self._order_table: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        
        
    def _round_price(
        self, symbol: str, price: typing.Optional[float]
    ) -> typing.Optional[float]:
        if price is None:
            return None

        # TODO
        return int(price * 2) / 2
    
    def _user_update_pending(
        self,
        client_orderID: str,
        price: typing.Optional[float],
        volume: float,
        symbol: str,
        side: str,
    ) -> None:
        ... # TODO
        
    def _user_update_pending_cancel(
        self,
        order_id: typing.Optional[str] = None,
        client_orderID: typing.Optional[str] = None,
    ) -> None:
        ... # TODO
    
    @staticmethod
    def get_pairs_list() -> typing.List[str]:
        """get_pairs_list Returns all available pairs on exchange

        Returns:
            typing.List[str]: The list of symbol strings
        """
        
        return [pair['symbol'] for pair in fp.MarketData().exchange_info()['symbols']]

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
            symbol = symbol,
            interval = candle_type,
            testnet = False
        )
        data = marketDataLoader.load_historical_candles(count = amount).iloc[:-1]
        data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

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
                    side=side,
                    orderType="Limit",
                    quantity=volume,
                    price=self._round_price(symbol, price),
                    # timeInForce='GTX' # POST ONLY
                ).result()[0]
            else:
                result = self._client.new_order(
                    symbol=symbol, side=side, quantity=volume, orderType="Market",
                ).result()[0]
        else:
            self._user_update_pending(
                client_ordID, self._round_price(symbol, price), volume, symbol, side
            )
            if price is not None:
                result = self._client.new_order(
                    clOrdID=client_ordID,
                    symbol=symbol,
                    side=side,
                    orderType="Limit",
                    quantity=volume,
                    price=self._round_price(symbol, price),
                    # timeInForce='GTX' # POST ONLY
                ).result()[0]
            else:
                result = self._client.new_order(
                    clOrdID=client_ordID,
                    symbol=symbol,
                    quantity=volume,
                    side=side,
                    orderType="Market",
                ).result()[0]

        return AbstractExchangeHandler.NewOrderData(
            orderID=result["orderID"], client_orderID=result["clOrdID"]
        )

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
        
        
        ...  # TODO

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
        
        if order_id is not None and order_id in self._orderId_dict.keys():
            self._client.cancel_order(symbol=self._orderId_dict[order_id], orderId=order_id)
        elif client_orderID is not None and client_orderID in self._clOrderId_dict.keys():
            self._client.cancel_order(symbol=self._clOrderId_dict[client_orderID], clientID=client_orderID)
        else:
            raise ValueError(
                "Either order_id of client_orderID should be sent, but both are None"
            )

    @staticmethod
    def _split_list(orders, size):
        return [orders[i : i + size] for i in range(0, len(orders), size)]

    async def cancel_orders(self, orders: typing.List[str]) -> None:
        """cancel_orders Cancels a lot of orders in one requets

        If the exchange does not support it, should create a parallel http requests, but it should be warned in docstring.

        Args:
            orders (typing.List[str]): The list of server's order_ids.
        """
        
        for order_id in orders:
            self._user_update_pending_cancel(order_id=order_id)
        
        # TODO
        
        tmp_list = self._split_list(orders=orders, size=10)
        for id_list in tmp_list:
            self._client.cancel_multiple_orders(id_list)

