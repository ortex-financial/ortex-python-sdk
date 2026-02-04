"""ORTEX API functions for retrieving financial data.

This module provides high-level functions for accessing all ORTEX API endpoints.
All functions return OrtexResponse objects that provide:
- Data as pandas DataFrames via .df property
- Pagination support via iter_all_pages() and next_page()
- Credit usage info via credits_used and credits_left properties
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

from .client import (
    OrtexClient,
    normalize_date,
    normalize_exchange,
    normalize_ticker,
)
from .exceptions import AuthenticationError
from .response import OrtexResponse

# Global client instance for convenience
_client: OrtexClient | None = None


def set_api_key(api_key: str) -> None:
    """Set the global API key for all ORTEX functions.

    This function sets the API key that will be used by all module-level
    functions. Alternatively, you can set the ORTEX_API_KEY environment
    variable or pass an api_key to each function.

    Args:
        api_key: Your ORTEX API key from https://app.ortex.com/apis

    Example:
        >>> import ortex
        >>> ortex.set_api_key("your-api-key")
        >>> response = ortex.get_short_interest("NYSE", "AMC")
        >>> df = response.df
    """
    global _client
    _client = OrtexClient(api_key=api_key)


def get_client(api_key: str | None = None) -> OrtexClient:
    """Get or create an ORTEX client instance.

    Args:
        api_key: Optional API key. If not provided, uses global client
            or ORTEX_API_KEY environment variable.

    Returns:
        OrtexClient instance.

    Raises:
        AuthenticationError: If no API key is available.
    """
    global _client

    if api_key:
        return OrtexClient(api_key=api_key)

    if _client is not None:
        return _client

    # Try environment variable
    env_key = os.environ.get("ORTEX_API_KEY")
    if env_key:
        _client = OrtexClient(api_key=env_key)
        return _client

    raise AuthenticationError(
        "No API key configured. Use ortex.set_api_key('your-key'), "
        "pass api_key parameter, or set ORTEX_API_KEY environment variable. "
        "Get your API key at https://app.ortex.com/apis"
    )


# =============================================================================
# Short Interest Functions
# =============================================================================


def get_short_interest(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get short interest data for a stock.

    Retrieves short interest metrics including shares on loan, utilization,
    and short interest percentage of free float.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol (e.g., "AMC", "AAPL").
        from_date: Start date for historical data.
        to_date: End date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with short interest data.
        Access data via .df property, iterate pages via .iter_all_pages().

    Example:
        >>> response = ortex.get_short_interest("NYSE", "AMC")
        >>> print(f"Credits used: {response.credits_used}")
        >>> df = response.df
        >>> # Get all pages
        >>> for page in response.iter_all_pages():
        ...     process(page.df)
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"{exchange}/{ticker}/short_interest"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_index_short_interest(
    index: str = "US-S 500",
    date_val: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get short interest data for an index.

    Retrieves short interest metrics for multiple stocks in an index.

    Args:
        index: Index name - "US-S 500", "US-N 100", "UK Top 100", "Europe Top 600".
        date_val: Date for the data. If None, returns latest.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with index short interest data.

    Example:
        >>> response = ortex.get_index_short_interest("US-S 500")
        >>> df = response.df
    """
    client = get_client(api_key)

    endpoint = "index/short_interest"
    params: dict[str, Any] = {"index": index}
    if date_val:
        params["date"] = normalize_date(date_val)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


def get_short_availability(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get share availability for shorting.

    Retrieves the number of shares available to borrow for short selling.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date for historical data.
        to_date: End date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with availability data.

    Example:
        >>> response = ortex.get_short_availability("NYSE", "AMC")
        >>> df = response.df
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/availability"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_cost_to_borrow(
    exchange: str,
    ticker: str,
    loan_type: str = "all",
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get cost to borrow data for short selling.

    Retrieves the annualized cost to borrow shares for short selling.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        loan_type: Type of loans - "all" for all loans, "new" for new loans only.
        from_date: Start date for historical data.
        to_date: End date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with cost to borrow data.

    Example:
        >>> response = ortex.get_cost_to_borrow("NYSE", "AMC")
        >>> response = ortex.get_cost_to_borrow("NYSE", "AMC", loan_type="new")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    loan_type = loan_type.lower()
    if loan_type not in ("all", "new"):
        loan_type = "all"

    endpoint = f"stock/{exchange}/{ticker}/ctb/{loan_type}"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_days_to_cover(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    period: str = "1m",
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get days to cover data.

    Days to cover represents the number of days it would take to cover
    all short positions based on average daily trading volume.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date for historical data.
        to_date: End date for historical data.
        period: Volume averaging period - "1w", "2w", "1m", "3m".
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with days to cover data.

    Example:
        >>> response = ortex.get_days_to_cover("NYSE", "AMC")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/dtc"
    params: dict[str, Any] = {"period": period}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


# =============================================================================
# Price Functions
# =============================================================================


def get_price(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    volume_from_all_exchanges: bool = False,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get OHLCV price data for a stock.

    Retrieves open, high, low, close prices and volume data.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date for historical data.
        to_date: End date for historical data.
        volume_from_all_exchanges: If True, include volume from all exchanges.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with OHLCV data.

    Example:
        >>> response = ortex.get_price("NASDAQ", "AAPL")
        >>> df = response.df
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/closing_prices"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if volume_from_all_exchanges:
        params["volume_from_all_exchanges"] = "true"
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_close_price(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get closing price data for a stock.

    This is an alias for get_price() - both return OHLCV data.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date for historical data.
        to_date: End date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with OHLCV data.

    Example:
        >>> response = ortex.get_close_price("NASDAQ", "AAPL")
    """
    return get_price(
        exchange, ticker, from_date, to_date, page_size=page_size, page=page, api_key=api_key
    )


# =============================================================================
# Stock Data Functions
# =============================================================================


def get_free_float(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get free float data for a stock.

    Free float represents the number of shares available for public trading.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date (required).
        to_date: End date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with free float data.

    Example:
        >>> response = ortex.get_free_float("NYSE", "F", "2024-01-01")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/free_float"
    params: dict[str, Any] = {"from_date": normalize_date(from_date)}
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


def get_shares_outstanding(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get shares outstanding data for a stock.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date (required).
        to_date: End date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with shares outstanding data.

    Example:
        >>> response = ortex.get_shares_outstanding("NYSE", "F", "2024-01-01")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/shares_outstanding"
    params: dict[str, Any] = {"from_date": normalize_date(from_date)}
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


# =============================================================================
# Fundamentals Functions
# =============================================================================


def get_income_statement(
    exchange: str,
    ticker: str,
    period: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get income statement data.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        period: Reporting period (e.g., "2024Q3" for Q3 2024, "2024" for annual).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with income statement data.

    Example:
        >>> response = ortex.get_income_statement("NYSE", "F", "2024Q3")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/fundamentals/income"
    params: dict[str, Any] = {"period": period}

    return client.fetch(endpoint, params=params)


def get_balance_sheet(
    exchange: str,
    ticker: str,
    period: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get balance sheet data.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        period: Reporting period (e.g., "2024Q3" for Q3 2024).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with balance sheet data.

    Example:
        >>> response = ortex.get_balance_sheet("NYSE", "F", "2024Q3")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/fundamentals/balance"
    params: dict[str, Any] = {"period": period}

    return client.fetch(endpoint, params=params)


def get_cash_flow(
    exchange: str,
    ticker: str,
    period: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get cash flow statement data.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        period: Reporting period (e.g., "2024Q3" for Q3 2024).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with cash flow data.

    Example:
        >>> response = ortex.get_cash_flow("NYSE", "F", "2024Q3")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/fundamentals/cash"
    params: dict[str, Any] = {"period": period}

    return client.fetch(endpoint, params=params)


def get_financial_ratios(
    exchange: str,
    ticker: str,
    period: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get financial ratios.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        period: Reporting period (e.g., "2024Q3" for Q3 2024).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with financial ratios.

    Example:
        >>> response = ortex.get_financial_ratios("NYSE", "F", "2024Q3")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/fundamentals/ratios"
    params: dict[str, Any] = {"period": period}

    return client.fetch(endpoint, params=params)


def get_fundamentals_summary(
    exchange: str,
    ticker: str,
    period: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get fundamentals summary.

    Returns a comprehensive summary of key fundamental metrics.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        period: Reporting period (e.g., "2024Q3" for Q3 2024).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with fundamentals summary.

    Example:
        >>> response = ortex.get_fundamentals_summary("NYSE", "F", "2024Q3")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/fundamentals/summary"
    params: dict[str, Any] = {"period": period}

    return client.fetch(endpoint, params=params)


def get_valuation(
    exchange: str,
    ticker: str,
    period: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get valuation metrics.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        period: Reporting period (e.g., "2024Q3" for Q3 2024).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with valuation metrics.

    Example:
        >>> response = ortex.get_valuation("NYSE", "F", "2024Q3")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/fundamentals/valuation"
    params: dict[str, Any] = {"period": period}

    return client.fetch(endpoint, params=params)


# =============================================================================
# European Short Interest Functions
# =============================================================================


def get_eu_short_positions(
    exchange: str,
    ticker: str,
    date_val: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get EU regulatory short positions.

    Returns disclosed short positions from EU regulatory filings.

    Args:
        exchange: Exchange code (e.g., "XETR" for Germany).
        ticker: Stock ticker symbol.
        date_val: Date for positions. If None, returns latest.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with EU short position data.

    Example:
        >>> response = ortex.get_eu_short_positions("XETR", "SAP")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/european_short_interest_filings/open_positions_at"
    params: dict[str, Any] = {}
    if date_val:
        params["date"] = normalize_date(date_val)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_eu_short_positions_history(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get EU regulatory short positions history.

    Returns short interest changes over a time period from EU filings.

    Args:
        exchange: Exchange code (e.g., "XETR" for Germany).
        ticker: Stock ticker symbol.
        from_date: Start date.
        to_date: End date.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with EU short position history.

    Example:
        >>> response = ortex.get_eu_short_positions_history("XETR", "SAP", "2024-01-01")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/european_short_interest_filings/positions_in_range"
    params: dict[str, Any] = {"from_date": normalize_date(from_date)}
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


def get_eu_short_total(
    exchange: str,
    ticker: str,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get total EU regulatory short interest.

    Returns the aggregate short position from EU regulatory filings.

    Args:
        exchange: Exchange code (e.g., "XETR" for Germany).
        ticker: Stock ticker symbol.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with total EU short interest.

    Example:
        >>> response = ortex.get_eu_short_total("XETR", "SAP")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/european_short_interest_filings/total_open_positions"

    return client.fetch(endpoint)


# =============================================================================
# Market Data Functions
# =============================================================================


def get_earnings(
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get earnings calendar.

    Returns upcoming or historical earnings announcements.

    Args:
        from_date: Start date.
        to_date: End date.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with earnings data.

    Example:
        >>> response = ortex.get_earnings()  # Upcoming
        >>> response = ortex.get_earnings("2024-12-01", "2024-12-31")  # Historical
    """
    client = get_client(api_key)

    endpoint = "earnings"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_exchanges(
    country: str | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get list of supported exchanges.

    Args:
        country: Optional country filter (e.g., "United States").
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with exchange information.

    Example:
        >>> response = ortex.get_exchanges()
        >>> response = ortex.get_exchanges("United States")
    """
    client = get_client(api_key)

    endpoint = "generics/exchanges"
    params: dict[str, Any] = {}
    if country:
        params["country_name"] = country
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_macro_events(
    country: str,
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get macroeconomic events calendar.

    Args:
        country: Country ISO-2 code (e.g., "US", "GB", "DE").
        from_date: Start date.
        to_date: End date.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with macro events.

    Example:
        >>> response = ortex.get_macro_events("US")
        >>> response = ortex.get_macro_events("US", "2024-12-01", "2024-12-15")
    """
    client = get_client(api_key)
    country = country.upper()

    endpoint = "macro_events"
    params: dict[str, Any] = {"country": country}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


# =============================================================================
# Index Data Functions
# =============================================================================


def get_index_short_availability(
    index: str = "US-S 500",
    date_val: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get short availability data for an index.

    Args:
        index: Index name - "US-S 500", "US-N 100", "UK Top 100", "Europe Top 600".
        date_val: Date for the data. If None, returns latest.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with index short availability data.

    Example:
        >>> response = ortex.get_index_short_availability("US-S 500")
    """
    client = get_client(api_key)

    endpoint = "index/short_availability"
    params: dict[str, Any] = {"index": index}
    if date_val:
        params["date"] = normalize_date(date_val)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


def get_index_cost_to_borrow(
    index: str = "US-S 500",
    date_val: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get cost to borrow data for an index.

    Args:
        index: Index name - "US-S 500", "US-N 100", "UK Top 100", "Europe Top 600".
        date_val: Date for the data. If None, returns latest.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with index cost to borrow data.

    Example:
        >>> response = ortex.get_index_cost_to_borrow("US-S 500")
    """
    client = get_client(api_key)

    endpoint = "index/short_ctb"
    params: dict[str, Any] = {"index": index}
    if date_val:
        params["date"] = normalize_date(date_val)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


def get_index_days_to_cover(
    index: str = "US-S 500",
    date_val: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get days to cover data for an index.

    Args:
        index: Index name - "US-S 500", "US-N 100", "UK Top 100", "Europe Top 600".
        date_val: Date for the data. If None, returns latest.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with index days to cover data.

    Example:
        >>> response = ortex.get_index_days_to_cover("US-S 500")
    """
    client = get_client(api_key)

    endpoint = "index/short_dtc"
    params: dict[str, Any] = {"index": index}
    if date_val:
        params["date"] = normalize_date(date_val)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


# =============================================================================
# Options Functions
# =============================================================================


def get_options_chain(
    exchange: str,
    ticker: str,
    expiry: str | date | datetime,
    as_of_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get the complete option chain for a stock.

    Retrieves all option contracts for a given ticker and expiry date,
    including strike prices, open interest, volume, and bid/ask data.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        expiry: Option expiry date (required).
        as_of_date: Date for the data snapshot. If None, returns latest.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with option chain data.

    Example:
        >>> response = ortex.get_options_chain("NASDAQ", "AAPL", "2025-03-21")
        >>> df = response.df
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/options/chain"
    params: dict[str, Any] = {"expiry": normalize_date(expiry)}
    if as_of_date:
        params["as_of_date"] = normalize_date(as_of_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


def get_options_details(
    exchange: str,
    ticker: str,
    parameter_name: str,
    as_of_date: str | date | datetime | None = None,
    days_back: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get option metrics for a stock.

    Retrieves a specific option metric such as open interest, volume,
    implied volatility, or greeks.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        parameter_name: Metric to retrieve. One of: "oi", "volume",
            "last_price", "last_size", "ask_price", "ask_size",
            "bid_price", "bid_size", "implied_vol", "delta", "gamma",
            "theta", "vega", "rho", "put_call_oi_ratio",
            "put_call_volume_ratio".
        as_of_date: Date for the data snapshot. If None, returns latest.
        days_back: Number of days back from today (ignored if as_of_date set).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with option detail data.

    Example:
        >>> response = ortex.get_options_details("NASDAQ", "AAPL", "implied_vol")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/options/details/{parameter_name}"
    params: dict[str, Any] = {}
    if as_of_date:
        params["as_of_date"] = normalize_date(as_of_date)
    if days_back is not None:
        params["days_back"] = days_back

    return client.fetch(endpoint, params=params if params else None)


def get_options_expiries(
    exchange: str,
    ticker: str,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get available option expiry dates for a stock.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with option expiry dates.

    Example:
        >>> response = ortex.get_options_expiries("NASDAQ", "AAPL")
        >>> df = response.df
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/options/expiries"
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_options_sentiment(
    exchange: str,
    ticker: str,
    days_fwd: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get Put/Call Ratio (PCR) sentiment data for a stock.

    Retrieves current and historical put/call ratios based on both
    open interest and trading volume.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        days_fwd: Consider contracts expiring within this many days
            (default 1000).
        api_key: Optional API key override.

    Returns:
        OrtexResponse with PCR sentiment data.

    Example:
        >>> response = ortex.get_options_sentiment("NASDAQ", "AAPL")
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/options/sentiment/pcr"
    params: dict[str, Any] = {}
    if days_fwd is not None:
        params["days_fwd"] = days_fwd

    return client.fetch(endpoint, params=params if params else None)


# =============================================================================
# Stock Scores Functions
# =============================================================================


def get_stock_scores(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get stock scores using default weights.

    Returns quality, value, momentum, growth, and total scores for a stock.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date for historical scores.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with stock score data.

    Example:
        >>> response = ortex.get_stock_scores("NASDAQ", "AAPL")
        >>> df = response.df
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/stock_scores"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


def get_stock_scores_custom(
    exchange: str,
    ticker: str,
    weights: dict[str, float],
    from_date: str | date | datetime | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get stock scores with custom weights.

    Allows customizing the weight of each metric in the scoring model.
    Metrics not specified default to 0.

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        weights: Dictionary of metric weights. Keys can include quality
            family metrics (e.g., "quality", "dtc", "roa"), growth metrics
            (e.g., "growth", "internal_growth"), momentum metrics
            (e.g., "momentum", "high_52w"), etc.
        from_date: Start date for historical scores.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with custom-weighted stock score data.

    Example:
        >>> weights = {"quality": 50, "growth": 50, "momentum": 65}
        >>> response = ortex.get_stock_scores_custom("NASDAQ", "AAPL", weights)
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/stock_scores"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)

    return client.fetch_post(endpoint, params=params if params else None, json={"weights": weights})


# =============================================================================
# Stock Splits Functions
# =============================================================================


def get_stock_splits(
    exchange: str,
    ticker: str,
    from_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get stock split history for a stock.

    Returns split dates, ratios, and split types (forward/reverse).

    Args:
        exchange: Exchange code (e.g., "NYSE", "NASDAQ").
        ticker: Stock ticker symbol.
        from_date: Start date for historical data.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with stock split data.

    Example:
        >>> response = ortex.get_stock_splits("NASDAQ", "AAPL")
        >>> df = response.df
    """
    client = get_client(api_key)
    exchange = normalize_exchange(exchange)
    ticker = normalize_ticker(ticker)

    endpoint = f"stock/{exchange}/{ticker}/stock_splits"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)


# =============================================================================
# Official Short Interest Functions
# =============================================================================


def get_official_short_interest(
    ticker: str,
    country_code: str,
    settlement_from_date: str | date | datetime,
    settlement_to_date: str | date | datetime | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get official (FINRA-reported) short interest data.

    Returns officially filed short interest for US, Canada, Australia,
    and Hong Kong.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        country_code: 2-character ISO country code: "US", "CA", "AU", "HK".
        settlement_from_date: Starting settlement date (required).
        settlement_to_date: Ending settlement date. Defaults to
            settlement_from_date if not provided.
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with official short interest data.

    Example:
        >>> response = ortex.get_official_short_interest("AAPL", "US", "2024-01-01")
        >>> df = response.df
    """
    client = get_client(api_key)

    endpoint = "stock/official_short_interest"
    params: dict[str, Any] = {
        "ticker": normalize_ticker(ticker),
        "country_code": country_code.upper(),
        "settlement_from_date": normalize_date(settlement_from_date),
    }
    if settlement_to_date:
        params["settlement_to_date"] = normalize_date(settlement_to_date)
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params)


# =============================================================================
# US Government Trades Functions
# =============================================================================


def get_us_government_trades(
    from_date: str | date | datetime | None = None,
    to_date: str | date | datetime | None = None,
    ticker: str | None = None,
    exchange: str | None = None,
    filer_name: str | None = None,
    party: str | None = None,
    chamber: str | None = None,
    transaction_type: str | None = None,
    page_size: int | None = None,
    page: int | None = None,
    api_key: str | None = None,
) -> OrtexResponse:
    """Get US government officials' stock trades.

    Returns disclosed stock transactions filed by members of the
    U.S. Congress, including transaction details, filer info, and
    committee memberships.

    Args:
        from_date: Transaction start date. Defaults to one year back.
        to_date: Transaction end date. Defaults to today.
        ticker: Filter by stock ticker (e.g., "AAPL").
        exchange: Filter by exchange symbol (e.g., "NYSE").
        filer_name: Filter by filer name.
        party: Filter by political party ("republican", "democrat",
            "independent").
        chamber: Filter by congressional chamber ("house", "senate").
        transaction_type: Filter by transaction type ("buy", "sell",
            "Sell (Partial)").
        page_size: Number of results per page.
        page: Page number for pagination.
        api_key: Optional API key override.

    Returns:
        OrtexResponse with government trade data.

    Example:
        >>> response = ortex.get_us_government_trades(ticker="AAPL")
        >>> response = ortex.get_us_government_trades(party="democrat", chamber="senate")
    """
    client = get_client(api_key)

    endpoint = "us_government_trades"
    params: dict[str, Any] = {}
    if from_date:
        params["from_date"] = normalize_date(from_date)
    if to_date:
        params["to_date"] = normalize_date(to_date)
    if ticker:
        params["ticker"] = normalize_ticker(ticker)
    if exchange:
        params["exchange"] = exchange
    if filer_name:
        params["filerName"] = filer_name
    if party:
        params["party"] = party.lower()
    if chamber:
        params["chamber"] = chamber.lower()
    if transaction_type:
        params["transactionType"] = transaction_type
    if page_size is not None:
        params["page_size"] = page_size
    if page is not None:
        params["page"] = page

    return client.fetch(endpoint, params=params if params else None)
