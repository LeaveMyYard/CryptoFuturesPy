from . import AbstractExchangeHandler

import typing
import pandas as pd


class BinanceFuturesExchangeHandler(AbstractExchangeHandler):
    @staticmethod
    def get_pairs_list() -> typing.List[str]:
        """get_pairs_list Returns all available pairs on exchange

        Returns:
            typing.List[str]: The list of symbol strings
        """

        ...  # TODO

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

        ...  # TODO

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

        ...  # TODO

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

        ...  # TODO

    async def cancel_orders(self, orders: typing.List[str]) -> None:
        """cancel_orders Cancels a lot of orders in one requets

        If the exchange does not support it, should create a parallel http requests, but it should be warned in docstring.

        Args:
            orders (typing.List[str]): The list of server's order_ids.
        """

        ...  # TODO

