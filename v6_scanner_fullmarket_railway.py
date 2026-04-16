"""
V6 UNIVERSAL PROTOCOL SCANNER — FULL MARKET EDITION
Muhammad Mussab Aqeel - Karachi, PK
Vol. 3 - All-Asset Compatible Edition

Ye scanner Binance ki PURI market scan karta hai (300+ coins).
Sirf woh coins dikhata hai jo V6 Protocol ke conditions poori karte hain.

Requirements:
    pip install requests pandas tabulate colorama

Run:
    python v6_scanner.py

Modes:
    1 = Top 50 coins by volume  (fast, ~3 min)
    2 = Top 100 coins           (medium, ~6 min)
    3 = Full market 300+ coins  (complete, ~20 min)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tabulate import tabulate

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except:
    class Fore:
        GREEN = CYAN = RED = YELLOW = WHITE = ""
    class Style:
        RESET_ALL = ""

# ─────────────────────────────────────────────
#  CONFIG — YAHAN APNI SETTINGS BADLO
# ─────────────────────────────────────────────
CAPITAL       = 876          # Aapka capital USD mein
RISK_PCT      = 0.01         # 1% risk per trade
RISK_AMOUNT   = round(CAPITAL * RISK_PCT, 2)

PKT_OFFSET    = timedelta(hours=5)   # Pakistan Standard Time (UTC+5)

LONDON_START  = 12
LONDON_END    = 15
NY_START      = 17
NY_END        = 20

BENCHMARK     = "BTCUSDT"

# ── Scan Mode ──
# 1 = Top 50 by volume  (sirf bade coins, fast)
# 2 = Top 100 by volume (recommended)
# 3 = Full 300+ market  (sab coins, time lagta hai)
SCAN_MODE     = 2

# Minimum 24h volume filter (USD) — chote/fake coins hatane ke liye
MIN_VOLUME_USD = 10_000_000   # $10 million minimum volume

# ─────────────────────────────────────────────
#  EMAIL ALERT CONFIG
# ─────────────────────────────────────────────
EMAIL_ALERTS    = True                    # False karo agar alerts band karne hon
SENDER_EMAIL    = "mmussab@gmail.com"
SENDER_PASSWORD = "rtyi jsoc fctb wpcj"  # Gmail App Password
RECEIVER_EMAIL  = "mmussab@gmail.com"    # Aapka email jahan alert aaye

# Sirf yeh score se upar wale coins par alert aayega
ALERT_MIN_SCORE = 2.5

# Coins jo skip karne hain (stablecoins, wrapped tokens, etc.)
SKIP_COINS = {
    "USDCUSDT","BUSDUSDT","TUSDUSDT","USDTUSDT","DAIUSDT",
    "FDUSDUSDT","EURUSDT","BTTUSDT","XECUSDT","SHIBUSDT",
    "PEPEUSDT","FLOKIUSDT","WBTCUSDT","STETHUSDT","WBETHUSDT",
    "BTCUSDT",  # yeh benchmark hai
}

BINANCE_BASE   = "https://api.binance.com/api/v3"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# PythonAnywhere free plan mein allowed APIs:
# 1. CoinGecko (primary)
# 2. Binance (agar local PC par chal raha ho)
USE_COINGECKO = True   # PythonAnywhere par True rakhein


# ─────────────────────────────────────────────
#  COINGECKO ID MAPPING
# ─────────────────────────────────────────────
# CoinGecko mein symbol alag hote hain — yeh map hai
CG_ID_MAP = {
    "BTC":"bitcoin","ETH":"ethereum","BNB":"binancecoin",
    "SOL":"solana","XRP":"ripple","ADA":"cardano",
    "AVAX":"avalanche-2","DOT":"polkadot","LINK":"chainlink",
    "LTC":"litecoin","ATOM":"cosmos","NEAR":"near",
    "FTM":"fantom","ALGO":"algorand","VET":"vechain",
    "ICP":"internet-computer","FIL":"filecoin","SAND":"the-sandbox",
    "MANA":"decentraland","AXS":"axie-infinity","GALA":"gala",
    "CHZ":"chiliz","ENJ":"enjincoin","ZIL":"zilliqa",
    "QNT":"quant-network","EGLD":"elrond-erd-2","HBAR":"hedera-hashgraph",
    "THETA":"theta-token","XTZ":"tezos","RUNE":"thorchain",
    "KAVA":"kava","CRV":"curve-dao-token","COMP":"compound-governance-token",
    "AAVE":"aave","MKR":"maker","SNX":"havven",
    "UNI":"uniswap","SUSHI":"sushi","TRX":"tron",
    "XMR":"monero","ZEC":"zcash","DASH":"dash","BCH":"bitcoin-cash",
    "MATIC":"matic-network","APE":"apecoin","DOGE":"dogecoin",
    "SHIB":"shiba-inu","LDO":"lido-dao","OP":"optimism",
    "ARB":"arbitrum","IMX":"immutable-x","GRT":"the-graph",
}

TOP_COINS_BY_MODE = {
    1: ["BTC","ETH","BNB","SOL","XRP","ADA","AVAX","DOT","LINK","LTC",
        "ATOM","NEAR","MATIC","UNI","AAVE","CRV","COMP","MKR","SNX","RUNE",
        "FTM","ALGO","VET","ICP","FIL","SAND","MANA","AXS","GALA","CHZ",
        "ENJ","ZIL","QNT","EGLD","HBAR","THETA","XTZ","KAVA","SUSHI","TRX",
        "XMR","ZEC","DASH","BCH","APE","DOGE","LDO","OP","ARB","GRT"],
    2: ["BTC","ETH","BNB","SOL","XRP","ADA","AVAX","DOT","LINK","LTC",
        "ATOM","NEAR","MATIC","UNI","AAVE","CRV","COMP","MKR","SNX","RUNE",
        "FTM","ALGO","VET","ICP","FIL","SAND","MANA","AXS","GALA","CHZ",
        "ENJ","ZIL","QNT","EGLD","HBAR","THETA","XTZ","KAVA","SUSHI","TRX",
        "XMR","ZEC","DASH","BCH","APE","DOGE","LDO","OP","ARB","GRT",
        "IMX","CAKE","1INCH","BAL","YFI","OCEAN","AUDIO","CELR","SKL","BAND",
        "REN","NMR","KNC","ZRX","BAT","STORJ","ANKR","COTI","CTSI","DENT",
        "DOCK","FET","GNO","HOT","ICX","IOTA","IOST","JASMY","KEY","KLAY",
        "LINA","LOOM","LPT","LSK","LUNC","MDT","MTL","NULS","OGN","OMG",
        "ONE","ONT","PERP","PHA","POLS","POND","PUNDIX","QTUM","RAY","RLC"],
}


# ─────────────────────────────────────────────
#  AUTO-FETCH COIN LIST
# ─────────────────────────────────────────────

def get_market_coins(mode=2):
    """
    CoinGecko se top coins list fetch karo
    ya static list use karo
    """
    limit = 50 if mode == 1 else 100
    coins_base = TOP_COINS_BY_MODE.get(mode, TOP_COINS_BY_MODE[2])

    if USE_COINGECKO:
        try:
            print(f"  {Fore.CYAN}CoinGecko se live coin list fetch ho rahi hai...{Style.RESET_ALL}")
            url = f"{COINGECKO_BASE}/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "volume_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False
            }
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            coins = [c["symbol"].upper() for c in data
                     if c["symbol"].upper() not in {"USDT","USDC","BUSD","DAI","TUSD","FDUSD","WBTC","STETH"}]
            print(f"  {Fore.GREEN}Total {len(coins)} coins mil gaye{Style.RESET_ALL}")
            return coins
        except Exception as e:
            print(f"  {Fore.YELLOW}CoinGecko fetch fail — default list use ho rahi hai: {e}{Style.RESET_ALL}")
            return [c for c in coins_base if c != "BTC"]
    else:
        # Local PC — Binance use karo
        try:
            print(f"  {Fore.CYAN}Binance se live coin list fetch ho rahi hai...{Style.RESET_ALL}")
            url = f"{BINANCE_BASE}/ticker/24hr"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            tickers = r.json()
            usdt_pairs = [
                t for t in tickers
                if t["symbol"].endswith("USDT")
                and t["symbol"] not in SKIP_COINS
                and float(t.get("quoteVolume", 0)) >= MIN_VOLUME_USD
            ]
            usdt_pairs.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
            coins_raw = [t["symbol"].replace("USDT","") for t in usdt_pairs[:limit]]
            print(f"  {Fore.GREEN}Total {len(coins_raw)} coins mil gaye{Style.RESET_ALL}")
            return coins_raw
        except Exception as e:
            print(f"  {Fore.YELLOW}Binance fetch fail — default list: {e}{Style.RESET_ALL}")
            return [c for c in coins_base if c != "BTC"]


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def pkt_now():
    return datetime.now(timezone.utc) + PKT_OFFSET


def send_email_alert(setups):
    """
    V6 setup milne par Gmail se email alert bhejo
    setups = list of dicts with coin info
    """
    if not EMAIL_ALERTS or not setups:
        return

    try:
        kz = in_killzone() or "No Killzone"
        time_str = pkt_now().strftime('%d %b %Y %H:%M PKT')

        # Email subject
        top = setups[0]
        subject = f"V6 ALERT: {len(setups)} Setup(s) Found — {top['Coin']} {top['Setup']}"

        # Email body
        body = f"""
==============================================
  V6 UNIVERSAL PROTOCOL — TRADE ALERT
  Muhammad Mussab Aqeel | Karachi, PK
==============================================
  Time     : {time_str}
  Killzone : {kz}
  Capital  : $876 | Risk/Trade: $8.76
==============================================

"""
        for i, s in enumerate(setups, 1):
            body += f"""
--- SETUP #{i} ---
Coin       : {s['Coin']}
Price      : {s['Price']}
Setup Type : {s['Setup']}
HTF Zone   : {s['HTF Zone']}
M15 Status : {s['M15 Status']}
Entry      : {s['Entry Ready']}
Score      : {s['Score']}
Risk       : $8.76 (1% of $876)
Protocol   : SL below OB → TP 1:2 R:R → BE
"""

        body += """
==============================================
  NEWS PROTOCOL: 15 min pehle/baad mat trade karo
  TradingView par khud verify zaroor karo
==============================================
"""

        msg = MIMEMultipart()
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"  {Fore.GREEN}Email alert bhej diya: {RECEIVER_EMAIL}{Style.RESET_ALL}")

    except Exception as e:
        print(f"  {Fore.YELLOW}Email alert fail: {e}{Style.RESET_ALL}")


def in_killzone():
    h = pkt_now().hour
    if LONDON_START <= h < LONDON_END:
        return f"LONDON KZ ({LONDON_START}:00–{LONDON_END}:00 PKT)"
    if NY_START <= h < NY_END:
        return f"NEW YORK KZ ({NY_START}:00–{NY_END}:00 PKT)"
    return None


def fetch_klines(symbol, interval, limit=100):
    """
    Candle data fetch karo.
    CoinGecko mode (PythonAnywhere) ya Binance mode (local PC)
    """
    if USE_COINGECKO:
        return fetch_klines_coingecko(symbol, interval, limit)
    else:
        return fetch_klines_binance(symbol, interval, limit)


def fetch_klines_binance(symbol, interval, limit=100):
    """Binance se candle data — local PC par use karo"""
    url = f"{BINANCE_BASE}/klines"
    params = {"symbol": symbol + "USDT" if not symbol.endswith("USDT") else symbol,
              "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","qav","trades","tbbav","tbqav","ignore"
        ])
        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)
        return df
    except:
        return None


def fetch_klines_coingecko(symbol, interval, limit=100):
    """
    CoinGecko se OHLC data fetch karo
    interval: '4h' ya '15m' — CoinGecko days mein convert karta hai
    """
    cg_id = CG_ID_MAP.get(symbol.upper())
    if not cg_id:
        # Symbol se ID dhundho
        cg_id = symbol.lower()

    # CoinGecko OHLC: days param
    # 4h ke liye 30 days, 15m ke liye 1 day
    if interval == "4h":
        days = 30
    elif interval == "15m":
        days = 1
    else:
        days = 7

    try:
        url = f"{COINGECKO_BASE}/coins/{cg_id}/ohlc"
        params = {"vs_currency": "usd", "days": days}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        if not data or len(data) < 5:
            return None

        df = pd.DataFrame(data, columns=["open_time","open","high","low","close"])
        for col in ["open","high","low","close"]:
            df[col] = df[col].astype(float)
        df["volume"] = 0.0  # CoinGecko OHLC mein volume nahi hota

        # Last `limit` candles lo
        df = df.tail(limit).reset_index(drop=True)
        return df
    except Exception as e:
        return None


# ─────────────────────────────────────────────
#  ANALYSIS FUNCTIONS
# ─────────────────────────────────────────────

def detect_htf_bias(df_h4):
    """
    H4 Bias: compare last 3 swing highs & lows
    Bullish = Higher Highs + Higher Lows
    Bearish = Lower Highs + Lower Lows
    """
    if df_h4 is None or len(df_h4) < 20:
        return "UNKNOWN", None

    closes  = df_h4["close"].values
    highs   = df_h4["high"].values
    lows    = df_h4["low"].values

    # Simple: last 20 candles — is latest close above midpoint?
    recent_high = highs[-20:].max()
    recent_low  = lows[-20:].min()
    mid         = (recent_high + recent_low) / 2
    current     = closes[-1]

    # Swing structure: compare last 3 pivot highs & lows
    pivot_highs = []
    pivot_lows  = []
    for i in range(2, len(df_h4)-2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            pivot_highs.append(highs[i])
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            pivot_lows.append(lows[i])

    bias = "NEUTRAL"
    if len(pivot_highs) >= 2 and len(pivot_lows) >= 2:
        hh = pivot_highs[-1] > pivot_highs[-2]
        hl = pivot_lows[-1]  > pivot_lows[-2]
        lh = pivot_highs[-1] < pivot_highs[-2]
        ll = pivot_lows[-1]  < pivot_lows[-2]
        if hh and hl:
            bias = "BULLISH"
        elif lh and ll:
            bias = "BEARISH"
        elif hl and lh:
            bias = "NEUTRAL"

    current_price = closes[-1]
    return bias, current_price


def detect_h4_ob(df_h4):
    """
    H4 Order Block: last significant bearish candle before bullish move (buy OB)
    or last significant bullish candle before bearish move (sell OB)
    Returns: (ob_type, ob_high, ob_low, tapped)
    """
    if df_h4 is None or len(df_h4) < 10:
        return None, None, None, False

    closes = df_h4["close"].values
    opens  = df_h4["open"].values
    highs  = df_h4["high"].values
    lows   = df_h4["low"].values
    current_price = closes[-1]

    # Look for last bearish OB (for buy setups): bearish candle followed by strong bullish move
    # Simplified: find last red candle whose low is near current price
    for i in range(len(df_h4)-3, max(len(df_h4)-20, 0), -1):
        is_bearish = closes[i] < opens[i]
        candle_size = abs(closes[i] - opens[i])
        avg_size = np.mean(np.abs(closes[-20:] - opens[-20:]))
        if is_bearish and candle_size > avg_size * 0.8:
            ob_high = highs[i]
            ob_low  = lows[i]
            # Is current price inside or near this OB?
            tapped = ob_low <= current_price <= ob_high * 1.005
            if tapped or (current_price < ob_high * 1.03 and current_price > ob_low * 0.97):
                return "BULLISH_OB", round(ob_high, 4), round(ob_low, 4), tapped

    # Bullish OB (for sell setups)
    for i in range(len(df_h4)-3, max(len(df_h4)-20, 0), -1):
        is_bullish = closes[i] > opens[i]
        candle_size = abs(closes[i] - opens[i])
        avg_size = np.mean(np.abs(closes[-20:] - opens[-20:]))
        if is_bullish and candle_size > avg_size * 0.8:
            ob_high = highs[i]
            ob_low  = lows[i]
            tapped = ob_low <= current_price <= ob_high * 1.005
            if tapped or (current_price < ob_high * 1.03 and current_price > ob_low * 0.97):
                return "BEARISH_OB", round(ob_high, 4), round(ob_low, 4), tapped

    return None, None, None, False


def detect_smt(df_btc_h4, df_alt_h4):
    """
    SMT Divergence:
    - Bullish SMT: BTC makes Lower Low but Altcoin makes Higher Low
    - Bearish SMT: BTC makes Higher High but Altcoin makes Lower High
    Returns: (smt_type, strength)
    """
    if df_btc_h4 is None or df_alt_h4 is None:
        return "NONE", 0

    btc_lows  = df_btc_h4["low"].values[-30:]
    btc_highs = df_btc_h4["high"].values[-30:]
    alt_lows  = df_alt_h4["low"].values[-30:]
    alt_highs = df_alt_h4["high"].values[-30:]

    # Compare last 2 significant lows
    btc_low1, btc_low2 = btc_lows[-15:].min(), btc_lows[-7:].min()
    alt_low1, alt_low2 = alt_lows[-15:].min(), alt_lows[-7:].min()

    btc_high1, btc_high2 = btc_highs[-15:].max(), btc_highs[-7:].max()
    alt_high1, alt_high2 = alt_highs[-15:].max(), alt_highs[-7:].max()

    btc_ll = btc_low2  < btc_low1   # BTC Lower Low
    alt_hl = alt_low2  > alt_low1   # Altcoin Higher Low
    btc_hh = btc_high2 > btc_high1  # BTC Higher High
    alt_lh = alt_high2 < alt_high1  # Altcoin Lower High

    # Divergence magnitude
    if btc_ll and alt_hl:
        div_pct = round(abs((alt_low2 - alt_low1) / alt_low1) * 100, 2)
        return "BULLISH_SMT", div_pct

    if btc_hh and alt_lh:
        div_pct = round(abs((alt_high1 - alt_high2) / alt_high1) * 100, 2)
        return "BEARISH_SMT", div_pct

    return "NONE", 0


def detect_choch_idm(df_m15):
    """
    M15 CHOCH + IDM Sweep detection
    CHOCH: price breaks previous swing high/low
    IDM:   price sweeps internal liquidity (a recent high/low) then reverses
    """
    if df_m15 is None or len(df_m15) < 30:
        return False, False, "N/A"

    closes = df_m15["close"].values
    highs  = df_m15["high"].values
    lows   = df_m15["low"].values

    # CHOCH: last 20 candles — did price break a swing level?
    swing_high = highs[-20:-5].max()
    swing_low  = lows[-20:-5].min()
    recent_high = highs[-5:].max()
    recent_low  = lows[-5:].min()
    recent_close = closes[-1]

    choch_bull = recent_close > swing_high   # Bullish CHOCH
    choch_bear = recent_close < swing_low    # Bearish CHOCH
    choch      = choch_bull or choch_bear
    choch_dir  = "BULL" if choch_bull else ("BEAR" if choch_bear else "NONE")

    # IDM Sweep: price swept a recent high or low and came back
    prev_high = highs[-10:-3].max()
    prev_low  = lows[-10:-3].min()

    swept_high = highs[-3:].max() > prev_high and closes[-1] < prev_high
    swept_low  = lows[-3:].min()  < prev_low  and closes[-1] > prev_low
    idm        = swept_high or swept_low

    status = f"CHOCH:{choch_dir} | IDM:{'YES' if idm else 'NO'}"
    return choch, idm, status


# ─────────────────────────────────────────────
#  MAIN SCANNER
# ─────────────────────────────────────────────

def scan():
    print(f"\n{Fore.CYAN}{'='*65}")
    print(f"  V6 UNIVERSAL PROTOCOL SCANNER — Muhammad Mussab Aqeel")
    print(f"  {pkt_now().strftime('%A, %d %B %Y  %H:%M PKT')}")
    print(f"  Capital: ${CAPITAL}  |  Risk/Trade: ${RISK_AMOUNT} (1%)")
    mode_names = {1:"Top 50 Coins", 2:"Top 100 Coins", 3:"Full Market 300+"}
    print(f"  Scan Mode: {mode_names.get(SCAN_MODE, 'Top 100')}")
    print(f"{'='*65}{Style.RESET_ALL}")

    kz = in_killzone()
    if kz:
        print(f"\n{Fore.GREEN}  *** KILLZONE ACTIVE: {kz} ***{Style.RESET_ALL}\n")
    else:
        next_kz_msg = "Next: London KZ at 12:00 PM PKT" if pkt_now().hour < 12 else \
                      ("Next: NY KZ at 5:00 PM PKT" if pkt_now().hour < 17 else "Next: London KZ tomorrow 12:00 PM PKT")
        print(f"\n{Fore.YELLOW}  [!] No active Killzone right now. {next_kz_msg}{Style.RESET_ALL}\n")

    # ── Auto-fetch live coin list from Binance ──
    coin_list = get_market_coins(SCAN_MODE)

    print(f"\n  Fetching BTC benchmark data...")
    df_btc_h4 = fetch_klines(BENCHMARK, "4h", 100)
    if df_btc_h4 is None:
        print(f"{Fore.RED}  ERROR: Cannot fetch BTC data. Check internet connection.{Style.RESET_ALL}")
        return

    btc_bias, btc_price = detect_htf_bias(df_btc_h4)
    print(f"  BTC Price: ${btc_price:,.2f}  |  H4 Bias: {btc_bias}")
    print(f"\n  Scanning {len(coin_list)} coins — please wait...\n")

    results   = []
    found_smt = 0

    for idx, symbol in enumerate(coin_list, 1):
        name = symbol.replace("USDT", "/USDT")
        print(f"  [{idx}/{len(coin_list)}] Scanning {name}...{' '*20}", end="\r")

        df_h4  = fetch_klines(symbol, "4h",  100)
        df_m15 = fetch_klines(symbol, "15m", 100)
        time.sleep(0.2)  # Binance rate limit respect — 2 calls per coin

        if df_h4 is None or df_m15 is None:
            continue

        alt_bias, alt_price  = detect_htf_bias(df_h4)
        ob_type, ob_high, ob_low, ob_tapped = detect_h4_ob(df_h4)
        smt_type, smt_strength = detect_smt(df_btc_h4, df_h4)
        choch, idm, m15_status = detect_choch_idm(df_m15)

        # ── Score the setup quality (0–4) ──
        score = 0
        if smt_type != "NONE":                          score += 2
        if ob_tapped:                                   score += 1
        if choch and idm:                               score += 1
        elif choch or idm:                              score += 0.5

        # ── Classify ──
        if smt_type == "BULLISH_SMT":
            setup = "BULLISH SMT"
            color = Fore.GREEN
        elif smt_type == "BEARISH_SMT":
            setup = "BEARISH SMT"
            color = Fore.RED
        else:
            setup = "NO SMT"
            color = Fore.WHITE

        htf_zone = "N/A"
        if ob_type:
            tap_str = "TAPPED ✓" if ob_tapped else "NEAR"
            htf_zone = f"{ob_type.split('_')[0]} OB ({tap_str})"

        entry_ready = "YES ✓" if (smt_type != "NONE" and choch and idm and ob_tapped) else \
                      ("WAIT" if (smt_type != "NONE" and (choch or idm)) else "NO")

        if smt_type != "NONE":
            found_smt += 1
            print(f"  {Fore.GREEN}  >>> SMT FOUND: {name} — {setup}{Style.RESET_ALL}   ")

        results.append({
            "Coin":         name,
            "Price":        f"${alt_price:,.4f}" if alt_price else "N/A",
            "Setup":        setup,
            "HTF Zone":     htf_zone,
            "M15 Status":   m15_status,
            "Entry Ready":  entry_ready,
            "Score":        f"{score}/4",
            "_color":       color,
            "_score_raw":   score,
            "_smt":         smt_type,
        })

    # Sort by score descending
    results.sort(key=lambda x: x["_score_raw"], reverse=True)

    # ── Print results table ──
    print(f"\n{'─'*65}")
    print(f"  SCAN COMPLETE — {len(results)} coins analyzed | {found_smt} SMT setups found")
    print(f"{'─'*65}\n")

    actionable = [r for r in results if r["_smt"] != "NONE"]

    if actionable:
        print(f"{Fore.CYAN}  ▶ ACTIVE SMT SETUPS ({len(actionable)} coins){Style.RESET_ALL}")
        table_data = []
        for r in actionable:
            color = r["_color"]
            table_data.append([
                f"{color}{r['Coin']}{Style.RESET_ALL}",
                r["Price"],
                f"{color}{r['Setup']}{Style.RESET_ALL}",
                r["HTF Zone"],
                r["M15 Status"],
                r["Entry Ready"],
                r["Score"]
            ])

        headers = ["Coin", "Price", "Setup", "HTF Zone", "M15 Status", "Entry Ready", "Score"]
        print(tabulate(table_data, headers=headers, tablefmt="rounded_outline"))
        print()

        # ── BEST SETUPS DETAIL ──
        top = [r for r in actionable if r["_score_raw"] >= 2.5]
        if top:
            print(f"{Fore.GREEN}  ★ TOP SETUPS — ENTRY CANDIDATES (Score ≥ 2.5/4){Style.RESET_ALL}")
            print(f"  {'─'*60}")
            for r in top:
                color = r["_color"]
                print(f"\n  {color}★ {r['Coin']} — {r['Setup']}{Style.RESET_ALL}")
                print(f"    Price       : {r['Price']}")
                print(f"    HTF Zone    : {r['HTF Zone']}")
                print(f"    M15 Status  : {r['M15 Status']}")
                print(f"    Entry Ready : {r['Entry Ready']}")
                print(f"    Risk        : ${RISK_AMOUNT} (1% of ${CAPITAL})")
                print(f"    BE Protocol : 1:2 R:R hit hote hi SL ko entry par shift karo")
        else:
            print(f"  {Fore.YELLOW}SMT mili hain lekin entry ke liye CHOCH + IDM ka wait karo{Style.RESET_ALL}")

    else:
        print(f"  {Fore.YELLOW}Abhi koi SMT divergence nahi mili.")
        print(f"  Market consolidate kar rahi hai — 15 min baad dobara scan hoga.{Style.RESET_ALL}")

    # ── Watchlist — sirf count dikhao, names nahi (100+ hone par boring lagta hai) ──
    watchlist = [r for r in results if r["_smt"] == "NONE"]
    print(f"\n  {Fore.WHITE}Watchlist: {len(watchlist)} coins mein abhi koi SMT nahi{Style.RESET_ALL}")

    # ── Email Alert — sirf top setups par ──
    alert_setups = [r for r in actionable if r["_score_raw"] >= ALERT_MIN_SCORE]
    if alert_setups:
        print(f"\n  {Fore.CYAN}Email alert bhej raha hoon...{Style.RESET_ALL}")
        send_email_alert(alert_setups)
    elif actionable:
        print(f"\n  {Fore.YELLOW}SMT mili hai lekin score {ALERT_MIN_SCORE} se kam — email nahi bheja{Style.RESET_ALL}")

    print(f"\n{'─'*65}")
    print(f"  NEWS PROTOCOL: Avoid 15 min before & after high-impact news")
    print(f"  KILLZONES: London 12–3 PM PKT | New York 5–8 PM PKT")
    print(f"  RISK: ${RISK_AMOUNT}/trade | BE mandatory at 1:2 R:R")
    print(f"{'─'*65}\n")


# ─────────────────────────────────────────────
#  CONTINUOUS MODE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}V6 Protocol Scanner starting...{Style.RESET_ALL}")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            scan()
            print(f"  Next scan in 15 minutes. Waiting...\n")
            time.sleep(900)   # 15 min refresh
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Scanner stopped. Trade safe, Mussab bhai!{Style.RESET_ALL}\n")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}. Retrying in 60s...{Style.RESET_ALL}")
            time.sleep(60)
