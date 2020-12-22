import logging
from collections import deque
from datetime import datetime
from typing import Any, Optional, List, TYPE_CHECKING

from aat.common import _in_cpp
from ..exchange import ExchangeType
from ..instrument import Instrument
from aat.config import OrderType, OrderFlag, EventType, Side


if TYPE_CHECKING:
    from .order import Order


try:
    from aat.binding import DataCpp, EventCpp, OrderCpp, TradeCpp  # type: ignore

    _CPP = _in_cpp()

except ImportError:
    logging.critical("Could not load C++ extension")
    _CPP = False


def _make_cpp_data(
    id: str,
    timestamp: datetime,
    instrument: Instrument,
    exchange: ExchangeType,
    data: Any,
) -> DataCpp:
    """helper method to ensure all arguments are setup"""
    return DataCpp(id, timestamp, instrument, exchange, data)


def _make_cpp_event(type: EventType, target: Any) -> EventCpp:
    """helper method to ensure all arguments are setup"""
    return EventCpp(type, target)


def _make_cpp_order(
    volume: float,
    price: float,
    side: Side,
    instrument: Instrument,
    exchange: ExchangeType = ExchangeType(""),
    notional: float = 0.0,
    order_type: OrderType = OrderType.MARKET,
    flag: OrderFlag = OrderFlag.NONE,
    stop_target: Optional["Order"] = None,
    id: str = None,
    timestamp: datetime = None,
) -> OrderCpp:
    """helper method to ensure all arguments are setup"""
    return OrderCpp(
        id or "0",
        timestamp or datetime.now(),
        volume,
        price,
        side,
        instrument,
        exchange,
        notional,
        order_type,
        flag,
        stop_target,
    )


def _make_cpp_trade(
    id: str,
    timestamp: datetime,
    maker_orders: List["Order"] = None,
    taker_order: Optional["Order"] = None,
) -> TradeCpp:
    """helper method to ensure all arguments are setup"""
    return TradeCpp(id, timestamp, maker_orders or deque(), taker_order)
