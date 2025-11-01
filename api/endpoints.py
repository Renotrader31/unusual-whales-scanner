"""
Unusual Whales API Endpoints
Organized by category with helper methods
"""
from typing import Dict, List, Optional
from datetime import date


class Endpoints:
    """API endpoint definitions organized by category."""
    
    # Base API path
    BASE = "/api"
    
    # ==================== OPTIONS FLOW ====================
    @staticmethod
    def flow_alerts(older_than: Optional[str] = None, newer_than: Optional[str] = None) -> tuple:
        """Get options flow alerts with optional time filtering."""
        endpoint = f"{Endpoints.BASE}/option-trades/flow-alerts"
        params = {}
        if older_than:
            params['older_than'] = older_than
        if newer_than:
            params['newer_than'] = newer_than
        return endpoint, params
    
    @staticmethod
    def full_tape(date: str) -> str:
        """Get full tape of option trades for a specific date."""
        return f"{Endpoints.BASE}/option-trades/full-tape/{date}"
    
    @staticmethod
    def greek_flow(flow_group: str, expiry: Optional[str] = None) -> str:
        """Get greek flow for a flow group."""
        if expiry:
            return f"{Endpoints.BASE}/group-flow/{flow_group}/greek-flow/{expiry}"
        return f"{Endpoints.BASE}/group-flow/{flow_group}/greek-flow"
    
    # ==================== MARKET DATA ====================
    @staticmethod
    def top_net_impact(issue_types: Optional[List[str]] = None, 
                       date: Optional[str] = None, 
                       limit: int = 20) -> tuple:
        """Get top tickers by net premium impact."""
        endpoint = f"{Endpoints.BASE}/market/top-net-impact"
        params = {'limit': limit}
        if issue_types:
            params['issue_types[]'] = issue_types
        if date:
            params['date'] = date
        return endpoint, params
    
    @staticmethod
    def market_correlations(tickers: List[str], 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> tuple:
        """Get correlations between tickers."""
        endpoint = f"{Endpoints.BASE}/market/correlations"
        params = {'tickers': ','.join(tickers)}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return endpoint, params
    
    @staticmethod
    def sector_tide(sector: str) -> str:
        """Get market tide for a specific sector."""
        return f"{Endpoints.BASE}/market/{sector}/sector-tide"
    
    @staticmethod
    def etf_tide(ticker: str) -> str:
        """Get ETF tide for a ticker."""
        return f"{Endpoints.BASE}/market/{ticker}/etf-tide"
    
    @staticmethod
    def oi_change() -> str:
        """Get open interest change data."""
        return f"{Endpoints.BASE}/market/oi-change"
    
    @staticmethod
    def fda_calendar() -> str:
        """Get FDA calendar events."""
        return f"{Endpoints.BASE}/market/fda-calendar"
    
    # ==================== STOCK DATA ====================
    @staticmethod
    def stock_state(ticker: str) -> str:
        """Get current stock state (price, volume, prev close)."""
        return f"{Endpoints.BASE}/stock/{ticker}/stock-state"
    
    @staticmethod
    def option_contracts(ticker: str) -> str:
        """Get option contracts for a stock (max 500)."""
        return f"{Endpoints.BASE}/stock/{ticker}/option-contracts"
    
    @staticmethod
    def expiry_breakdown(ticker: str) -> str:
        """Get option expiry breakdown."""
        return f"{Endpoints.BASE}/stock/{ticker}/expiry-breakdown"
    
    @staticmethod
    def max_pain(ticker: str) -> str:
        """Get max pain value."""
        return f"{Endpoints.BASE}/stock/{ticker}/max-pain"
    
    @staticmethod
    def flow_per_strike_intraday(ticker: str) -> str:
        """Get intraday flow per strike."""
        return f"{Endpoints.BASE}/stock/{ticker}/flow-per-strike-intraday"
    
    @staticmethod
    def oi_per_strike(ticker: str) -> str:
        """Get open interest per strike."""
        return f"{Endpoints.BASE}/stock/{ticker}/oi-per-strike"
    
    @staticmethod
    def oi_per_expiry(ticker: str) -> str:
        """Get open interest per expiry."""
        return f"{Endpoints.BASE}/stock/{ticker}/oi-per-expiry"
    
    @staticmethod
    def realized_volatility(ticker: str) -> str:
        """Get realized volatility."""
        return f"{Endpoints.BASE}/stock/{ticker}/volatility/realized"
    
    @staticmethod
    def nope(ticker: str) -> str:
        """Get NOPE (Net Options Pricing Effect)."""
        return f"{Endpoints.BASE}/stock/{ticker}/nope"
    
    @staticmethod
    def net_prem_ticks(ticker: str) -> str:
        """Get net premium ticks with volume breakdown."""
        return f"{Endpoints.BASE}/stock/{ticker}/net-prem-ticks"
    
    @staticmethod
    def interpolated_iv(ticker: str) -> str:
        """Get interpolated implied volatility."""
        return f"{Endpoints.BASE}/stock/{ticker}/interpolated-iv"
    
    # ==================== GREEKS ====================
    @staticmethod
    def greeks(ticker: str) -> str:
        """Get greek values with option symbols."""
        return f"{Endpoints.BASE}/stock/{ticker}/greeks"
    
    @staticmethod
    def greek_exposure_strike(ticker: str) -> str:
        """Get greek exposure by strike."""
        return f"{Endpoints.BASE}/stock/{ticker}/greek-exposure/strike"
    
    @staticmethod
    def greek_exposure_expiry(ticker: str) -> str:
        """Get greek exposure by expiry."""
        return f"{Endpoints.BASE}/stock/{ticker}/greek-exposure/expiry"
    
    @staticmethod
    def greek_exposure_strike_expiry(ticker: str) -> str:
        """Get greek exposure by strike and expiry."""
        return f"{Endpoints.BASE}/stock/{ticker}/greek-exposure/strike-expiry"
    
    @staticmethod
    def spot_exposures(ticker: str, expirations: Optional[List[str]] = None) -> tuple:
        """Get spot exposures with optional expiry filter."""
        endpoint = f"{Endpoints.BASE}/stock/{ticker}/spot-exposures"
        params = {}
        if expirations:
            params['expirations[]'] = expirations
        return endpoint, params
    
    @staticmethod
    def spot_exposures_expiry_strike(ticker: str, expirations: List[str]) -> tuple:
        """Get spot exposures by expiry and strike."""
        endpoint = f"{Endpoints.BASE}/stock/{ticker}/spot-exposures/expiry-strike"
        params = {'expirations[]': expirations}
        return endpoint, params
    
    @staticmethod
    def historical_risk_reversal_skew(ticker: str) -> str:
        """Get historical risk reversal skew."""
        return f"{Endpoints.BASE}/stock/{ticker}/historical_risk_reversal_skew"
    
    @staticmethod
    def ticker_greek_flow(ticker: str, expiry: Optional[str] = None) -> str:
        """Get greek flow for a ticker."""
        if expiry:
            return f"{Endpoints.BASE}/stock/{ticker}/greek-flow/{expiry}"
        return f"{Endpoints.BASE}/stock/{ticker}/greek-flow"
    
    # ==================== DARK POOL ====================
    @staticmethod
    def dark_pool(ticker: str, 
                  older_than: Optional[str] = None,
                  newer_than: Optional[str] = None) -> tuple:
        """Get dark pool trades with optional filters."""
        endpoint = f"{Endpoints.BASE}/darkpool/{ticker}"
        params = {}
        if older_than:
            params['older_than'] = older_than
        if newer_than:
            params['newer_than'] = newer_than
        return endpoint, params
    
    # ==================== INSTITUTIONAL ====================
    @staticmethod
    def institutions_list() -> str:
        """Get list of institutions."""
        return f"{Endpoints.BASE}/institutions"
    
    @staticmethod
    def institution_holdings(name: str) -> str:
        """Get holdings for an institution."""
        return f"{Endpoints.BASE}/institution/{name}/holdings"
    
    @staticmethod
    def institution_activity(name: str) -> str:
        """Get activity for an institution."""
        return f"{Endpoints.BASE}/institution/{name}/activity"
    
    @staticmethod
    def institution_sectors(name: str) -> str:
        """Get sector exposure for an institution."""
        return f"{Endpoints.BASE}/institution/{name}/sectors"
    
    @staticmethod
    def institution_ownership(ticker: str) -> str:
        """Get institutional ownership for a ticker."""
        return f"{Endpoints.BASE}/institution/{ticker}/ownership"
    
    @staticmethod
    def latest_filings() -> str:
        """Get latest institutional filings."""
        return f"{Endpoints.BASE}/institution/latest_filings"
    
    @staticmethod
    def etf_inflow_outflow(ticker: str) -> str:
        """Get ETF inflow/outflow data."""
        return f"{Endpoints.BASE}/etfs/{ticker}/in_outflow"
    
    # ==================== NET FLOW ====================
    @staticmethod
    def net_flow_expiry() -> str:
        """Get net premium flow by expiry."""
        return f"{Endpoints.BASE}/net-flow/expiry"
    
    # ==================== NEWS ====================
    @staticmethod
    def news_headlines() -> str:
        """Get financial news headlines."""
        return f"{Endpoints.BASE}/news/headlines"
    
    # ==================== SHORT INTEREST ====================
    @staticmethod
    def shorts_data(ticker: str) -> str:
        """Get short interest data."""
        return f"{Endpoints.BASE}/shorts/{ticker}/data"
    
    @staticmethod
    def shorts_volumes_by_exchange(ticker: str) -> str:
        """Get short volumes by exchange."""
        return f"{Endpoints.BASE}/shorts/{ticker}/volumes-by-exchange"
    
    @staticmethod
    def shorts_ftds(ticker: str) -> str:
        """Get fail-to-deliver statistics."""
        return f"{Endpoints.BASE}/shorts/{ticker}/ftds"
    
    @staticmethod
    def shorts_interest_float(ticker: str) -> str:
        """Get short interest as % of float."""
        return f"{Endpoints.BASE}/shorts/{ticker}/interest-float"
    
    @staticmethod
    def shorts_volume_ratio(ticker: str) -> str:
        """Get short volume and ratio."""
        return f"{Endpoints.BASE}/shorts/{ticker}/volume-and-ratio"
    
    # ==================== SEASONALITY ====================
    @staticmethod
    def seasonality_market() -> str:
        """Get market seasonality data."""
        return f"{Endpoints.BASE}/seasonality/market"
    
    @staticmethod
    def seasonality_month_performers(month: int) -> str:
        """Get top/poor performers for a month."""
        return f"{Endpoints.BASE}/seasonality/{month}/performers"
    
    @staticmethod
    def seasonality_ticker_monthly(ticker: str) -> str:
        """Get ticker seasonality by month."""
        return f"{Endpoints.BASE}/seasonality/{ticker}/monthly"
    
    @staticmethod
    def seasonality_ticker_year_month(ticker: str, year: int, month: int) -> str:
        """Get ticker seasonality for specific year-month."""
        return f"{Endpoints.BASE}/seasonality/{ticker}/year-month"
    
    # ==================== ALERTS ====================
    @staticmethod
    def alerts_configuration() -> str:
        """Get alert configurations."""
        return f"{Endpoints.BASE}/alerts/configuration"
    
    @staticmethod
    def alerts(older_than: Optional[str] = None, newer_than: Optional[str] = None) -> tuple:
        """Get triggered alerts with optional time filtering."""
        endpoint = f"{Endpoints.BASE}/alerts"
        params = {}
        if older_than:
            params['older_than'] = older_than
        if newer_than:
            params['newer_than'] = newer_than
        return endpoint, params
    
    # ==================== CONGRESS ====================
    @staticmethod
    def congress_recent_trades() -> str:
        """Get recent congressional trades."""
        return f"{Endpoints.BASE}/congress/recent-trades"
    
    # ==================== OPTION CONTRACT ====================
    @staticmethod
    def option_contract_volume_profile(contract_id: str) -> str:
        """Get volume profile for option contract."""
        return f"{Endpoints.BASE}/option-contract/{contract_id}/volume-profile"
    
    @staticmethod
    def option_contract_intraday(contract_id: str) -> str:
        """Get intraday data for option contract (1-min ticks)."""
        return f"{Endpoints.BASE}/option-contract/{contract_id}/intraday"
    
    @staticmethod
    def option_contract_flow(contract_id: str, date: str) -> str:
        """Get flow for specific option contract."""
        return f"{Endpoints.BASE}/option-contract/{contract_id}/flow?date={date}"
