# ORTEX Python SDK

Official Python SDK for the ORTEX Financial Data API. Access comprehensive financial data including short interest, stock prices, fundamentals, and more.

[![PyPI version](https://img.shields.io/pypi/v/ortex.svg)](https://pypi.org/project/ortex/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Short Interest Data** - Shares on loan, utilization, cost to borrow, days to cover
- **Stock Prices** - OHLCV data with historical support
- **Stock Data** - Free float, shares outstanding
- **Fundamentals** - Income statements, balance sheets, cash flow, ratios
- **EU Short Interest** - European regulatory short positions
- **Market Data** - Earnings calendar, macro events, exchanges
- **Pagination Support** - Automatic pagination with `iter_all_pages()`
- **Credit Tracking** - Monitor API credit usage with `credits_used` and `credits_left`

## Installation

```bash
pip install ortex
```

## Quick Start

### Get Your API Key

Get your API key at **[app.ortex.com/apis](https://app.ortex.com/apis)**

### Set Up Authentication

```python
import ortex

# Option 1: Set API key directly
ortex.set_api_key("your-api-key")

# Option 2: Use environment variable
# export ORTEX_API_KEY="your-api-key"
# The SDK will automatically use this

# Option 3: Pass to each function
response = ortex.get_short_interest("NYSE", "AMC", api_key="your-api-key")
```

### Basic Usage

```python
import ortex

ortex.set_api_key("your-api-key")

# Get short interest data
response = ortex.get_short_interest("NYSE", "AMC")
df = response.df  # Access data as DataFrame
print(f"Credits used: {response.credits_used}")
print(f"Credits left: {response.credits_left}")

# Get historical short interest
response = ortex.get_short_interest("NYSE", "AMC", "2024-01-01", "2024-12-31")

# Get stock prices
response = ortex.get_price("NASDAQ", "AAPL", "2024-01-01", "2024-12-31")
df = response.df
```

## Response Object

All functions return an `OrtexResponse` object that provides:

```python
response = ortex.get_short_interest("NYSE", "AMC")

# Access data as DataFrame
df = response.df

# Access raw row data
rows = response.rows

# Credit tracking
print(f"Credits used: {response.credits_used}")
print(f"Credits left: {response.credits_left}")

# Pagination info
print(f"Total results: {response.length}")
print(f"Has next page: {response.has_next_page}")

# Iterate through all pages
for page in response.iter_all_pages():
    process(page.df)

# Get all data at once (fetches all pages)
full_df = response.to_dataframe_all()
```

## Pagination

Control page size and iterate through results:

```python
# Set page size
response = ortex.get_short_interest("NYSE", "AMC", page_size=100)

# Iterate through all pages
all_data = []
for page in response.iter_all_pages():
    all_data.extend(page.rows)
    print(f"Fetched {len(page.rows)} rows, credits used: {page.credits_used}")

# Or get everything at once
full_df = response.to_dataframe_all()
```

## All Available Functions

### Short Interest

```python
# Short interest data for a stock
response = ortex.get_short_interest("NYSE", "AMC")
response = ortex.get_short_interest("NYSE", "AMC", "2024-01-01", "2024-12-31")

# Short interest for an index (S&P 500, NASDAQ 100, etc.)
response = ortex.get_index_short_interest("US-S 500")

# Share availability for shorting
response = ortex.get_short_availability("NYSE", "AMC")

# Cost to borrow (all loans or new loans)
response = ortex.get_cost_to_borrow("NYSE", "AMC")
response = ortex.get_cost_to_borrow("NYSE", "AMC", loan_type="new")

# Days to cover
response = ortex.get_days_to_cover("NYSE", "AMC")
```

### Index Short Data

```python
# Index-level short interest data
response = ortex.get_index_short_interest("US-S 500")
response = ortex.get_index_short_availability("US-S 500")
response = ortex.get_index_cost_to_borrow("US-S 500")
response = ortex.get_index_days_to_cover("US-S 500")
```

### Stock Prices

```python
# OHLCV price data
response = ortex.get_price("NASDAQ", "AAPL")
response = ortex.get_price("NASDAQ", "AAPL", "2024-01-01", "2024-12-31")

# Close price (alias for get_price)
response = ortex.get_close_price("NASDAQ", "AAPL")
```

### Stock Data

```python
# Free float shares (from_date is required)
response = ortex.get_free_float("NYSE", "F", "2024-01-01")

# Shares outstanding (uses free_float endpoint)
response = ortex.get_shares_outstanding("NYSE", "F", "2024-01-01")
```

### Fundamentals

```python
# Income statement
response = ortex.get_income_statement("NYSE", "F", "2024Q3")
print(f"Company: {response.company}")
print(f"Period: {response.period}")
df = response.df  # Financial data as DataFrame

# Balance sheet
response = ortex.get_balance_sheet("NYSE", "F", "2024Q3")

# Cash flow statement
response = ortex.get_cash_flow("NYSE", "F", "2024Q3")

# Financial ratios
response = ortex.get_financial_ratios("NYSE", "F", "2024Q3")

# Fundamentals summary
response = ortex.get_fundamentals_summary("NYSE", "F", "2024Q3")

# Valuation metrics
response = ortex.get_valuation("NYSE", "F", "2024Q3")
```

### EU Short Interest

```python
# EU short positions (individual holders)
response = ortex.get_eu_short_positions("XETR", "SAP")

# EU short positions at a specific date
response = ortex.get_eu_short_positions("XETR", "SAP", "2024-12-01")

# EU short positions history
response = ortex.get_eu_short_positions_history("XETR", "SAP", "2024-01-01", "2024-12-31")

# Total EU short interest
response = ortex.get_eu_short_total("XETR", "SAP")
```

### Market Data

```python
# Earnings calendar
response = ortex.get_earnings("2024-12-01", "2024-12-31")

# List of exchanges
response = ortex.get_exchanges()
response = ortex.get_exchanges("United States")

# Macro economic events
response = ortex.get_macro_events("US")
response = ortex.get_macro_events("US", "2024-12-01", "2024-12-15")
```

## Using the Client Directly

For more control, use the `OrtexClient` class:

```python
from ortex import OrtexClient

# Create client
client = OrtexClient(api_key="your-api-key")

# Make requests (returns raw JSON)
data = client.get("NYSE/AMC/short_interest")

# Make requests with OrtexResponse wrapper
response = client.fetch("NYSE/AMC/short_interest")
df = response.df

# Use as context manager
with OrtexClient(api_key="your-api-key") as client:
    response = client.fetch("stock/NASDAQ/AAPL/closing_prices")
```

## Date Handling

The SDK accepts dates in multiple formats:

```python
from datetime import date, datetime

# String format (YYYY-MM-DD)
response = ortex.get_short_interest("NYSE", "AMC", "2024-01-01", "2024-12-31")

# Python date objects
response = ortex.get_short_interest("NYSE", "AMC", date(2024, 1, 1), date(2024, 12, 31))

# Python datetime objects
response = ortex.get_short_interest("NYSE", "AMC", datetime(2024, 1, 1), datetime(2024, 12, 31))
```

## Error Handling

The SDK provides specific exception types:

```python
import ortex
from ortex import (
    APIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
)

try:
    response = ortex.get_short_interest("NYSE", "INVALID")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except NotFoundError:
    print("Stock not found")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except ServerError:
    print("ORTEX server error")
except APIError as e:
    print(f"API error: {e}")
```

## Rate Limiting

The SDK automatically handles rate limiting with exponential backoff:

- Automatically retries on 429 (rate limit) responses
- Uses exponential backoff (1s, 2s, 4s, 8s, up to 60s)
- Maximum 5 retry attempts by default

Configure retry behavior:

```python
from ortex import OrtexClient

client = OrtexClient(
    api_key="your-api-key",
    timeout=60,      # Request timeout in seconds
    max_retries=10,  # Maximum retry attempts
)
```

## Documentation

- **Full API Documentation**: [docs.ortex.com](https://docs.ortex.com)
- **Get API Key**: [app.ortex.com/apis](https://app.ortex.com/apis)
- **Support**: support@ortex.com

## Requirements

- Python 3.9+
- pandas >= 2.0.0
- requests >= 2.31.0
- tenacity >= 8.2.0

## License

MIT License - ORTEX Technologies LTD

## Version

1.0.3
