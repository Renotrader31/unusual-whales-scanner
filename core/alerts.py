"""
Alert System - Discord, Telegram, Email notifications
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger


class AlertManager:
    """Manages alerts across multiple channels"""
    
    def __init__(self, config):
        self.config = config
        
        # Discord webhook
        self.discord_webhook = config.DISCORD_WEBHOOK_URL if hasattr(config, 'DISCORD_WEBHOOK_URL') else None
        
        # Telegram bot
        self.telegram_token = config.TELEGRAM_BOT_TOKEN if hasattr(config, 'TELEGRAM_BOT_TOKEN') else None
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID if hasattr(config, 'TELEGRAM_CHAT_ID') else None
        
        # Email (future)
        self.email_enabled = False
        
        # Alert history (prevent spam)
        self.recent_alerts = []
        self.cooldown_seconds = 300  # 5 minutes between same alerts
        
        logger.info(f"Alert Manager initialized - Discord: {bool(self.discord_webhook)}, Telegram: {bool(self.telegram_token)}")
    
    async def send_alert(self, alert: Dict):
        """Send alert to all configured channels"""
        # Check cooldown
        if self._is_duplicate(alert):
            logger.debug(f"Skipping duplicate alert for {alert.get('ticker')}")
            return
        
        # Format alert
        message = self._format_alert(alert)
        
        # Send to all channels
        tasks = []
        
        if self.discord_webhook:
            tasks.append(self._send_discord(message, alert))
        
        if self.telegram_token and self.telegram_chat_id:
            tasks.append(self._send_telegram(message, alert))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Alert send error: {result}")
            
            # Add to history
            self.recent_alerts.append({
                'alert': alert,
                'timestamp': datetime.now()
            })
            
            # Cleanup old alerts
            self._cleanup_history()
    
    async def _send_discord(self, message: str, alert: Dict):
        """Send alert to Discord"""
        try:
            mode = alert.get('mode', 1)
            priority = alert.get('priority', 5)
            ticker = alert.get('ticker', 'SPY')
            score = alert.get('score', 0)
            
            # Color based on mode
            color_map = {
                1: 0x00D9FF,  # Cyan for intraday
                2: 0xFFAA00,  # Orange for swing
                3: 0x00FF00   # Green for long-term
            }
            color = color_map.get(mode, 0x808080)
            
            # Build embed
            embed = {
                "title": f"🚨 {self._get_mode_name(mode)} Alert",
                "description": message,
                "color": color,
                "fields": [
                    {
                        "name": "Ticker",
                        "value": ticker,
                        "inline": True
                    },
                    {
                        "name": "Score",
                        "value": f"{score:.1f}/10",
                        "inline": True
                    },
                    {
                        "name": "Priority",
                        "value": self._get_priority_emoji(priority),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"UW Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add mode-specific fields
            if mode == 1:  # Intraday
                if 'direction' in alert:
                    embed['fields'].append({
                        "name": "Direction",
                        "value": alert['direction'],
                        "inline": True
                    })
            elif mode == 2:  # Swing
                if 'strategy' in alert:
                    embed['fields'].append({
                        "name": "Strategy",
                        "value": alert['strategy'],
                        "inline": False
                    })
            elif mode == 3:  # Long-term
                if 'thesis' in alert:
                    embed['fields'].append({
                        "name": "Investment Thesis",
                        "value": alert['thesis'],
                        "inline": False
                    })
                if 'catalysts' in alert:
                    catalysts = alert['catalysts']
                    if catalysts:
                        embed['fields'].append({
                            "name": "Catalysts",
                            "value": "\n".join(f"• {c}" for c in catalysts[:3]),
                            "inline": False
                        })
            
            payload = {
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 204:
                        logger.info(f"✅ Discord alert sent: {ticker}")
                    else:
                        logger.warning(f"Discord alert failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Discord alert error: {e}")
            raise
    
    async def _send_telegram(self, message: str, alert: Dict):
        """Send alert to Telegram"""
        try:
            mode = alert.get('mode', 1)
            ticker = alert.get('ticker', 'SPY')
            score = alert.get('score', 0)
            priority = alert.get('priority', 5)
            
            # Format for Telegram (Markdown)
            mode_emoji = {1: "⚡", 2: "📊", 3: "🎯"}
            emoji = mode_emoji.get(mode, "🔔")
            
            tg_message = f"{emoji} *{self._get_mode_name(mode)} Alert*\n\n"
            tg_message += f"*{ticker}* - Score: `{score:.1f}/10`\n"
            tg_message += f"Priority: {self._get_priority_emoji(priority)}\n\n"
            tg_message += message
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": tg_message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Telegram alert sent: {ticker}")
                    else:
                        text = await response.text()
                        logger.warning(f"Telegram alert failed: {response.status} - {text}")
            
        except Exception as e:
            logger.error(f"Telegram alert error: {e}")
            raise
    
    def _format_alert(self, alert: Dict) -> str:
        """Format alert message"""
        mode = alert.get('mode', 1)
        ticker = alert.get('ticker', 'SPY')
        score = alert.get('score', 0)
        
        if mode == 1:  # Intraday
            direction = alert.get('direction', 'N/A')
            signal_type = alert.get('signal_type', 'N/A')
            return (
                f"**Intraday Signal on {ticker}**\n"
                f"Direction: {direction}\n"
                f"Type: {signal_type}\n"
                f"Score: {score:.1f}/10"
            )
        
        elif mode == 2:  # Swing
            direction = alert.get('direction', 'N/A')
            strategy = alert.get('strategy', 'N/A')
            price = alert.get('price', 0)
            return (
                f"**Swing Trade Setup: {ticker}**\n"
                f"Price: ${price:.2f}\n"
                f"Direction: {direction}\n"
                f"Strategy: {strategy}\n"
                f"Score: {score:.1f}/10"
            )
        
        elif mode == 3:  # Long-term
            thesis = alert.get('thesis', 'N/A')
            conviction = alert.get('conviction', 'N/A')
            price = alert.get('price', 0)
            return (
                f"**Long-Term Investment: {ticker}**\n"
                f"Price: ${price:.2f}\n"
                f"Thesis: {thesis}\n"
                f"Conviction: {conviction}\n"
                f"Score: {score:.1f}/10"
            )
        
        return f"Alert for {ticker} - Score: {score:.1f}/10"
    
    def _is_duplicate(self, alert: Dict) -> bool:
        """Check if alert is duplicate (within cooldown)"""
        ticker = alert.get('ticker')
        mode = alert.get('mode')
        
        now = datetime.now()
        
        for recent in self.recent_alerts:
            recent_alert = recent['alert']
            recent_time = recent['timestamp']
            
            # Check if same ticker + mode within cooldown
            if (recent_alert.get('ticker') == ticker and 
                recent_alert.get('mode') == mode and
                (now - recent_time).total_seconds() < self.cooldown_seconds):
                return True
        
        return False
    
    def _cleanup_history(self):
        """Remove old alerts from history"""
        now = datetime.now()
        self.recent_alerts = [
            r for r in self.recent_alerts
            if (now - r['timestamp']).total_seconds() < self.cooldown_seconds * 2
        ]
    
    def _get_mode_name(self, mode: int) -> str:
        """Get mode name"""
        names = {
            1: "Intraday SPY",
            2: "Swing Trading",
            3: "Long-Term Investment"
        }
        return names.get(mode, "Unknown")
    
    def _get_priority_emoji(self, priority: int) -> str:
        """Get priority emoji"""
        if priority >= 9:
            return "🔥🔥🔥"
        elif priority >= 8:
            return "🔥🔥"
        elif priority >= 7:
            return "🔥"
        else:
            return "⚠️"


class AlertBuilder:
    """Helper to build standardized alerts"""
    
    @staticmethod
    def build_mode1_alert(signal: Dict) -> Dict:
        """Build Mode 1 alert"""
        return {
            'mode': 1,
            'ticker': signal.get('ticker', 'SPY'),
            'score': signal.get('score', 0),
            'direction': signal.get('direction', 'NEUTRAL'),
            'signal_type': signal.get('signal_type', 'Unknown'),
            'confidence': signal.get('confidence', 0),
            'priority': signal.get('priority', 7),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def build_mode2_alert(signal: Dict) -> Dict:
        """Build Mode 2 alert"""
        return {
            'mode': 2,
            'ticker': signal.get('ticker', 'N/A'),
            'price': signal.get('price', 0),
            'score': signal.get('score', 0),
            'direction': signal.get('direction', 'NEUTRAL'),
            'strategy': signal.get('strategy', 'N/A'),
            'confidence': signal.get('confidence', 'LOW'),
            'priority': signal.get('priority', 7),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def build_mode3_alert(signal: Dict) -> Dict:
        """Build Mode 3 alert"""
        return {
            'mode': 3,
            'ticker': signal.get('ticker', 'N/A'),
            'price': signal.get('price', 0),
            'score': signal.get('score', 0),
            'thesis': signal.get('thesis', 'N/A'),
            'catalysts': signal.get('catalysts', []),
            'conviction': signal.get('conviction', 'LOW'),
            'priority': signal.get('priority', 8),
            'timestamp': datetime.now().isoformat()
        }
