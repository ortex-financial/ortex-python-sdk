"""Response wrapper for ORTEX API with pagination support."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import OrtexClient


class OrtexResponse:
    """Response wrapper providing access to data, pagination, and credit info.

    This class wraps API responses and provides:
    - Access to data as a pandas DataFrame
    - Credit usage information (credits_used, credits_left)
    - Automatic pagination through iter_all_pages()
    - Total result count via length property

    Example:
        >>> response = ortex.get_short_interest("NYSE", "F")
        >>> print(f"Credits used: {response.credits_used}")
        >>> print(f"Credits left: {response.credits_left}")
        >>> df = response.df  # Get data as DataFrame
        >>> for page in response.iter_all_pages():
        ...     print(page.df)  # Process each page
    """

    def __init__(
        self,
        raw_response: dict[str, Any],
        client: OrtexClient | None = None,
        endpoint: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the response wrapper.

        Args:
            raw_response: Raw API response dictionary containing rows, paginationLinks, etc.
            client: OrtexClient instance for fetching additional pages.
            endpoint: Original endpoint for pagination requests.
            params: Original query parameters for pagination requests.
        """
        self._raw = raw_response
        self._client = client
        self._endpoint = endpoint
        self._params = params or {}
        self._df: pd.DataFrame | None = None

    @property
    def rows(self) -> list[dict[str, Any]]:
        """Get the raw row data from the response.

        For paginated endpoints, this returns the 'rows' array.
        For non-paginated endpoints (like fundamentals), returns a list with
        the 'data' dict as the single element.

        Returns:
            List of dictionaries containing the data rows.
        """
        # Standard paginated response with 'rows'
        if "rows" in self._raw:
            rows = self._raw.get("rows", [])
            if isinstance(rows, list):
                return rows
            return []

        # Fundamentals-style response with 'data' dict
        if "data" in self._raw:
            data = self._raw.get("data", {})
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return data

        return []

    @property
    def data(self) -> dict[str, Any]:
        """Get the raw data dict from non-paginated responses.

        This is useful for fundamentals endpoints that return a single
        data object rather than an array of rows.

        Returns:
            Dictionary containing the data (or empty dict if not available).
        """
        data = self._raw.get("data", {})
        if isinstance(data, dict):
            return data
        return {}

    @property
    def company(self) -> str | None:
        """Get the company name (for fundamentals responses).

        Returns:
            Company name or None if not available.
        """
        return self._raw.get("company")

    @property
    def period(self) -> str | None:
        """Get the period (for fundamentals responses).

        Returns:
            Period string (e.g., "2024Q3") or None if not available.
        """
        return self._raw.get("period")

    @property
    def category(self) -> str | None:
        """Get the category (for fundamentals responses).

        Returns:
            Category string (e.g., "income", "balance") or None.
        """
        return self._raw.get("category")

    @property
    def df(self) -> pd.DataFrame:
        """Get the data as a pandas DataFrame.

        For paginated responses, returns DataFrame from 'rows'.
        For fundamentals responses, returns DataFrame from 'data'.

        Returns:
            DataFrame containing the response data.

        Example:
            >>> response = ortex.get_short_interest("NYSE", "F")
            >>> df = response.df
            >>> print(df.columns)
        """
        if self._df is None:
            rows = self.rows
            if not rows:
                self._df = pd.DataFrame()
            else:
                self._df = pd.DataFrame(rows)
        return self._df

    @property
    def length(self) -> int:
        """Get the total number of results available.

        This represents the total count across all pages, not just the current page.

        Returns:
            Total number of results available.
        """
        length = self._raw.get("length")
        if isinstance(length, int):
            return length
        return len(self.rows)

    @property
    def credits_used(self) -> float:
        """Get the number of credits used by this request.

        Returns:
            Number of credits consumed.
        """
        credits = self._raw.get("creditsUsed", 0)
        if isinstance(credits, (int, float)):
            return float(credits)
        return 0.0

    @property
    def credits_left(self) -> float:
        """Get the remaining credits in your account.

        Returns:
            Number of credits remaining.
        """
        credits = self._raw.get("creditsLeft", 0)
        if isinstance(credits, (int, float)):
            return float(credits)
        return 0.0

    @property
    def pagination_links(self) -> dict[str, str | None]:
        """Get pagination links for next/previous pages.

        Returns:
            Dictionary with 'next' and 'previous' URLs (or None if not available).
        """
        links = self._raw.get("paginationLinks", {})
        if isinstance(links, str):
            # Handle case where paginationLinks is a string representation
            return {"next": None, "previous": None}
        return {
            "next": links.get("next"),
            "previous": links.get("previous"),
        }

    @property
    def has_next_page(self) -> bool:
        """Check if there is a next page of results.

        Returns:
            True if more pages are available.
        """
        return self.pagination_links.get("next") is not None

    @property
    def has_previous_page(self) -> bool:
        """Check if there is a previous page of results.

        Returns:
            True if previous page is available.
        """
        return self.pagination_links.get("previous") is not None

    def next_page(self) -> OrtexResponse | None:
        """Fetch the next page of results.

        Returns:
            OrtexResponse for the next page, or None if no next page.

        Raises:
            ValueError: If client is not available for pagination.

        Example:
            >>> response = ortex.get_short_interest("NYSE", "F", page_size=10)
            >>> while response.has_next_page:
            ...     response = response.next_page()
            ...     process(response.df)
        """
        if not self.has_next_page:
            return None

        if self._client is None:
            raise ValueError("Client not available for pagination. Use iter_all_pages() instead.")

        # Extract page number from next URL or increment current page
        next_url = self.pagination_links.get("next")
        if next_url:
            # Parse page from URL
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(next_url)
            query_params = parse_qs(parsed.query)
            next_page_num = int(query_params.get("page", [2])[0])

            new_params = self._params.copy()
            new_params["page"] = next_page_num

            raw = self._client.get(self._endpoint or "", params=new_params)
            return OrtexResponse(
                raw_response=raw,
                client=self._client,
                endpoint=self._endpoint,
                params=new_params,
            )

        return None

    def iter_all_pages(self) -> Iterator[OrtexResponse]:
        """Iterate through all pages of results.

        Yields each page as an OrtexResponse, starting with the current page.
        Automatically fetches subsequent pages until all data is retrieved.

        Yields:
            OrtexResponse for each page of results.

        Example:
            >>> response = ortex.get_short_interest("NYSE", "F", page_size=100)
            >>> all_data = []
            >>> for page in response.iter_all_pages():
            ...     all_data.extend(page.rows)
            >>> full_df = pd.DataFrame(all_data)
        """
        yield self

        current = self
        while current.has_next_page:
            next_response = current.next_page()
            if next_response is None:
                break
            yield next_response
            current = next_response

    def to_dataframe_all(self) -> pd.DataFrame:
        """Fetch all pages and return combined DataFrame.

        This method iterates through all pages and combines the data
        into a single DataFrame. Use with caution for large datasets.

        Returns:
            DataFrame containing all data from all pages.

        Example:
            >>> response = ortex.get_short_interest("NYSE", "F", page_size=100)
            >>> full_df = response.to_dataframe_all()
        """
        all_rows: list[dict[str, Any]] = []
        for page in self.iter_all_pages():
            all_rows.extend(page.rows)

        if not all_rows:
            return pd.DataFrame()
        return pd.DataFrame(all_rows)

    def __len__(self) -> int:
        """Return the number of rows in the current page.

        Returns:
            Number of rows in the current response.
        """
        return len(self.rows)

    def __repr__(self) -> str:
        """Return string representation of the response.

        Returns:
            String showing key response information.
        """
        return (
            f"OrtexResponse(rows={len(self.rows)}, "
            f"total={self.length}, "
            f"credits_used={self.credits_used}, "
            f"credits_left={self.credits_left})"
        )

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over data rows.

        Yields:
            Each row as a dictionary.
        """
        return iter(self.rows)
