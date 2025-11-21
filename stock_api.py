"""
Stock Data API Module
Fetches real-time stock data with comprehensive metrics for synesthetic visualization
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Cache to avoid excessive API calls
_cache = {}
_cache_timestamp = {}
CACHE_DURATION = 300  # 5 minutes in seconds

# Curated list of popular stocks across sectors for visualization
STOCK_TICKERS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO",
    # Cloud & Software
    "CRM", "ADBE", "NOW", "INTU", "TEAM", "PLTR", "SNOW", "DDOG",
    # Semiconductors
    "AMD", "INTC", "QCOM", "MU", "AMAT", "LRCX", "KLAC", "TSM",
    # Finance
    "JPM", "BAC", "GS", "MS", "V", "MA", "PYPL", "SQ",
    # Consumer
    "WMT", "TGT", "COST", "NKE", "SBUX", "MCD", "DIS", "NFLX",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "TMO", "DHR", "LLY", "MRNA",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG",
    # Automotive
    "F", "GM", "RIVN", "LCID",
    # E-commerce & Retail
    "SHOP", "ETSY", "MELI", "SPOT",
    # Aerospace & Defense
    "BA", "LMT", "RTX", "NOC",
    # Growth Stocks
    "ROKU", "COIN", "RBLX", "U", "DASH", "ABNB",
    # Cloud Infrastructure
    "NET", "FSLY", "DOCN",
    # Cybersecurity
    "CRWD", "ZS", "PANW", "FTNT",
    # AI/ML
    "AI", "SMCI", "DELL"
]


def fetch_market_snapshot(tickers: Optional[List[str]] = None, max_stocks: int = 60) -> pd.DataFrame:
    """
    Fetch comprehensive stock data for visualization
    
    Args:
        tickers: List of ticker symbols (uses default list if None)
        max_stocks: Maximum number of stocks to return
        
    Returns:
        DataFrame with columns: ticker, price, change_pct, volume, market_cap,
                                operating_margin, revenue_growth, pe_ratio, beta,
                                volatility, rule_of_40, debt_to_equity
    """
    cache_key = "market_snapshot"
    
    # Check cache
    if cache_key in _cache and cache_key in _cache_timestamp:
        if time.time() - _cache_timestamp[cache_key] < CACHE_DURATION:
            print("📦 Using cached market data")
            return _cache[cache_key]
    
    if tickers is None:
        tickers = STOCK_TICKERS[:max_stocks]
    
    print(f"🔄 Fetching data for {len(tickers)} stocks...")
    
    stocks_data = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price and daily change
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', current_price)
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            # Get volume and market cap
            volume = info.get('volume', 0) or info.get('regularMarketVolume', 0)
            market_cap = info.get('marketCap', 0)
            
            # Get financial metrics for Rule of 40
            operating_margin = info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0
            revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
            
            # Calculate Rule of 40 score
            rule_of_40 = operating_margin + revenue_growth
            
            # Get valuation metrics
            pe_ratio = info.get('trailingPE', 0) or info.get('forwardPE', 0)
            
            # Get risk metrics
            beta = info.get('beta', 1.0) or 1.0
            
            # Estimate volatility from 52-week range
            high_52w = info.get('fiftyTwoWeekHigh', current_price)
            low_52w = info.get('fiftyTwoWeekLow', current_price)
            avg_price = (high_52w + low_52w) / 2 if low_52w > 0 else current_price
            volatility = ((high_52w - low_52w) / avg_price * 100) if avg_price > 0 else 0
            
            # Get debt metrics
            debt_to_equity = info.get('debtToEquity', 0) or 0
            
            # Get momentum (week/month performance)
            week_change = 0
            month_change = 0
            try:
                hist = stock.history(period="1mo")
                if len(hist) > 0:
                    month_ago_price = hist['Close'].iloc[0]
                    month_change = ((current_price - month_ago_price) / month_ago_price * 100)
                if len(hist) >= 5:
                    week_ago_price = hist['Close'].iloc[-5]
                    week_change = ((current_price - week_ago_price) / week_ago_price * 100)
            except:
                pass
            
            stocks_data.append({
                'ticker': ticker,
                'price': round(current_price, 2),
                'change_pct': round(change_pct, 2),
                'week_change': round(week_change, 2),
                'month_change': round(month_change, 2),
                'volume': volume,
                'market_cap': market_cap,
                'operating_margin': round(operating_margin, 2),
                'revenue_growth': round(revenue_growth, 2),
                'rule_of_40': round(rule_of_40, 2),
                'pe_ratio': round(pe_ratio, 2) if pe_ratio else 0,
                'beta': round(beta, 2),
                'volatility': round(volatility, 2),
                'debt_to_equity': round(debt_to_equity, 2),
                'sector': info.get('sector', 'Unknown')
            })
            
        except Exception as e:
            print(f"⚠️  Error fetching {ticker}: {str(e)}")
            continue
    
    df = pd.DataFrame(stocks_data)
    
    # Cache the result
    _cache[cache_key] = df
    _cache_timestamp[cache_key] = time.time()
    
    print(f"✅ Successfully fetched {len(df)} stocks")
    return df


def fetch_top_gainers(df: Optional[pd.DataFrame] = None, top_n: int = 20) -> pd.DataFrame:
    """Get top gaining stocks by daily change percentage"""
    if df is None:
        df = fetch_market_snapshot()
    
    return df.nlargest(top_n, 'change_pct')


def fetch_most_traded(df: Optional[pd.DataFrame] = None, top_n: int = 20) -> pd.DataFrame:
    """Get most actively traded stocks by volume"""
    if df is None:
        df = fetch_market_snapshot()
    
    return df.nlargest(top_n, 'volume')


def fetch_best_value_rule40(df: Optional[pd.DataFrame] = None, min_rule40: float = 40, top_n: int = 20) -> pd.DataFrame:
    """
    Get best value stocks based on Rule of 40
    Filter for stocks with Rule of 40 >= min_rule40
    """
    if df is None:
        df = fetch_market_snapshot()
    
    # Filter for positive Rule of 40 scores
    value_stocks = df[df['rule_of_40'] >= min_rule40]
    
    # Sort by Rule of 40 score
    return value_stocks.nlargest(top_n, 'rule_of_40')


def get_sector_stocks(sector: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Filter stocks by sector"""
    if df is None:
        df = fetch_market_snapshot()
    
    return df[df['sector'] == sector]


def clear_cache():
    """Clear the data cache - useful for forcing refresh"""
    global _cache, _cache_timestamp
    _cache = {}
    _cache_timestamp = {}
    print("🗑️  Cache cleared")


if __name__ == "__main__":
    # Test the API
    print("Testing Stock API...")
    df = fetch_market_snapshot(max_stocks=20)
    print("\n📊 Sample Data:")
    print(df[['ticker', 'price', 'change_pct', 'rule_of_40', 'volume']].head(10))
    
    print("\n📈 Top Gainers:")
    print(fetch_top_gainers(df, 5)[['ticker', 'change_pct', 'price']])
    
    print("\n💎 Best Value (Rule of 40):")
    print(fetch_best_value_rule40(df, min_rule40=30, top_n=5)[['ticker', 'rule_of_40', 'operating_margin', 'revenue_growth']])
