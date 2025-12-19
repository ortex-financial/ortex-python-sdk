"""ORTEX Python SDK - Official Python SDK for ORTEX Financial Data API.

Access comprehensive financial data including short interest, stock prices,
options, fundamentals, and more.

Quick Start:
    >>> import ortex
    >>> ortex.set_api_key("your-api-key")
    >>> response = ortex.get_short_interest("NYSE", "AMC")
    >>> df = response.df  # Get data as DataFrame
    >>> print(f"Credits used: {response.credits_used}")

Get your API key at: https://app.ortex.com/apis
Full documentation: https://docs.ortex.com
"""

from __future__ import annotations

__version__ = "1.0.4"
__author__ = "ORTEX Technologies LTD"

from .api import (
    get_balance_sheet,
    get_cash_flow,
    get_client,
    get_close_price,
    get_cost_to_borrow,
    get_days_to_cover,
    get_earnings,
    get_eu_short_positions,
    get_eu_short_positions_history,
    get_eu_short_total,
    get_exchanges,
    get_financial_ratios,
    get_free_float,
    get_fundamentals_summary,
    get_income_statement,
    get_index_cost_to_borrow,
    get_index_days_to_cover,
    get_index_short_availability,
    get_index_short_interest,
    get_macro_events,
    get_price,
    get_shares_outstanding,
    get_short_availability,
    get_short_interest,
    get_valuation,
    set_api_key,
)
from .client import OrtexClient
from .exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    OrtexError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .response import OrtexResponse
from .throttler import RequestThrottler

__all__ = [
    # Version
    "__version__",
    # Core
    "OrtexClient",
    "OrtexResponse",
    "RequestThrottler",
    # Configuration
    "set_api_key",
    "get_client",
    # Short Interest
    "get_short_interest",
    "get_index_short_interest",
    "get_short_availability",
    "get_index_short_availability",
    "get_cost_to_borrow",
    "get_index_cost_to_borrow",
    "get_days_to_cover",
    "get_index_days_to_cover",
    # Prices
    "get_price",
    "get_close_price",
    # Stock Data
    "get_free_float",
    "get_shares_outstanding",
    # Fundamentals
    "get_income_statement",
    "get_balance_sheet",
    "get_cash_flow",
    "get_financial_ratios",
    "get_fundamentals_summary",
    "get_valuation",
    # EU Short Interest
    "get_eu_short_positions",
    "get_eu_short_positions_history",
    "get_eu_short_total",
    # Market Data
    "get_earnings",
    "get_exchanges",
    "get_macro_events",
    # Exceptions
    "APIError",
    "OrtexError",  # Backwards compatibility alias for APIError
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "NetworkError",
    "TimeoutError",
]
