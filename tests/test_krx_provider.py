import unittest
from unittest.mock import patch
import pandas as pd

from risk_radar_mcp.providers.krx_provider import (
    krx_ohlcv,
    investor_flow,
    market_investor_flow,
    krx_market_snapshot,
)

class TestKrxProvider(unittest.TestCase):
    @patch("pykrx.stock.get_market_ohlcv")
    def test_krx_ohlcv(self, mock_get):
        df = pd.DataFrame(
            {"시가": [100], "고가": [110], "저가": [90], "종가": [105], "거래량": [1000]},
            index=pd.date_range("2023-01-01", periods=1)
        )
        mock_get.return_value = df
        
        res = krx_ohlcv("005930", "20230101", "20230101")
        self.assertEqual(res["symbol"], "005930")
        self.assertEqual(len(res["rows"]), 1)
        self.assertEqual(res["rows"][0]["종가"], 105)
        self.assertIn("stale_label", res)

    @patch("pykrx.stock.get_market_ohlcv")
    def test_krx_ohlcv_error(self, mock_get):
        mock_get.side_effect = Exception("API Error")
        
        res = krx_ohlcv("005930")
        self.assertEqual(res["symbol"], "005930")
        self.assertEqual(len(res["rows"]), 0)
        self.assertIn("error", res)

    @patch("pykrx.stock.get_market_trading_value_by_investor")
    def test_investor_flow(self, mock_get):
        df = pd.DataFrame(
            {"기관합계": [100], "기타법인": [0], "개인": [-50], "외국인합계": [-50], "전체": [0]},
            index=pd.date_range("2023-01-01", periods=1)
        )
        mock_get.return_value = df
        
        res = investor_flow("005930", "20230101", "20230101")
        self.assertEqual(res["symbol"], "005930")
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["items"][0]["기관합계"], 100)

    @patch("pykrx.stock.get_market_trading_value_by_investor")
    def test_investor_flow_error(self, mock_get):
        mock_get.side_effect = Exception("API Error")
        res = investor_flow("005930")
        self.assertIn("error", res)

    @patch("pykrx.stock.get_market_net_purchases_of_equities_by_investor", create=True)
    def test_market_investor_flow(self, mock_get):
        df = pd.DataFrame(
            {"순매수": [100]},
            index=pd.Index(["기관합계"])
        )
        mock_get.return_value = df
        
        res = market_investor_flow("20230101")
        self.assertEqual(res["symbol"], "MARKET")
        self.assertEqual(len(res["items"]), 2) # 1 for KOSPI, 1 for KOSDAQ
        self.assertEqual(res["items"][0]["market"], "KOSPI")

    @patch("pykrx.stock.get_market_net_purchases_of_equities_by_investor", create=True)
    def test_market_investor_flow_error(self, mock_get):
        mock_get.side_effect = Exception("API Error")
        res = market_investor_flow()
        self.assertIn("error", res)

    @patch("pykrx.stock.get_index_ohlcv_by_date")
    def test_krx_market_snapshot(self, mock_get):
        df = pd.DataFrame(
            {"종가": [2500]},
            index=pd.date_range("2023-01-01", periods=1)
        )
        mock_get.return_value = df
        
        res = krx_market_snapshot()
        self.assertIn("KOSPI", res["items"])
        self.assertIn("KOSDAQ", res["items"])
        self.assertEqual(res["items"]["KOSPI"]["종가"], 2500)

    @patch("pykrx.stock.get_index_ohlcv_by_date")
    def test_krx_market_snapshot_error(self, mock_get):
        mock_get.side_effect = Exception("API Error")
        res = krx_market_snapshot()
        self.assertIn("error", res["items"]["KOSPI"])
        self.assertIn("error", res["items"]["KOSDAQ"])
