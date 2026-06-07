import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

from risk_radar_mcp.providers.yfinance_provider import (
    quote,
    quotes,
    ohlcv,
    news,
    market_snapshot,
)
from risk_radar_mcp.exceptions import ProviderError

class TestQuote(unittest.TestCase):
    @patch("yfinance.Ticker")
    def test_quote_returns_valid_symbol(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        # mock history
        df = pd.DataFrame(
            {"Close": [100.0, 105.0], "Open": [99.0, 101.0], "High": [101.0, 106.0], "Low": [98.0, 100.0], "Volume": [1000, 1100]},
            index=pd.date_range("2023-01-01", periods=2)
        )
        mock_ticker.history.return_value = df
        
        # mock fast_info
        class MockInfo:
            last_price = 105.0
            regular_market_previous_close = 100.0
            currency = "USD"
            exchange = "NMS"
            timezone = "EST"
            
        mock_ticker.fast_info = MockInfo()
        
        result = quote("AAPL")
        
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["last_price"], 105.0)
        self.assertEqual(result["change"], 5.0)
        self.assertEqual(result["change_percent"], 5.0)
        self.assertEqual(result["metadata"]["currency"], "USD")
        
    @patch("yfinance.Ticker")
    def test_quote_unknown_symbol(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        mock_ticker.history.side_effect = Exception("Unknown symbol")
        
        with self.assertRaises(ProviderError):
            quote("UNKNOWN")
            
    @patch("yfinance.Ticker")
    def test_quote_falls_back_to_history(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        df = pd.DataFrame(
            {"Close": [100.0, 105.0], "Open": [99.0, 101.0]},
            index=pd.date_range("2023-01-01", periods=2)
        )
        mock_ticker.history.return_value = df
        
        # no last_price in fast_info
        class EmptyInfo:
            pass
        mock_ticker.fast_info = EmptyInfo()
        
        result = quote("AAPL")
        self.assertEqual(result["last_price"], 105.0)
        self.assertEqual(result["previous_close"], 100.0)

class TestQuotes(unittest.TestCase):
    @patch("yfinance.download")
    def test_quotes_returns_downloaded_data(self, mock_download):
        columns = pd.MultiIndex.from_product([['AAPL', 'MSFT'], ['Close', 'Open']])
        df = pd.DataFrame(index=pd.date_range("2023-01-01", periods=2), columns=columns)
        df.loc[:, ('AAPL', 'Close')] = [140.0, 145.0]
        df.loc[:, ('MSFT', 'Close')] = [290.0, 295.0]
        
        mock_download.return_value = df
        
        result = quotes(["AAPL", "MSFT"])
        
        self.assertEqual(result["source"], "yfinance")
        self.assertEqual(result["count"], 2)
        symbols = [item["symbol"] for item in result["items"]]
        self.assertIn("AAPL", symbols)
        self.assertIn("MSFT", symbols)

class TestOhlcv(unittest.TestCase):
    @patch("yfinance.Ticker")
    def test_ohlcv_returns_history(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        df = pd.DataFrame(
            {"Close": [100.0, 105.0], "Open": [99.0, 101.0]},
            index=pd.date_range("2023-01-01", periods=2)
        )
        mock_ticker.history.return_value = df
        
        result = ohlcv("AAPL")
        
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(result["rows"][0]["Close"], 100.0)

    @patch("yfinance.Ticker")
    def test_ohlcv_respects_limit(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        df = pd.DataFrame(
            {"Close": list(range(10))},
            index=pd.date_range("2023-01-01", periods=10)
        )
        mock_ticker.history.return_value = df
        
        result = ohlcv("AAPL", limit=5)
        
        self.assertEqual(len(result["rows"]), 5)

class TestNews(unittest.TestCase):
    @patch("yfinance.Ticker")
    def test_news_returns_items(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        
        mock_ticker.get_news.return_value = [
            {
                "title": "Test News 1",
                "publisher": "Test Publisher",
                "link": "http://test.com/1",
                "providerPublishTime": 1600000000
            }
        ]
        
        result = news("AAPL")
        
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["title"], "Test News 1")

class TestMarketSnapshot(unittest.TestCase):
    @patch("risk_radar_mcp.providers.yfinance_provider.quote")
    def test_market_snapshot_returns_keys(self, mock_quote):
        mock_quote.return_value = {"symbol": "TEST", "last_price": 100.0}
        
        result = market_snapshot()
        
        self.assertEqual(result["source"], "yfinance")
        self.assertIn("items", result)
        self.assertIn("note", result)
