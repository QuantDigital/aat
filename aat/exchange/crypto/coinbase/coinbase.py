import os
from collections import deque
from typing import List, Mapping

from aat.core import ExchangeType, Order, Event, Instrument
from aat.config import TradingType, InstrumentType, EventType
from aat.exchange import Exchange

from .client import CoinbaseExchangeClient


class CoinbaseProExchange(Exchange):
    '''Coinbase Pro Exchange'''

    def __init__(self,
                 trading_type,
                 verbose,
                 api_key='',
                 api_secret='',
                 api_passphrase='',
                 **kwargs):
        self._trading_type = trading_type
        self._verbose = verbose

        # coinbase keys
        self._api_key = api_key or os.environ.get('API_KEY', '')
        self._api_secret = api_key or os.environ.get('API_SECRET', '')
        self._api_passphrase = api_key or os.environ.get('API_PASSPHRASE', '')

        # enforce authentication, otherwise we don't get enough
        # data to be interesting
        if not (self._api_key and self._api_secret and self._api_passphrase):
            raise Exception('No coinbase auth!')

        # don't implement backtest for now
        if trading_type == TradingType.BACKTEST:
            raise NotImplementedError()

        if self._trading_type == TradingType.SANDBOX:
            # Coinbase sandbox
            super().__init__(ExchangeType('coinbaseprosandbox'))
        else:
            # Coinbase Live trading
            print('*' * 100)
            print('*' * 100)
            print('WARNING: LIVE TRADING')
            print('*' * 100)
            print('*' * 100)
            super().__init__(ExchangeType('coinbasepro'))

        # Create an exchange client based on the coinbase docs
        # Note: cbpro doesnt seem to work as well as I remember,
        # and ccxt has moved to a "freemium" model where coinbase
        # pro now costs money for full access, so here i will just
        # implement the api myself.
        self._client = CoinbaseExchangeClient(self._trading_type, self.exchange(), self._api_key, self._api_secret, self._api_passphrase)

        # store client order events in a deque
        self._order_events = deque()

        # list of market data subscriptions
        self._subscriptions: List[Instrument] = []

    # *************** #
    # General methods #
    # *************** #
    async def connect(self):
        '''connect to exchange. should be asynchronous.'''
        # instantiate instruments
        self._client.instruments()

    async def lookup(self, instrument):
        '''lookup an instrument on the exchange'''
        # TODO
        raise NotImplementedError()

    # ******************* #
    # Market Data Methods #
    # ******************* #
    async def tick(self):
        '''return data from exchange'''

        # First, roll through order book snapshot
        for item in self._client.orderBook(self._subscriptions):
            yield item

        # then stream in live updates
        async for tick in self._client.websocket(self._subscriptions):
            yield tick

            # drain order events ASAP
            while len(self._order_events) > 0:
                _ = self._order_events.popleft()
                yield _

    async def subscribe(self, instrument):
        # can only subscribe to pair data
        if instrument.type == InstrumentType.PAIR:
            self._subscriptions.append(instrument)

    # ******************* #
    # Order Entry Methods #
    # ******************* #
    async def accounts(self):
        '''get accounts from source'''
        return self._client.accounts()

    async def newOrder(self, order):
        '''submit a new order to the exchange. should set the given order's `id` field to exchange-assigned id'''
        ret = self._client.newOrder(order)
        if ret:
            # order succesful
            self._order_events.append(Event(type=EventType.RECEIVED, target=order))
        else:
            # order failure
            self._order_events.append(Event(type=EventType.REJECTED, target=order))

    async def cancelOrder(self, order: Order):
        '''cancel a previously submitted order to the exchange.'''
        ret = self._client.cancelOrder(order)
        if ret:
            # cancel succesful
            self._order_events.append(Event(type=EventType.CANCELED, target=order))
        else:
            # cancel rejected
            self._order_events.append(Event(type=EventType.REJECTED, target=order))


Exchange.registerExchange('coinbase', CoinbaseProExchange)
