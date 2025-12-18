"""Tests for ORTEX API functions."""

from __future__ import annotations

import pandas as pd
import responses

import ortex
from ortex import OrtexResponse


def make_paginated_response(
    rows: list[dict],
    credits_used: float = 1.0,
    credits_left: float = 1000.0,
) -> dict:
    """Create a standard paginated API response."""
    return {
        "paginationLinks": {"next": None, "previous": None},
        "length": len(rows),
        "rows": rows,
        "creditsUsed": credits_used,
        "creditsLeft": credits_left,
    }


def make_fundamentals_response(
    data: dict,
    company: str = "Test Company",
    period: str = "2024Q3",
    category: str = "income",
    credits_used: float = 0.1,
    credits_left: float = 1000.0,
) -> dict:
    """Create a fundamentals API response."""
    return {
        "company": company,
        "period": period,
        "category": category,
        "data": data,
        "creditsUsed": credits_used,
        "creditsLeft": credits_left,
    }


class TestShortInterestFunctions:
    """Tests for short interest API functions."""

    @responses.activate
    def test_get_short_interest(self, api_key: str) -> None:
        """Test get_short_interest function."""
        rows = [{"date": "2024-12-17", "sharesOnLoan": 1000000, "utilization": 85.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/NYSE/AMC/short_interest",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_short_interest("NYSE", "AMC")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)
        assert len(response.df) == 1
        assert "sharesOnLoan" in response.df.columns
        assert response.credits_used == 1.0

    @responses.activate
    def test_get_short_interest_with_dates(self, api_key: str) -> None:
        """Test get_short_interest with date range."""
        rows = [{"date": "2024-01-01", "sharesOnLoan": 500000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/NYSE/AMC/short_interest",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_short_interest("NYSE", "AMC", "2024-01-01", "2024-12-31")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_short_interest_normalizes_input(self, api_key: str) -> None:
        """Test that exchange and ticker are normalized to uppercase."""
        rows = [{"date": "2024-12-17", "sharesOnLoan": 1000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/NYSE/AMC/short_interest",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_short_interest("nyse", "amc")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_short_availability(self, api_key: str) -> None:
        """Test get_short_availability function."""
        rows = [{"date": "2024-12-17", "sharesAvailable": 5000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/AMC/availability",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_short_availability("NYSE", "AMC")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_cost_to_borrow_all(self, api_key: str) -> None:
        """Test get_cost_to_borrow for all loans."""
        rows = [{"date": "2024-12-17", "ctbAvg": 15.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/AMC/ctb/all",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_cost_to_borrow("NYSE", "AMC")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_cost_to_borrow_new(self, api_key: str) -> None:
        """Test get_cost_to_borrow for new loans."""
        rows = [{"date": "2024-12-17", "ctbAvg": 20.0}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/AMC/ctb/new",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_cost_to_borrow("NYSE", "AMC", loan_type="new")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_days_to_cover(self, api_key: str) -> None:
        """Test get_days_to_cover function."""
        rows = [{"date": "2024-12-17", "daysToCover": 3.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/AMC/dtc",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_days_to_cover("NYSE", "AMC")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestIndexFunctions:
    """Tests for index API functions."""

    @responses.activate
    def test_get_index_short_interest(self, api_key: str) -> None:
        """Test get_index_short_interest function."""
        rows = [{"ticker": "AAPL", "sharesOnLoan": 1000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/index/short_interest",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_index_short_interest("US-S 500")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_index_short_availability(self, api_key: str) -> None:
        """Test get_index_short_availability function."""
        rows = [{"ticker": "AAPL", "sharesAvailable": 5000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/index/short_availability",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_index_short_availability("US-S 500")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_index_cost_to_borrow(self, api_key: str) -> None:
        """Test get_index_cost_to_borrow function."""
        rows = [{"ticker": "AAPL", "ctbAvg": 5.0}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/index/short_ctb",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_index_cost_to_borrow("US-S 500")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_index_days_to_cover(self, api_key: str) -> None:
        """Test get_index_days_to_cover function."""
        rows = [{"ticker": "AAPL", "daysToCover": 2.0}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/index/short_dtc",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_index_days_to_cover("US-S 500")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestPriceFunctions:
    """Tests for price API functions."""

    @responses.activate
    def test_get_price(self, api_key: str) -> None:
        """Test get_price function."""
        rows = [{"date": "2024-12-17", "open": 100, "close": 105, "volume": 1000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NASDAQ/AAPL/closing_prices",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_price("NASDAQ", "AAPL")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)
        assert "close" in response.df.columns

    @responses.activate
    def test_get_close_price(self, api_key: str) -> None:
        """Test get_close_price function (alias for get_price)."""
        rows = [{"date": "2024-12-17", "close": 105}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NASDAQ/AAPL/closing_prices",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_close_price("NASDAQ", "AAPL")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestStockDataFunctions:
    """Tests for stock data API functions."""

    @responses.activate
    def test_get_free_float(self, api_key: str) -> None:
        """Test get_free_float function."""
        rows = [{"date": "2024-12-17", "freeFloat": 500000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/free_float",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_free_float("NYSE", "F", "2024-01-01")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_shares_outstanding(self, api_key: str) -> None:
        """Test get_shares_outstanding function."""
        rows = [{"date": "2024-12-17", "sharesOutstanding": 600000000}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/free_float",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_shares_outstanding("NYSE", "F", "2024-01-01")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestFundamentalsFunctions:
    """Tests for fundamentals API functions."""

    @responses.activate
    def test_get_income_statement(self, api_key: str) -> None:
        """Test get_income_statement function."""
        data = {"revenue": 50000000000, "netIncome": 5000000000}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/fundamentals/income",
            json=make_fundamentals_response(data, category="income"),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_income_statement("NYSE", "F", "2024Q3")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)
        assert response.company == "Test Company"
        assert response.period == "2024Q3"
        assert response.category == "income"

    @responses.activate
    def test_get_balance_sheet(self, api_key: str) -> None:
        """Test get_balance_sheet function."""
        data = {"totalAssets": 100000000000}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/fundamentals/balance",
            json=make_fundamentals_response(data, category="balance"),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_balance_sheet("NYSE", "F", "2024Q3")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_cash_flow(self, api_key: str) -> None:
        """Test get_cash_flow function."""
        data = {"operatingCashFlow": 10000000000}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/fundamentals/cash",
            json=make_fundamentals_response(data, category="cash"),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_cash_flow("NYSE", "F", "2024Q3")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_financial_ratios(self, api_key: str) -> None:
        """Test get_financial_ratios function."""
        data = {"peRatio": 15.5, "roe": 0.12}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/fundamentals/ratios",
            json=make_fundamentals_response(data, category="ratios"),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_financial_ratios("NYSE", "F", "2024Q3")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_fundamentals_summary(self, api_key: str) -> None:
        """Test get_fundamentals_summary function."""
        data = {"marketCap": 50000000000}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/fundamentals/summary",
            json=make_fundamentals_response(data, category="summary"),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_fundamentals_summary("NYSE", "F", "2024Q3")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_valuation(self, api_key: str) -> None:
        """Test get_valuation function."""
        data = {"enterpriseValue": 60000000000}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/NYSE/F/fundamentals/valuation",
            json=make_fundamentals_response(data, category="valuation"),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_valuation("NYSE", "F", "2024Q3")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestEUShortInterestFunctions:
    """Tests for EU short interest API functions."""

    @responses.activate
    def test_get_eu_short_positions(self, api_key: str) -> None:
        """Test get_eu_short_positions function."""
        rows = [{"holder": "Test Fund", "position": 0.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/XETR/SAP/european_short_interest_filings/open_positions_at",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_eu_short_positions("XETR", "SAP")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_eu_short_positions_history(self, api_key: str) -> None:
        """Test get_eu_short_positions_history function."""
        rows = [{"date": "2024-01-01", "position": 0.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/XETR/SAP/european_short_interest_filings/positions_in_range",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_eu_short_positions_history("XETR", "SAP", "2024-01-01")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_eu_short_total(self, api_key: str) -> None:
        """Test get_eu_short_total function."""
        rows = [{"totalPosition": 2.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/stock/XETR/SAP/european_short_interest_filings/total_open_positions",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_eu_short_total("XETR", "SAP")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestMarketDataFunctions:
    """Tests for market data API functions."""

    @responses.activate
    def test_get_earnings(self, api_key: str) -> None:
        """Test get_earnings function."""
        rows = [{"ticker": "AAPL", "date": "2024-12-20", "epsEstimate": 2.5}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/earnings",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_earnings()

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_earnings_with_dates(self, api_key: str) -> None:
        """Test get_earnings with date range."""
        rows = [{"ticker": "AAPL", "date": "2024-12-01"}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/earnings",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_earnings("2024-12-01", "2024-12-31")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_exchanges(self, api_key: str) -> None:
        """Test get_exchanges function."""
        rows = [{"code": "NYSE", "name": "New York Stock Exchange", "country": "United States"}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/generics/exchanges",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_exchanges()

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_exchanges_with_country(self, api_key: str) -> None:
        """Test get_exchanges with country filter."""
        rows = [{"code": "NYSE", "name": "New York Stock Exchange"}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/generics/exchanges",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_exchanges("United States")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)

    @responses.activate
    def test_get_macro_events(self, api_key: str) -> None:
        """Test get_macro_events function."""
        rows = [{"event": "GDP Release", "date": "2024-12-20"}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/macro_events",
            json=make_paginated_response(rows),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_macro_events("US")

        assert isinstance(response, OrtexResponse)
        assert isinstance(response.df, pd.DataFrame)


class TestOrtexResponseFeatures:
    """Tests for OrtexResponse features."""

    @responses.activate
    def test_credits_tracking(self, api_key: str) -> None:
        """Test that credits are properly tracked."""
        rows = [{"date": "2024-12-17", "value": 100}]
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/NYSE/AMC/short_interest",
            json=make_paginated_response(rows, credits_used=2.5, credits_left=997.5),
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_short_interest("NYSE", "AMC")

        assert response.credits_used == 2.5
        assert response.credits_left == 997.5

    @responses.activate
    def test_pagination_info(self, api_key: str) -> None:
        """Test pagination information."""
        rows = [{"date": "2024-12-17", "value": 100}]
        json_response = make_paginated_response(rows)
        json_response["paginationLinks"] = {
            "next": "https://api.ortex.com/api/v1/NYSE/AMC/short_interest?page=2",
            "previous": None,
        }
        json_response["length"] = 200

        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/NYSE/AMC/short_interest",
            json=json_response,
            status=200,
        )

        ortex.set_api_key(api_key)
        response = ortex.get_short_interest("NYSE", "AMC")

        assert response.length == 200
        assert response.has_next_page is True
        assert response.has_previous_page is False


class TestApiKeyConfiguration:
    """Tests for API key configuration."""

    def test_set_api_key(self) -> None:
        """Test setting API key."""
        ortex.set_api_key("test-key")
        client = ortex.get_client()
        assert client.api_key == "test-key"

    def test_get_client_with_explicit_key(self) -> None:
        """Test getting client with explicit key."""
        client = ortex.get_client(api_key="explicit-key")
        assert client.api_key == "explicit-key"
