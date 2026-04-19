import math
import os
import time
import random

import requests
import json
import streamlit as st

import yfinance as yf

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

try:
    from google import genai
    GENAI_AVAILABLE = True
    
    # APIキーの取得優先順位: 1. Streamlit Secrets, 2. 環境変数, 3. ローカルのAPI.txt
    api_key = None
    
    # Streamlit Secrets (Cloud環境・ローカルの .streamlit/secrets.toml)
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    # 環境変数
    if not api_key and os.environ.get("GEMINI_API_KEY"):
        api_key = os.environ["GEMINI_API_KEY"]
        
    # ローカルファイル
    if not api_key:
        try:
            with open("API.txt", "r") as f:
                api_key = f.read().strip()
        except Exception:
            pass
            
    # APIクライアントの設定
    if api_key:
        AI_CLIENT = genai.Client(api_key=api_key)
    else:
        GENAI_AVAILABLE = False
        print("Gemini API Key not found. AI features will be disabled.")
        
except ImportError:
    GENAI_AVAILABLE = False

# ─────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="US Stock Dashboard",
    page_icon="📈",
    layout="wide",
)

# ─────────────────────────────────────────────
# カスタムCSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* 背景 & フォント */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* タイトル */
    h1 {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 2.4rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* サブタイトル */
    .subtitle {
        text-align: center;
        color: #9ca3af;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* metric カード */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 18px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0, 210, 255, 0.15);
    }
    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-size: 0.82rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }

    /* 入力テキスト */
    input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        padding: 12px 16px !important;
    }
    input:focus {
        border-color: #00d2ff !important;
        box-shadow: 0 0 0 2px rgba(0, 210, 255, 0.25) !important;
    }

    /* ディバイダー */
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }

    /* 銘柄名ヘッダー */
    .company-name {
        text-align: center;
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 1rem;
        margin-bottom: 0.3rem;
    }
    .company-sector {
        text-align: center;
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
    }

    /* フッター */
    .footer {
        text-align: center;
        color: #4b5563;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding-bottom: 1rem;
    }

    /* タブ */
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        color: #9ca3af !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #00d2ff !important;
        border-bottom-color: #00d2ff !important;
    }

    /* セクションタイトル */
    .section-title {
        color: #cbd5e1;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        padding-left: 4px;
        border-left: 3px solid #00d2ff;
        padding-left: 12px;
    }

    /* AI レポートカード */
    .ai-report {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px 32px;
        line-height: 1.85;
        color: #d1d5db;
        font-size: 0.95rem;
    }
    .ai-report h3, .ai-report h4 {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        background: none !important;
    }
    .ai-report strong {
        color: #93c5fd;
    }
    .ai-report ul {
        padding-left: 1.2rem;
    }
    .ai-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        margin-bottom: 12px;
        letter-spacing: 0.04em;
    }
    .ai-report strong {
        color: #00d2ff;
    }

    /* 成長ドライバ・カード */
    .growth-card {
        display: flex;
        align-items: center;
        border-radius: 12px;
        padding: 14px 22px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        backdrop-filter: blur(8px);
    }
    .growth-card-num {
        font-size: 1.6rem;
        font-weight: 800;
        margin-right: 22px;
        min-width: 45px;
        text-align: center;
        opacity: 0.9;
    }
    .growth-card-content {
        flex-grow: 1;
    }
    .growth-card-theme {
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 3px;
        color: #f8fafc;
    }
    .growth-card-impact {
        font-size: 0.92rem;
        color: rgba(255, 255, 255, 0.85);
        line-height: 1.4;
    }
    .status-positive {
        background: rgba(6, 78, 59, 0.4);
        border: 1px solid rgba(16, 185, 129, 0.5);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
    }
    .status-positive .growth-card-num { color: #10b981; }
    .status-neutral {
        background: rgba(69, 26, 3, 0.4);
        border: 1px solid rgba(245, 158, 11, 0.5);
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.1);
    }
    .status-neutral .growth-card-num { color: #f59e0b; }
    .status-critical {
        background: rgba(80, 7, 36, 0.4);
        border: 1px solid rgba(236, 72, 153, 0.5);
        box-shadow: 0 4px 15px rgba(236, 72, 153, 0.1);
    }
    .status-critical .growth-card-num { color: #ec4899; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# セッションステート初期化
# ─────────────────────────────────────────────
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "個別銘柄分析"
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = ""
if "theme_search_query" not in st.session_state:
    st.session_state.theme_search_query = ""

# ─────────────────────────────────────────────
# サイドバー・ナビゲーション
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("Momentum Master")
    st.radio(
        "モード選択",
        ["個別銘柄分析", "テーマ・エクスプローラー", "セクター・アナライザー"],
        key="app_mode"
    )
    st.divider()
    st.caption("AI-Powered Institutional Grade Analytics")
    
    if st.session_state.app_mode == "テーマ・エクスプローラー":
        st.info("💡 成長テーマやキーワード（例：AI, 核融合, 減量薬）から銘柄を検索できます。")

# ─────────────────────────────────────────────
# カスタムCSS (追加)
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* 検索結果カード */
    .theme-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
    }
    .theme-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: #00d2ff;
        transform: translateY(-2px);
    }
    .theme-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .theme-ticker {
        font-size: 1.5rem;
        font-weight: 800;
        color: #00d2ff;
    }
    .theme-name {
        font-size: 0.95rem;
        color: #94a3b8;
        font-weight: 600;
    }
    .theme-match {
        font-size: 0.9rem;
        color: #e2e8f0;
        line-height: 1.6;
        background: rgba(0, 210, 255, 0.1);
        padding: 10px 14px;
        border-radius: 8px;
        margin-top: 10px;
        border-left: 3px solid #00d2ff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# Plotly 共通テーマ
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#c9d1d9"),
    margin=dict(l=50, r=30, t=50, b=50),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.06)",
        linecolor="rgba(255,255,255,0.1)",
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.06)",
        linecolor="rgba(255,255,255,0.1)",
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    ),
    hoverlabel=dict(
        bgcolor="#1e293b",
        font_size=13,
        font_family="Inter, sans-serif",
    ),
)

# ─────────────────────────────────────────────
# ヘルパー関数
# ─────────────────────────────────────────────

def fmt_number(value, prefix="", suffix="", decimals=2):
    """数値をフォーマットする。None / N/A の場合は '—' を返す。"""
    if value is None or value == "N/A":
        return "—"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "—"

    if abs(v) >= 1_000_000_000_000:
        return f"{prefix}{v / 1_000_000_000_000:.{decimals}f}T{suffix}"
    if abs(v) >= 1_000_000_000:
        return f"{prefix}{v / 1_000_000_000:.{decimals}f}B{suffix}"
    if abs(v) >= 1_000_000:
        return f"{prefix}{v / 1_000_000:.{decimals}f}M{suffix}"
    return f"{prefix}{v:,.{decimals}f}{suffix}"


def fmt_percent(value):
    """パーセント表記にフォーマットする。"""
    if value is None or value == "N/A":
        return "—"
    try:
        return f"{float(value) * 100:.2f}%"
    except (ValueError, TypeError):
        return "—"


def fmt_ratio(value):
    """倍率をフォーマットする。"""
    if value is None or value == "N/A":
        return "—"
    try:
        return f"{float(value):.2f}x"
    except (ValueError, TypeError):
        return "—"


def to_millions(series: pd.Series) -> pd.Series:
    """pandas Series を百万ドル単位に変換する。NaN は 0 に置換。"""
    return (series / 1_000_000).fillna(0).round(1)


@st.cache_data(ttl=86400)
def translate_to_japanese(text: str) -> str:
    """AIを使わず、Google Translate の無料API経由で日本語に翻訳する。"""
    if not text:
        return ""
        
    try:
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ja&dt=t&q={encoded_text}"
        response = requests.get(url, timeout=10)
        data = response.json()
        translated = "".join([d[0] for d in data[0] if d[0]])
        return translated
    except Exception as e:
        print(f"Translation Error: {e}")
        return text # 失敗時は原文を返す


# セクターETFマッピング
SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}

# セクター日本語名マッピング
SECTOR_JA_MAP = {
    "Technology": "情報技術",
    "Financial Services": "金融",
    "Healthcare": "ヘルスケア",
    "Consumer Cyclical": "一般消費財",
    "Consumer Defensive": "生活必需品",
    "Energy": "エネルギー",
    "Industrials": "資本財",
    "Basic Materials": "素材",
    "Real Estate": "不動産",
    "Utilities": "公共事業",
    "Communication Services": "通信サービス",
}

# 業界日本語名マッピング（yfinance で返される主要な業界名）
INDUSTRY_JA_MAP = {
    # Technology
    "Semiconductors": "半導体",
    "Semiconductor Equipment & Materials": "半導体製造装置・材料",
    "Software - Application": "アプリケーションソフトウェア",
    "Software - Infrastructure": "インフラソフトウェア",
    "Information Technology Services": "ITサービス",
    "Consumer Electronics": "家電",
    "Electronic Components": "電子部品",
    "Scientific & Technical Instruments": "科学・技術機器",
    "Computer Hardware": "コンピュータハードウェア",
    "Communication Equipment": "通信機器",
    "Solar": "太陽光発電",
    # Financial Services
    "Banks - Diversified": "総合銀行",
    "Banks - Regional": "地方銀行",
    "Capital Markets": "資本市場",
    "Insurance - Diversified": "総合保険",
    "Insurance - Life": "生命保険",
    "Insurance - Property & Casualty": "損害保険",
    "Insurance Brokers": "保険仲介",
    "Asset Management": "資産運用",
    "Financial Data & Stock Exchanges": "金融データ・証券取引所",
    "Credit Services": "クレジットサービス",
    "Insurance - Reinsurance": "再保険",
    "Insurance - Specialty": "専門保険",
    "Mortgage Finance": "住宅ローン",
    "Financial Conglomerates": "金融コングロマリット",
    "Shell Companies": "シェルカンパニー",
    # Healthcare
    "Drug Manufacturers - General": "医薬品（大手）",
    "Drug Manufacturers - Specialty & Generic": "医薬品（専門・ジェネリック）",
    "Biotechnology": "バイオテクノロジー",
    "Medical Devices": "医療機器",
    "Medical Instruments & Supplies": "医療器具・用品",
    "Diagnostics & Research": "診断・研究",
    "Health Information Services": "医療情報サービス",
    "Healthcare Plans": "医療保険プラン",
    "Medical Care Facilities": "医療施設",
    "Pharmaceutical Retailers": "調剤薬局",
    "Medical Distribution": "医療流通",
    # Consumer Cyclical
    "Internet Retail": "ネット通販",
    "Auto Manufacturers": "自動車メーカー",
    "Auto Parts": "自動車部品",
    "Restaurants": "レストラン",
    "Apparel Retail": "衣料品小売",
    "Home Improvement Retail": "ホームセンター",
    "Travel Services": "旅行サービス",
    "Specialty Retail": "専門小売",
    "Residential Construction": "住宅建設",
    "Footwear & Accessories": "靴・アクセサリー",
    "Apparel Manufacturing": "衣料品製造",
    "Packaging & Containers": "包装・容器",
    "Furnishings, Fixtures & Appliances": "家具・設備・家電",
    "Leisure": "レジャー",
    "Gambling": "ギャンブル",
    "Resorts & Casinos": "リゾート・カジノ",
    "Luxury Goods": "高級品",
    "Department Stores": "百貨店",
    "Textile Manufacturing": "繊維製造",
    # Consumer Defensive
    "Beverages - Non-Alcoholic": "清涼飲料",
    "Beverages - Alcoholic": "酒類",
    "Beverages - Wineries & Distilleries": "ワイナリー・蒸留所",
    "Household & Personal Products": "家庭用品・パーソナルケア",
    "Packaged Foods": "加工食品",
    "Tobacco": "たばこ",
    "Discount Stores": "ディスカウントストア",
    "Grocery Stores": "食料品店",
    "Farm Products": "農産物",
    "Food Distribution": "食品流通",
    "Confectioners": "菓子メーカー",
    "Education & Training Services": "教育・研修サービス",
    # Energy
    "Oil & Gas Integrated": "石油・ガス（総合）",
    "Oil & Gas E&P": "石油・ガス（探査・生産）",
    "Oil & Gas Midstream": "石油・ガス（中流）",
    "Oil & Gas Equipment & Services": "石油・ガス設備・サービス",
    "Oil & Gas Refining & Marketing": "石油精製・販売",
    "Oil & Gas Drilling": "石油・ガス掘削",
    "Uranium": "ウラン",
    "Thermal Coal": "一般炭",
    # Industrials
    "Aerospace & Defense": "航空宇宙・防衛",
    "Railroads": "鉄道",
    "Farm & Heavy Construction Machinery": "農業・建設機械",
    "Building Products & Equipment": "建材・設備",
    "Specialty Industrial Machinery": "専門産業機械",
    "Waste Management": "廃棄物処理",
    "Conglomerates": "コングロマリット",
    "Industrial Distribution": "産業流通",
    "Consulting Services": "コンサルティング",
    "Staffing & Employment Services": "人材サービス",
    "Engineering & Construction": "エンジニアリング・建設",
    "Trucking": "トラック輸送",
    "Integrated Freight & Logistics": "総合物流",
    "Airlines": "航空会社",
    "Rental & Leasing Services": "レンタル・リース",
    "Security & Protection Services": "警備・セキュリティ",
    "Metal Fabrication": "金属加工",
    "Pollution & Treatment Controls": "環境・汚染処理",
    "Electrical Equipment & Parts": "電気機器・部品",
    "Marine Shipping": "海運",
    "Airports & Air Services": "空港・航空サービス",
    "Tools & Accessories": "工具・付属品",
    "Infrastructure Operations": "インフラ運営",
    "Business Equipment & Supplies": "事務用品・機器",
    # Basic Materials
    "Gold": "金",
    "Copper": "銅",
    "Steel": "鉄鋼",
    "Aluminum": "アルミニウム",
    "Specialty Chemicals": "特殊化学品",
    "Agricultural Inputs": "農業資材",
    "Building Materials": "建材",
    "Lumber & Wood Production": "木材",
    "Paper & Paper Products": "紙・紙製品",
    "Chemicals": "化学",
    "Other Industrial Metals & Mining": "その他産業用金属・鉱業",
    "Silver": "銀",
    "Coking Coal": "原料炭",
    "Other Precious Metals & Mining": "その他貴金属・鉱業",
    # Real Estate
    "REIT - Diversified": "REIT（総合）",
    "REIT - Industrial": "REIT（産業施設）",
    "REIT - Retail": "REIT（商業施設）",
    "REIT - Residential": "REIT（住宅）",
    "REIT - Office": "REIT（オフィス）",
    "REIT - Healthcare Facilities": "REIT（医療施設）",
    "REIT - Specialty": "REIT（専門）",
    "REIT - Hotel & Motel": "REIT（ホテル）",
    "REIT - Mortgage": "REIT（住宅ローン）",
    "Real Estate - Development": "不動産開発",
    "Real Estate - Diversified": "不動産（総合）",
    "Real Estate Services": "不動産サービス",
    # Utilities
    "Utilities - Regulated Electric": "電力（規制）",
    "Utilities - Regulated Gas": "ガス（規制）",
    "Utilities - Diversified": "公共事業（総合）",
    "Utilities - Renewable": "再生可能エネルギー",
    "Utilities - Independent Power Producers": "独立系発電事業者",
    "Utilities - Regulated Water": "水道（規制）",
    # Communication Services
    "Internet Content & Information": "インターネットコンテンツ・情報",
    "Telecom Services": "通信サービス",
    "Entertainment": "エンターテインメント",
    "Electronic Gaming & Multimedia": "ゲーム・マルチメディア",
    "Advertising Agencies": "広告代理店",
    "Broadcasting": "放送",
    "Publishing": "出版",
    # その他
    "Auto & Truck Dealerships": "自動車ディーラー",
    "Diversified Industrials": "総合産業",
    "Data Storage": "データストレージ",
    "Pay TV": "有料テレビ",
}


@st.cache_data(ttl=3600)
def fetch_market_context(ticker: str, sector: str):
    """当該銘柄、セクターETF、SPYの相対パフォーマンスデータを取得する（個別に取得して安定化）。"""
    try:
        # ETFの特定
        sector_etf = SECTOR_ETF_MAP.get(sector, "SPY")
        tickers_to_fetch = [ticker, sector_etf, "SPY"]
        
        # 個別に取得して結合
        all_hist = {}
        for t in tickers_to_fetch:
            try:
                hist = yf.Ticker(t).history(period="1y", interval="1d")
                if not hist.empty:
                    # 終値だけ抽出して保存
                    all_hist[t] = hist["Close"]
            except Exception as e:
                print(f"Error fetching {t}: {e}")
        
        if not all_hist:
            return None
            
        # DataFrameに結合
        data = pd.DataFrame(all_hist)
        
        # 欠損値は前日値で埋める
        data = data.ffill().dropna()
        
        if data.empty:
            return None
            
        # 100ベースで正規化（相対パフォーマンス）
        normalized = (data / data.iloc[0]) * 100
        
        # セクターの騰落率（存在する銘柄のみ計算）
        mom_1m = None
        mom_3m = None
        if sector_etf in data.columns:
            etf_prices = data[sector_etf]
            if len(etf_prices) > 63:
                mom_3m = (etf_prices.iloc[-1] / etf_prices.iloc[-63] - 1) * 100
            if len(etf_prices) > 21:
                mom_1m = (etf_prices.iloc[-1] / etf_prices.iloc[-21] - 1) * 100

        return {
            "normalized_df": normalized,
            "sector_etf": sector_etf,
            "sector_mom_1m": mom_1m,
            "sector_mom_3m": mom_3m,
            "tickers": list(data.columns)
        }
    except Exception as e:
        print(f"Context Fetch Error: {e}")
        return None


def render_52week_range(current, low, high):
    """52週安値・高値圏での現在地を可視化するバーを表示する。"""
    if not current or not low or not high:
        st.info("52週レンジデータがありません。")
        return

    # 計算
    dist_from_low = (current - low) / low * 100
    dist_to_high = (current - high) / high * 100  # 通常はマイナス
    
    # 進行度 (0.0 - 1.0)
    progress = (current - low) / (high - low)
    progress = max(0, min(1, progress))

    st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #94a3b8; margin-bottom: 4px;">
            <span>52週安値: ${low:,.2f}</span>
            <span>52週高値: ${high:,.2f}</span>
        </div>
        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; position: relative;">
            <div style="width: {progress*100}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #06b6d4); border-radius: 4px;"></div>
            <div style="position: absolute; left: calc({progress*100}% - 4px); top: -2px; width: 12px; height: 12px; background: #ffffff; border-radius: 50%; border: 2px solid #06b6d4; box-shadow: 0 0 8px rgba(6, 182, 212, 0.5);"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85em; margin-top: 8px;">
            <span style="color: #34d399;">安値から <b>+{dist_from_low:.1f}%</b></span>
            <span style="color: #f87171;">高値から <b>{dist_to_high:.1f}%</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=86400)
def translate_only(text: str) -> str:
    """テキストを要約せず、日本語に翻訳する。"""
    if not GENAI_AVAILABLE or not text:
        return text or "データがありません。"

    try:
        response = AI_CLIENT.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"""
            以下の文章（英語）を、意味を損なわないように自然な日本語に翻訳してください。
            要約はせず、元の内容をすべて含めてください。
            日本語のみで出力してください。

            文章:
            {text}
            """
        )
        return response.text
    except Exception as e:
        return f"翻訳に失敗しました: {str(e)}"


@st.cache_data(ttl=86400)
def generate_ai_swot(data: dict) -> dict:
    """財務データとビジネス概要からAIによるSWOT分析を生成する。"""
    if not GENAI_AVAILABLE:
        return None

    try:
        # 財務指标の成型
        metrics_summary = f"""
        - 売上成長率: {fmt_percent(data.get('revenue_growth'))}
        - 純利益率: {fmt_percent(data.get('profit_margins'))}
        - 営業利益率: {fmt_percent(data.get('operating_margins'))}
        - 負債比率 (D/E): {data.get('debt_to_equity', '—')}
        - ROE: {fmt_percent(data.get('roe'))}
        - 株価位置: 52週高値から {((data['price']/data['fifty_two_week_high'] - 1)*100):.1f}%
        """
        
        prompt = f"""
        あなたはシニア投資コンサルタントです。以下のデータに基づき、企業の「動的SWOT分析」を行ってください。
        
        【企業名】: {data['name']}
        【事業概要】: {data.get('long_summary', 'データなし')}
        【主な財務指標】:
        {metrics_summary}

        各項目について、専門的かつ簡潔な日本語の弾丸ポイント（各2-3個）で回答してください。
        JSON形式で以下のキーを持つように出力してください:
        {{
            "strengths": ["...", "..."],
            "weaknesses": ["...", "..."],
            "opportunities": ["...", "..."],
            "threats": ["...", "..."]
        }}
        """
        
        response = AI_CLIENT.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        # JSON部分を抽出 (稀にAIが説明文をつけてしまうのを防ぐ)
        clean_json = response.text[response.text.find("{"):response.text.rfind("}")+1]
        return json.loads(clean_json)
    except Exception as e:
        print(f"SWOT Generation Error: {e}")
        return None




@st.cache_data(ttl=86400)
def generate_ai_final_verdict(ticker: str, data: dict, cio_inputs: dict, final_judge: dict) -> dict:
    """CIO 7軸スコアを入力とし、AIによる最終ジャッジを定型フォーマットで生成する。"""
    if not GENAI_AVAILABLE:
        return None

    try:
        # 必要なデータを抽出
        total_score = cio_inputs.get("total_score", "N/A")
        scores = cio_inputs.get("scores", {})
        verdict_ja = final_judge.get("verdict_ja", "N/A")
        verdict_desc = final_judge.get("verdict_desc", "")

        prompt = f"""
あなたは米国株のシニア・ポートフォリオマネージャーです。
以下の構造化された分析データ（7軸の統合スコアおよびルールベースの判定）に基づき、
最終的な投資判断を厳密に構造化データ形式（JSON）で出力してください。

【対象銘柄】
- ティッカー: {ticker}
- 企業名: {data.get("name", "N/A")}
- セクター/産業: {data.get("sector", "N/A")} / {data.get("industry", "N/A")}

【CIO 7軸総合評価】
- 総合スコア: {total_score} / 100
- 主な強み: {", ".join(final_judge.get('strengths', ['なし']))}
- 主なリスク: {", ".join(final_judge.get('risks', ['なし']))}
- トレンド: {scores.get('trend_score')} / 100
- エントリー: {scores.get('entry_score')} / 100
- 相対強度: {scores.get('rs_score')} / 100
- 決算品質: {scores.get('earnings_score')} / 100
- 需給: {scores.get('supply_demand_score')} / 100
- バリュエーション: {scores.get('valuation_score')} / 100
- イベント安全性: {scores.get('event_safety_score')} / 100

これらのデータを総合的に解釈し、最終ジャッジを下してください。
必ず以下のJSONフォーマットで出力すること。キーの名前や階層は変更しないこと。
あなたの意見や推測をJSONの外のテキストとして含めてはいけません（JSONのみを返すこと）。

{{
    "final_verdict": "buy | buy_on_pullback | monitor | pass のいずれか1つ",
    "final_verdict_label_ja": "買い | 押し目なら買い | 監視継続 | 見送り のいずれか1つ",
    "buy_now": "true または false (boolean)",
    "confidence_level": "high | medium | low のいずれか1つ",
    "confidence_label_ja": "高確信 | 中確信 | 低確信 のいずれか1つ",
    "one_line_summary": "最終判断を一言で表す1行要約",
    "top_reasons": [
        "最大の判断理由1",
        "最大の判断理由2",
        "最大の判断理由3"
    ],
    "top_risks": [
        "最大のリスク1",
        "最大のリスク2"
    ],
    "best_entry_condition": "具体的なベストエントリー条件（例: 20日線反発確認など。箇条書きではなく一文で）",
    "invalidation_condition": "撤退・シナリオ無効化条件（例: 50日線明確割れなど。箇条書きではなく一文で）",
    "investor_type_fit": "どのような投資スタイルに向いているか（例: 押し目継続型、モメンタム追及型）",
    "action_plan": [
        "具体的なアクション1",
        "具体的なアクション2",
        "具体的なアクション3"
    ],
    "full_commentary": "各軸のスコアを踏まえ、なぜその判断に至ったかを論理的に解説するコメント（200〜300文字程度）"
}}
"""
        response = AI_CLIENT.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        # JSON部分を抽出
        text = response.text
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_json = text[start_idx:end_idx+1]
            return json.loads(clean_json)
        return None
    except Exception as e:
        print(f"AI Final Verdict Error: {e}")
        return None

def generate_short_term_ai_verdict(ticker: str, data: dict, snap: dict) -> dict:
    """短期モード用のAIジャッジを定型フォーマットで生成する。"""
    if not GENAI_AVAILABLE:
        return None

    try:
        # 解析データをまとめる
        breakout = snap.get("breakout_details", {})
        vwap = snap.get("vwap_details", {})
        setup = snap.get("setup_details", {})
        
        # 安全な文字列化
        price_val = snap.get('price')
        price_str = f"${price_val:.2f}" if price_val is not None else "N/A"
        chg_val = snap.get('chg_pct')
        chg_str = f"{chg_val:+.2f}%" if chg_val is not None else "N/A"
        vol_val = snap.get('vol_ratio')
        vol_str = f"{vol_val:.2f}x" if vol_val is not None else "N/A"
        
        prompt = f"""
あなたは米国株のデイトレーダー兼スキャルパー、短期スイングトレーダーのメンターです。
以下の短期的な解析データ（20日高値、VWAP、出来高、トレンド）に基づき、
「今日・明日・数日内」の視点での投資判断を厳密に構造化データ形式（JSON）で出力してください。

【対象銘柄】
- ティッカー: {ticker}
- 価格: {price_str} / 前日比: {chg_str}
- 出来高倍率: {vol_str}

【解析済データ】
- 短期トレンド: {snap.get('trend')}
- 短期ブレイク判定: {breakout.get('label')} (Score: {breakout.get('score')})
- VWAP/ギャップ判定: {vwap.get('label')} (Score: {vwap.get('score')})
- 総合セットアップスコア: {setup.get('score')} / 100
- 判定根拠の要約: {", ".join(setup.get('reasons', []))}

これらのデータを総合的に解釈し、短期目線での最終ジャッジを下してください。
必ず以下のJSONフォーマットで出力すること。キーの名前や階層は変更しないこと。
あなたの意見や推測をJSONの外のテキストとして含めてはいけません（JSONのみを返すこと）。

{{
    "short_ai_verdict": "setup_candidate | buy_on_pullback | monitor | pass のいずれか1つ",
    "short_ai_verdict_label_ja": "仕掛け候補 | 押し待ち | 監視 | 見送り のいずれか1つ",
    "confidence_level": "high | medium | low のいずれか1つ",
    "confidence_label_ja": "高確信 | 中確信 | 低確信 のいずれか1つ",
    "one_line_summary": "短期判断を一言で表す1行要約（50文字程度）",
    "top_reasons": [
        "最大の判断理由1",
        "最大の判断理由2",
        "最大の判断理由3"
    ],
    "top_risks": [
        "最大のリスク1",
        "最大のリスク2"
    ],
    "action_plan": [
        "具体的なエントリー/イグジットのアクション1",
        "具体的なエントリー/イグジットのアクション2",
        "具体的なエントリー/イグジットのアクション3"
    ],
    "invalidation_condition": "シナリオが無効化され、撤退すべき条件（例: VWAP明確割れ、当日安値更新など）"
}}
"""
        response = AI_CLIENT.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        # JSON部分を抽出
        text = response.text
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_json = text[start_idx:end_idx+1]
            return json.loads(clean_json)
        return None
    except Exception as e:
        print(f"Short Term AI Verdict Error: {e}")
        return None

def render_short_term_ai_judge(ticker: str, data: dict, snap: dict):
    """短期モード用のAIジャッジを表示する。"""
    import streamlit as st
    
    if not GENAI_AVAILABLE:
        st.warning("⚠️ Gemini APIが設定されていないため、AIジャッジを利用できません。")
        return

    st.markdown("#### ⚖️ 短期AIジャッジ (Short-Term Tactical View)")
    
    if st.button("🤖 AIに短期売買戦略を聞く", key=f"short_ai_btn_{ticker}"):
        with st.spinner("AIが短期モメンタムを解析中..."):
            verdict = generate_short_term_ai_verdict(ticker, data, snap)
            
            if verdict:
                # 判定によって色を変更
                color = "#10b981" # 仕掛け候補, 押し待ち
                if verdict['short_ai_verdict'] == "pass": color = "#ef4444"
                elif verdict['short_ai_verdict'] == "monitor": color = "#f59e0b"
                
                st.markdown(f"""
                    <div style='padding: 24px; background: rgba(255,255,255,0.03); border-radius: 16px; border: 1px solid {color}44; margin-bottom: 24px;'>
                        <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;'>
                            <div>
                                <div style='font-size: 0.85rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>AI Verdict</div>
                                <div style='font-size: 1.8rem; font-weight: 800; color: {color};'>{verdict['short_ai_verdict_label_ja']}</div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='font-size: 0.85rem; color: #94a3b8; font-weight: 600;'>確信度</div>
                                <div style='font-size: 1.1rem; font-weight: 700; color: #f8fafc;'>{verdict['confidence_label_ja']}</div>
                            </div>
                        </div>
                        <div style='font-size: 1.1rem; color: #f1f5f9; font-weight: 600; margin-bottom: 20px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px;'>
                            {verdict['one_line_summary']}
                        </div>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 24px;'>
                            <div>
                                <div style='font-size: 0.9rem; font-weight: 700; color: #10b981; margin-bottom: 10px; border-bottom: 1px solid #10b98133; padding-bottom: 4px;'>🚀 主なプラス材料</div>
                                {"".join([f"<div style='font-size: 0.85rem; color: #e2e8f0; margin-bottom: 6px;'>• {r}</div>" for r in verdict['top_reasons']])}
                            </div>
                            <div>
                                <div style='font-size: 0.9rem; font-weight: 700; color: #ef4444; margin-bottom: 10px; border-bottom: 1px solid #ef444433; padding-bottom: 4px;'>⚠️ 直近のリスク</div>
                                {"".join([f"<div style='font-size: 0.85rem; color: #e2e8f0; margin-bottom: 6px;'>• {r}</div>" for r in verdict['top_risks']])}
                            </div>
                        </div>
                        <div style='margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);'>
                            <div style='font-size: 0.9rem; font-weight: 700; color: #38bdf8; margin-bottom: 12px;'>⏱ アクションプラン (売買戦略)</div>
                            {"".join([f"<div style='font-size: 0.85rem; color: #e2e8f0; margin-bottom: 6px;'>✅ {a}</div>" for a in verdict['action_plan']])}
                        </div>
                        <div style='margin-top: 16px; padding: 12px; background: rgba(239,68,68,0.1); border-radius: 8px; border: 1px solid rgba(239,68,68,0.2);'>
                            <div style='font-size: 0.85rem; font-weight: 700; color: #ef4444;'>❌ 撤退条件 (Invalidation)</div>
                            <div style='font-size: 0.85rem; color: #f8fafc; margin-top: 4px;'>{verdict['invalidation_condition']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("AI分析の生成中にエラーが発生しました。時間を置いて再度お試しください。")

def render_short_term_watchlist_panel(snap: dict):
    """短期ウォッチリストの進捗と不足条件を表示する"""
    import streamlit as st
    if "watchlist_details" not in snap:
        return
        
    det = snap["watchlist_details"]
    
    with st.container(border=True):
        st.markdown(f"##### 📌 ウォッチリスト条件: {det['label']} ({det['met_count']}/{det['total_count']})")
        
        # 条件チェックリストを横並びチップで表示
        checks_html = ""
        for c in det["conditions"]:
            if c["met"]:
                checks_html += f"<span style='background:rgba(16,185,129,0.1); color:#10b981; padding:2px 10px; border-radius:12px; margin-right:8px; font-size:0.8rem; border:1px solid rgba(16,185,129,0.2);'>✅ {c['label']}</span>"
            else:
                checks_html += f"<span style='background:rgba(255,255,255,0.05); color:#94a3b8; padding:2px 10px; border-radius:12px; margin-right:8px; font-size:0.8rem; border:1px solid rgba(255,255,255,0.1);'>⚪ {c['label']}</span>"
        
        st.markdown(f"<div style='margin-bottom:15px; display:flex; flex-wrap:wrap; gap:8px;'>{checks_html}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**⚡️ 次のトリガー:**  \n<span style='color:#38bdf8;'>{det['next_trigger']}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**🎯 行動計画:**  \n{det['action_if_triggered']}")

def render_short_term_alert_panel(snap: dict):
    """短期アラート条件を上下対比で表示する"""
    import streamlit as st
    if "alert_details" not in snap:
        return
        
    det = snap["alert_details"]
    
    # 優先度によって色を変える
    priority_color = "#94a3b8" # low
    if det["alert_priority"] == "high": priority_color = "#ef4444"
    elif det["alert_priority"] == "medium": priority_color = "#f59e0b"

    with st.container(border=True):
        st.markdown(f"##### 🔔 アラート条件マトリクス <span style='font-size:0.8rem; background:{priority_color}22; color:{priority_color}; padding:2px 8px; border-radius:8px; border:1px solid {priority_color}44;'>{det['alert_priority_label_ja']}</span>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div style='color:#10b981; font-weight:700; margin-bottom:8px;'>📈 上方向 (注目トリガー)</div>", unsafe_allow_html=True)
            for a in det["upside_alerts"]:
                st.markdown(f"<div style='font-size:0.85rem; color:#e2e8f0; margin-bottom:4px;'>⬆️ {a}</div>", unsafe_allow_html=True)
                
        with c2:
            st.markdown("<div style='color:#ef4444; font-weight:700; margin-bottom:8px;'>📉 下方向 (警戒トリガー)</div>", unsafe_allow_html=True)
            for a in det["downside_alerts"]:
                st.markdown(f"<div style='font-size:0.85rem; color:#e2e8f0; margin-bottom:4px;'>⬇️ {a}</div>", unsafe_allow_html=True)
        
        st.divider()
        st.markdown(f"**💡 総括:** {det['comment']}")

@st.cache_data(ttl=86400)
def get_translated_summary(summary_text: str) -> str:
    """事業概要をAIなしで安定して日本語に翻訳する。"""
    if not summary_text:
        return "事業概要のデータがありません。"

    translated = translate_to_japanese(summary_text)
    return translated



# ─────────────────────────────────────────────
# データ取得
# ─────────────────────────────────────────────

def fetch_next_earnings_date(ticker: str) -> dict:
    """
    yfinanceを用いて次回決算日を取得し、結果と状態を返す。
    取得元と失敗理由を明示的にし、タブ間での取得のズレを防ぐ。
    """
    import pandas as pd
    import yfinance as yf
    
    result = {
        "earnings_date": None,
        "source": "none",
        "status": "missing",
        "message": "取得できませんでした"
    }
    
    try:
        stock = yf.Ticker(ticker)
        
        # 1. stock.calendar (優先)
        try:
            cal = stock.calendar
            if isinstance(cal, dict) and "Earnings Date" in cal:
                raw_d = cal["Earnings Date"]
                val = raw_d[0] if isinstance(raw_d, list) else raw_d
                if pd.notna(val):
                    result["earnings_date"] = pd.Timestamp(val).date()
                    result["source"] = "calendar"
                    result["status"] = "ok"
                    result["message"] = "calendar (dict) から取得"
                    return result
            elif hasattr(cal, "iloc") and not cal.empty:
                val = cal.iloc[0, 0]
                if pd.notna(val):
                    result["earnings_date"] = pd.Timestamp(val).date()
                    result["source"] = "calendar"
                    result["status"] = "ok"
                    result["message"] = "calendar (dataframe) から取得"
                    return result
        except Exception as e:
            result["message"] = f"calendar 取得エラー: {str(e)}"
            
        # 2. stock.earnings_dates (フォールバック)
        try:
            ed = stock.earnings_dates
            if ed is not None and not ed.empty:
                today = pd.Timestamp.now(tz=ed.index.tz).normalize()
                future_idx = ed.index[ed.index >= today]
                if not future_idx.empty:
                    result["earnings_date"] = future_idx[0].date()  # 最も近い未来日 (昇順なら0番目だが、yfinanceは降順の場合がある。一応一番近いものを取る)
                    # yfinance の recent earnings_dates は降順 (新しい日付ほど上) かもしれないので
                    # future_idx[-1] にするのが一般的な一番近い未来日。
                    # Wait, if future dates are eg: [2025-05-15, 2024-05-15] then [-1] is smallest if descending,
                    # index >= today -> keeps order. Let's just use minimum date in future_idx.
                    result["earnings_date"] = min(d.date() for d in future_idx)
                    
                    result["source"] = "earnings_dates"
                    result["status"] = "ok"
                    result["message"] = "earnings_dates から最も近い未来日を取得"
                    return result
                else:
                    result["message"] = "earnings_dates 内に未来の決算日がありません"
        except Exception as e:
            if "message" not in result or result["message"] == "取得できませんでした" or "calendar 取得エラー" in result["message"]:
                result["message"] = f"earnings_dates 取得エラー: {str(e)}"
                
    except Exception as e:
        result["message"] = f"Ticker 取得エラー: {str(e)}"
        
    return result

@st.cache_data(ttl=300)
def fetch_stock_data(ticker: str) -> tuple[dict | None, str | None]:
    """yfinance を使って株価指標を取得する。詳細データが取得できない場合は基本データで補完する。"""
    error_msg = None
    try:
        stock = yf.Ticker(ticker)
        # 1. メインの info 取得試行
        try:
            info = stock.info
        except Exception as e:
            info = None
            error_msg = f"yfinance.info エラー: {str(e)}"
        
        # 基本的な器を作成
        res = {}
        
        # infoが取得できた場合
        if info and isinstance(info, dict) and "shortName" in info:
            res = {
                "name": info.get("shortName") or info.get("longName") or ticker,
                "sector": info.get("sector") or info.get("sectorKey"),
                "industry": info.get("industry") or info.get("industryKey"),
                "exchange": info.get("exchange"),
                "long_summary": info.get("longBusinessSummary", ""),
                "website": info.get("website", ""),
                "employees": info.get("fullTimeEmployees"),
                "city": info.get("city", ""),
                "state": info.get("state", ""),
                "country": info.get("country", ""),
                "officers": info.get("companyOfficers", []),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "prev_close": info.get("previousClose"),
                "shares_outstanding": info.get("sharesOutstanding"),
                "total_cash": info.get("total_cash", 0),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "eps_trailing": info.get("trailingEps"),
                "eps_forward": info.get("forwardEps"),
                "eps_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
                "beta": info.get("beta"),
                "profit_margins": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "operating_margins": info.get("operatingMargins"),
                "roe": info.get("returnOnEquity"),
                "avg_vol_3m": info.get("averageVolume"),
                "avg_vol_10d": info.get("averageVolume10days"),
                "short_ratio": info.get("shortPercentOfFloat"),
                "ex_dividend_date": info.get("exDividendDate"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
            }
        
        # 2. infoが不完全な場合の fast_info 補完
        try:
            fast = stock.fast_info
            if fast:
                if not res.get("name"): res["name"] = ticker
                if not res.get("price"): res["price"] = fast.get("lastPrice")
                if not res.get("market_cap"): res["market_cap"] = fast.get("marketCap")
                if not res.get("currency"): res["currency"] = fast.get("currency", "USD")
                if not res.get("exchange"): res["exchange"] = fast.get("exchange")
                if not res.get("prev_close"): res["prev_close"] = fast.get("previousClose")
                if not res.get("fifty_two_week_high"): res["fifty_two_week_high"] = fast.get("yearHigh")
                if not res.get("fifty_two_week_low"): res["fifty_two_week_low"] = fast.get("yearLow")
        except Exception as e:
            if not error_msg:
                error_msg = f"yfinance.fast_info エラー: {str(e)}"
            else:
                error_msg += f" / fast_infoエラー: {str(e)}"

        # 有効なデータか最終チェック（銘柄名も価格も取れない場合はNG）
        if not res.get("name") or not res.get("price"):
            if not error_msg:
                error_msg = "必要な基本データ（銘柄名または株価）が yfinance から取得できませんでした。"
            return None, error_msg

        # 3. セクター等の欠損補完
        for k in ["sector", "industry", "exchange"]:
            if not res.get(k) or res.get(k) == "—":
                res[k] = "—"

        # 決算日の取得 (専用関数へ集約)
        ed_info = fetch_next_earnings_date(ticker)
        res["earnings_date"] = ed_info["earnings_date"]
        res["earnings_date_source"] = ed_info["source"]
        res["earnings_date_message"] = ed_info["message"]

        # 日本語化処理
        res["sector_display"] = SECTOR_JA_MAP.get(res["sector"], res["sector"])
        res["industry_display"] = INDUSTRY_JA_MAP.get(res["industry"], res["industry"])

        return res, error_msg
    except Exception as e:
        import traceback
        full_err = traceback.format_exc()
        print(f"Fetch Error for {ticker}: {full_err}")
        return None, f"致命的な取得エラー: {str(e)}\n\n{full_err}"



@st.cache_data(ttl=300)
def fetch_financials(ticker: str) -> tuple[dict | None, str | None]:
    """yfinance を使って過去の財務データ（損益計算書 & キャッシュフロー）を取得する。"""
    try:
        stock = yf.Ticker(ticker)

        # 年次損益計算書
        try:
            income_stmt = stock.financials  # columns = 日付, rows = 項目
            cashflow = stock.cashflow
        except Exception as e:
            return None, f"財務データアクセスエラー: {str(e)}"

        if income_stmt is None or income_stmt.empty:
            return None

        # 日付を昇順にソート
        income_stmt = income_stmt.T.sort_index()
        cashflow = cashflow.T.sort_index() if cashflow is not None and not cashflow.empty else pd.DataFrame()

        result = {"dates": [d.strftime("%Y") for d in income_stmt.index]}

        # 売上高
        for col_name in ["Total Revenue", "TotalRevenue"]:
            if col_name in income_stmt.columns:
                vals = to_millions(income_stmt[col_name]).tolist()
                result["revenue"] = [0 if math.isnan(v) else v for v in vals]
                break
        else:
            result["revenue"] = None

        # 純利益
        for col_name in ["Net Income", "NetIncome"]:
            if col_name in income_stmt.columns:
                vals = to_millions(income_stmt[col_name]).tolist()
                result["net_income"] = [0 if math.isnan(v) else v for v in vals]
                break
        else:
            result["net_income"] = None

        # 営業キャッシュフロー
        if not cashflow.empty:
            cf_dates = [d.strftime("%Y") for d in cashflow.index]
            for col_name in ["Operating Cash Flow", "OperatingCashFlow",
                             "Total Cash From Operating Activities"]:
                if col_name in cashflow.columns:
                    vals = to_millions(cashflow[col_name]).tolist()
                    result["operating_cf"] = [0 if math.isnan(v) else v for v in vals]
                    result["cf_dates"] = cf_dates
                    break
            else:
                result["operating_cf"] = None
                result["cf_dates"] = cf_dates
        else:
            result["operating_cf"] = None
            result["cf_dates"] = []

        return result, None
    except Exception as e:
        return None, f"財務データ取得エラー: {str(e)}"


@st.cache_data(ttl=300)
def fetch_quarterly_financials(ticker: str) -> tuple[dict | None, str | None]:
    """yfinance を使って四半期ごとの財務データ（損益計算書 & キャッシュフロー）を取得する。"""
    try:
        stock = yf.Ticker(ticker)

        # 四半期損益計算書
        income_stmt = stock.quarterly_financials
        cashflow = stock.quarterly_cashflow

        if income_stmt is None or income_stmt.empty:
            return None

        # 日付を昇順にソート（行=項目, 列=日付 → 転置して 行=日付, 列=項目 にする）
        income_stmt = income_stmt.T.sort_index()
        cashflow = cashflow.T.sort_index() if cashflow is not None and not cashflow.empty else pd.DataFrame()

        def fmt_quarter(d):
            """日付から '2025 Q1' 形式の文字列を生成する"""
            q = (d.month - 1) // 3 + 1
            return f"{d.year} Q{q}"

        result = {"dates": [fmt_quarter(d) for d in income_stmt.index]}

        # 売上高
        for col_name in ["Total Revenue", "TotalRevenue", "Operating Revenue"]:
            if col_name in income_stmt.columns:
                vals = to_millions(income_stmt[col_name]).tolist()
                result["revenue"] = [0 if math.isnan(v) else v for v in vals]
                break
        else:
            result["revenue"] = None

        # 純利益
        for col_name in ["Net Income", "NetIncome", "Net Income Common Stockholders"]:
            if col_name in income_stmt.columns:
                vals = to_millions(income_stmt[col_name]).tolist()
                result["net_income"] = [0 if math.isnan(v) else v for v in vals]
                break
        else:
            result["net_income"] = None

        # 営業キャッシュフロー
        if not cashflow.empty:
            cf_dates = [fmt_quarter(d) for d in cashflow.index]
            for col_name in ["Operating Cash Flow", "OperatingCashFlow",
                             "Total Cash From Operating Activities"]:
                if col_name in cashflow.columns:
                    vals = to_millions(cashflow[col_name]).tolist()
                    result["operating_cf"] = [0 if math.isnan(v) else v for v in vals]
                    result["cf_dates"] = cf_dates
                    break
            else:
                result["operating_cf"] = None
                result["cf_dates"] = cf_dates
        else:
            result["operating_cf"] = None
            result["cf_dates"] = []

        return result, None
    except Exception as e:
        print(f"Quarterly Financials Error: {e}")
        return None, f"四半期財務データ取得エラー: {str(e)}"


@st.cache_data(ttl=300)
def fetch_advanced_financials(ticker: str) -> dict | None:
    """yfinance から高度な財務指標（デュポン分析、ROIC、安全性など）を計算するためのデータを取得する。"""
    try:
        stock = yf.Ticker(ticker)
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        if bs.empty or fin.empty:
            return None

        # 最新の年次データを取得
        bs = bs.T.sort_index()
        fin = fin.T.sort_index()
        cf = cf.T.sort_index() if cf is not None and not cf.empty else pd.DataFrame()

        latest_bs = bs.iloc[-1]
        latest_fin = fin.iloc[-1]
        latest_cf = cf.iloc[-1] if not cf.empty else pd.Series()

        res = {}
        
        # --- 基礎データ取得 ---
        def get_val(df_row, keys):
            for k in keys:
                if k in df_row and pd.notna(df_row[k]):
                    return float(df_row[k])
            return None

        total_assets = get_val(latest_bs, ["Total Assets"])
        total_equity = get_val(latest_bs, ["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity", "Total Equity"])
        current_assets = get_val(latest_bs, ["Current Assets"])
        current_liabilities = get_val(latest_bs, ["Current Liabilities"])
        total_debt = get_val(latest_bs, ["Total Debt"])
        invested_capital = get_val(latest_bs, ["Invested Capital"])

        net_income = get_val(latest_fin, ["Net Income", "Net Income Continuous Operations"])
        revenue = get_val(latest_fin, ["Total Revenue", "Operating Revenue"])
        ebit = get_val(latest_fin, ["EBIT", "Operating Income"])
        pretax_income = get_val(latest_fin, ["Pretax Income"])
        tax_provision = get_val(latest_fin, ["Tax Provision"])
        tax_rate = get_val(latest_fin, ["Tax Rate For Calcs"])

        if tax_rate is None and pretax_income and tax_provision:
            tax_rate = tax_provision / pretax_income if pretax_income != 0 else 0

        operating_cf = get_val(latest_cf, ["Operating Cash Flow", "Total Cash From Operating Activities"])

        # --- 計算 ---
        # デュポン分析
        if net_income and total_equity and total_equity > 0:
            res["ROE"] = net_income / total_equity
        if net_income and revenue and revenue > 0:
            res["Net Margin"] = net_income / revenue
        if revenue and total_assets and total_assets > 0:
            res["Asset Turnover"] = revenue / total_assets
        if total_assets and total_equity and total_equity > 0:
            res["Financial Leverage"] = total_assets / total_equity

        # ROIC
        if ebit and invested_capital and invested_capital > 0:
            tr = tax_rate if tax_rate else 0.21 # fallback
            nopat = ebit * (1 - tr)
            res["ROIC"] = nopat / invested_capital

        # 安全性
        if total_equity and total_assets and total_assets > 0:
            res["Equity Ratio"] = total_equity / total_assets
        if current_assets and current_liabilities and current_liabilities > 0:
            res["Current Ratio"] = current_assets / current_liabilities
        if total_debt is not None and total_equity and total_equity > 0:
            res["D/E Ratio"] = total_debt / total_equity

        # CF質
        if operating_cf and net_income and net_income > 0:
            res["Operating CF / Net Income"] = operating_cf / net_income

        # --- 過去5年FCF ---
        fcf_list = []
        fcf_dates = []
        if not cf.empty:
            # 過去5年分（最大）
            recent_cf = cf.tail(5)
            # FCF列を探す
            fcf_col = None
            for c in ["Free Cash Flow"]:
                if c in recent_cf.columns:
                    fcf_col = c
                    break
            
            if fcf_col:
                for d, val in recent_cf[fcf_col].items():
                    if pd.notna(val):
                        fcf_dates.append(d.strftime("%Y"))
                        fcf_list.append(val / 1_000_000) # 百万ドル単位
            else:
                # フォールバック: 営業CF + 設備投資額
                if "Operating Cash Flow" in recent_cf.columns and "Capital Expenditure" in recent_cf.columns:
                    for d in recent_cf.index:
                        ocf = recent_cf.loc[d, "Operating Cash Flow"]
                        capex = recent_cf.loc[d, "Capital Expenditure"]
                        if pd.notna(ocf) and pd.notna(capex):
                            fcf_dates.append(d.strftime("%Y"))
                            # yfinanceではCapExは通常負の値なので、加算することで差し引きになる
                            fcf_list.append((ocf + capex) / 1_000_000)

        res["FCF Dates"] = fcf_dates
        res["FCF Values"] = fcf_list

        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None




def calculate_earnings_valuation(base_eps: float, growth_rate: float, horizon_years: int, target_pe: float, discount_rate: float = 0.08) -> dict | None:
    """利益ベースの理論株価を計算する（累積利益 + 未来の期待価値を現在価値に割引）。"""
    try:
        if any(v is None or pd.isna(v) for v in [base_eps, growth_rate, target_pe, discount_rate]):
            return None
        
        if base_eps <= 0:
            return None
            
        accumulated_pv = 0
        current_eps = base_eps
        
        # 指定期間の利益を積み上げ & 現在価値に割引
        for t in range(1, horizon_years + 1):
            current_eps *= (1 + growth_rate)
            # 各年の利益を現在価値に割り戻す
            pv_eps = current_eps / ((1 + discount_rate) ** t)
            accumulated_pv += pv_eps
            
        # 最終年の期待株価 (EPS * PER)
        expected_price_future = current_eps * target_pe
        # 期待株価を現在価値に割り戻す
        expected_price_pv = expected_price_future / ((1 + discount_rate) ** horizon_years)
        
        # 合計の現在価値（＝理論上の適正株価）
        total_intrinsic_value = accumulated_pv + expected_price_pv
        
        return {
            "accumulated_profit": accumulated_pv, # 現在価値ベースの累積利益
            "expected_price": expected_price_pv,  # 現在価値ベースの期待価格
            "total_value": total_intrinsic_value,
            "final_eps": current_eps,
            "future_price": expected_price_future
        }
    except Exception:
        return None


import requests

@st.cache_data(ttl=86400)
def get_competitors(ticker: str) -> list:
    """Yahoo Financeから競合銘柄を取得する"""
    try:
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(f'https://query2.finance.yahoo.com/v6/finance/recommendationsbysymbol/{ticker}', headers=h, timeout=5)
        if r.status_code == 200:
            data = r.json()
            recs = data.get('finance', {}).get('result', [])
            if recs and len(recs) > 0:
                symbols = recs[0].get('recommendedSymbols', [])
                return [s['symbol'] for s in symbols[:5]]
    except Exception as e:
        print(f"Error getting competitors: {e}")
    return []


@st.cache_data(ttl=3600)
def calculate_f_score(ticker: str) -> dict:
    """ジョセフ・ピオトロスキーのFスコア（9点満点）を判定する"""
    results = {}
    try:
        stock = yf.Ticker(ticker)
        income = stock.income_stmt
        bs = stock.balance_sheet
        cf = stock.cashflow
        
        if len(income.columns) < 2 or len(bs.columns) < 2 or len(cf.columns) < 2:
            return {}

        def get_val(df, keys, year_idx=0):
            for k in keys:
                if k in df.index:
                    return df.loc[k].iloc[year_idx]
            return None

        # --- 1. Profitability ---
        ni_curr = get_val(income, ['Net Income', 'Net Income Common Stockholders'])
        ni_pass = ni_curr > 0 if ni_curr is not None else False
        results['1. 当期純利益（黒字か）'] = {
            'pass': ni_pass,
            'val': f"${ni_curr/1e6:,.1f}M" if ni_curr else "N/A",
            'reason': "当期純利益がプラス（黒字）" if ni_pass else "当期純利益がマイナス（赤字）であるため不合格"
        }
        
        total_assets_curr = get_val(bs, ['Total Assets'])
        total_assets_prev = get_val(bs, ['Total Assets'], 1)
        roa_curr = ni_curr / total_assets_curr if ni_curr and total_assets_curr else 0
        roa_prev = get_val(income, ['Net Income', 'Net Income Common Stockholders'], 1) / total_assets_prev if total_assets_prev else 0
        roa_pass = roa_curr > roa_prev
        results['2. ROAの改善（前期比）'] = {
            'pass': roa_pass,
            'val': f"{roa_prev:.2%} → {roa_curr:.2%}",
            'reason': f"ROAが前期({roa_prev:.2%})から改善({roa_curr:.2%})" if roa_pass else f"ROAが前期({roa_prev:.2%})から悪化({roa_curr:.2%})しているため不合格"
        }
        
        ocf_curr = get_val(cf, ['Operating Cash Flow'])
        ocf_pass = ocf_curr > 0 if ocf_curr is not None else False
        results['3. 営業CF（プラスか）'] = {
            'pass': ocf_pass,
            'val': f"${ocf_curr/1e6:,.1f}M" if ocf_curr else "N/A",
            'reason': "営業キャッシュフローがプラスで本業から現金を稼いでいる" if ocf_pass else "営業CFがマイナスで本業から現金を生み出せていないため不合格"
        }
        
        quality_pass = ocf_curr > ni_curr if ocf_curr and ni_curr else False
        results['4. 利益の質（営業CF > 純利益）'] = {
            'pass': quality_pass,
            'val': f"CF: ${ocf_curr/1e6:,.1f}M > NI: ${ni_curr/1e6:,.1f}M" if ocf_curr and ni_curr else "N/A",
            'reason': "利益の裏付けとなるキャッシュが十分にある（会計操作のリスク低）" if quality_pass else "利益に対してキャッシュが不足しており、利益の質に疑問があるため不合格"
        }

        # --- 2. Leverage/Liquidity ---
        lt_debt_curr = get_val(bs, ['Long Term Debt']) or 0
        lt_debt_prev = get_val(bs, ['Long Term Debt'], 1) or 0
        lev_curr = lt_debt_curr / total_assets_curr if total_assets_curr else 0
        lev_prev = lt_debt_prev / total_assets_prev if total_assets_prev else 0
        lev_pass = lev_curr <= lev_prev
        results['5. 長期負債比率の低下'] = {
            'pass': lev_pass,
            'val': f"{lev_prev:.1%} → {lev_curr:.1%}",
            'reason': f"長期負債比率が低下({lev_prev:.1%}→{lev_curr:.1%})し、財務体質が改善" if lev_pass else f"長期負債比率が上昇({lev_prev:.1%}→{lev_curr:.1%})し、財務リスクが増加しているため不合格"
        }
        
        curr_assets_curr = get_val(bs, ['Current Assets', 'Total Current Assets'])
        curr_assets_prev = get_val(bs, ['Current Assets', 'Total Current Assets'], 1)
        curr_liab_curr = get_val(bs, ['Current Liabilities', 'Total Current Liabilities'])
        curr_liab_prev = get_val(bs, ['Current Liabilities', 'Total Current Liabilities'], 1)
        cr_curr = curr_assets_curr / curr_liab_curr if curr_assets_curr and curr_liab_curr else 0
        cr_prev = curr_assets_prev / curr_liab_prev if curr_assets_prev and curr_liab_prev else 0
        cr_pass = cr_curr > cr_prev
        results['6. 流動比率の改善'] = {
            'pass': cr_pass,
            'val': f"{cr_prev:.2f} → {cr_curr:.2f}",
            'reason': f"流動比率が{cr_prev:.2f}→{cr_curr:.2f}に改善し、短期的な支払い能力が向上" if cr_pass else f"流動比率が{cr_prev:.2f}→{cr_curr:.2f}に低下し、短期の支払い余力が減少しているため不合格"
        }
        
        shares_curr = get_val(bs, ['Ordinary Shares Number', 'Share Issued'])
        shares_prev = get_val(bs, ['Ordinary Shares Number', 'Share Issued'], 1)
        shares_pass = shares_curr <= shares_prev if shares_curr and shares_prev else True
        results['7. 発行済株式数の増加なし'] = {
            'pass': shares_pass,
            'val': f"{shares_prev/1e6:,.1f}M → {shares_curr/1e6:,.1f}M" if shares_curr and shares_prev else "N/A",
            'reason': "新株発行による既存株主の希薄化がない" if shares_pass else "新株発行により1株あたり価値が希薄化しているため不合格"
        }

        # --- 3. Efficiency ---
        gp_curr = get_val(income, ['Gross Profit'])
        gp_prev = get_val(income, ['Gross Profit'], 1)
        rev_curr = get_val(income, ['Total Revenue'])
        rev_prev = get_val(income, ['Total Revenue'], 1)
        gm_curr = gp_curr / rev_curr if gp_curr and rev_curr else 0
        gm_prev = gp_prev / rev_prev if gp_prev and rev_prev else 0
        gm_pass = gm_curr > gm_prev
        results['8. 売上高総利益率の改善'] = {
            'pass': gm_pass,
            'val': f"{gm_prev:.1%} → {gm_curr:.1%}",
            'reason': f"粗利率が{gm_prev:.1%}→{gm_curr:.1%}に改善し、価格競争力や原価管理が向上" if gm_pass else f"粗利率が{gm_prev:.1%}→{gm_curr:.1%}に低下し、コスト圧力が強まっているため不合格"
        }
        
        at_curr = rev_curr / total_assets_curr if rev_curr and total_assets_curr else 0
        at_prev = rev_prev / total_assets_prev if rev_prev and total_assets_prev else 0
        at_pass = at_curr > at_prev
        results['9. 総資産回転率の改善'] = {
            'pass': at_pass,
            'val': f"{at_prev:.2f} → {at_curr:.2f}",
            'reason': f"資産の効率的活用度が{at_prev:.2f}→{at_curr:.2f}に改善" if at_pass else f"資産活用効率が{at_prev:.2f}→{at_curr:.2f}に悪化し、投資に対するリターンが低下しているため不合格"
        }

    except Exception as e:
        print(f"F-SCORE ERROR: {e}")
    return results

def fetch_supply_demand_data(ticker: str) -> dict:
    """機関動向、インサイダー売買、空売り比率を取得する"""
    data = {}
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 1. Institutional
        data['inst_ownership'] = info.get('heldPercentInstitutions')
        data['major_holders'] = stock.institutional_holders
        
        # 2. Insider
        insider = stock.insider_transactions
        if insider is not None and not insider.empty:
            # 公開市場での売買 (Open Market Purchase/Sale) にフォーカス
            # yfinanceは 'Text' カラムなどで種類を判別可能
            def is_market_trade(text):
                t = str(text).lower()
                return "sale" in t or "purchase" in t
            
            market_insider = insider[insider['Text'].apply(is_market_trade)].copy()
            if not market_insider.empty:
                # 金額計算 (Shares * Price)
                # yfinanceによってPriceが取得できない場合は直近価格で代用
                curr_price = info.get('currentPrice', 0)
                market_insider['Value'] = market_insider.apply(
                    lambda row: row['Shares'] * (row.get('Price', curr_price) or curr_price), axis=1
                )
                # 買い/売りフラグ
                market_insider['Side'] = market_insider['Text'].apply(lambda x: 'Buy' if 'purchase' in str(x).lower() else 'Sell')
                data['insider_trades'] = market_insider
            else:
                data['insider_trades'] = pd.DataFrame()
        else:
            data['insider_trades'] = pd.DataFrame()
            
        # 3. Supply/Demand Balance
        data['short_float'] = info.get('shortPercentOfFloat')
        data['short_ratio'] = info.get('shortRatio')
        
    except Exception as e:
        print(f"SUPPLY/DEMAND ERROR: {e}")
    return data

SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC"
}

def calculate_risk_sensitivity(ticker: str, sector_name: str) -> dict:
    """ベータ値(1Y, 3Y, 5Y)と市場・セクター・金利との相関を算出する"""
    results = {}
    try:
        # セクターETFの特定
        sector_etf = SECTOR_ETF_MAP.get(sector_name, "SPY")
        tickers = [ticker, "SPY", sector_etf, "^TNX"]
        
        # 5年分のデータを取得
        data_5y = yf.download(tickers, period="5y", interval="1d")['Close']
        if data_5y.empty:
            return {}
        
        returns_5y = data_5y.pct_change()
        
        # 1. 期間別ベータの算出
        def get_beta(df):
            if ticker not in df.columns or "SPY" not in df.columns:
                return None
            df_cl = df[[ticker, "SPY"]].dropna()
            if len(df_cl) < 30: return None
            cov = df_cl.cov().iloc[0, 1]
            var = df_cl["SPY"].var()
            return cov / var if var != 0 else None

        results['beta_1y'] = get_beta(returns_5y.iloc[-252:])
        results['beta_3y'] = get_beta(returns_5y.iloc[-(252*3):])
        results['beta_5y'] = get_beta(returns_5y)
        
        # 2. 相関（直近1年）
        corr_1y = returns_5y.iloc[-252:].corr()
        results['corr_market'] = corr_1y.loc[ticker, "SPY"] if "SPY" in corr_1y.columns else 0
        results['corr_sector'] = corr_1y.loc[ticker, sector_etf] if sector_etf in corr_1y.columns else 0
        results['corr_yield'] = corr_1y.loc[ticker, "^TNX"] if "^TNX" in corr_1y.columns else 0
        results['sector_etf_used'] = sector_etf

    except Exception as e:
        print(f"RISK ANALYSIS ERROR: {e}")
    return results

def analyze_vcp_and_trade_plan(ticker: str, data: dict, hist_df: pd.DataFrame) -> dict:
    """VCP（ボラティリティ収縮）の判定とトレードプラン（エントリ、ストップ、サイズ）を生成する"""
    plan = {}
    try:
        # 1. ボラティリティ収縮 (VCP) の簡易判定
        # 過去4週間（5日×4）の週ごとの高安レンジ(%)を計算
        ranges = []
        for i in range(4):
            start = -(5 * (i + 1))
            end = - (5 * i) if i > 0 else len(hist_df)
            week_data = hist_df['Close'].iloc[start:end]
            if not week_data.empty:
                w_range = (week_data.max() - week_data.min()) / week_data.min()
                ranges.append(w_range)
        
        # 逆順にして直近が最後に来るようにする
        ranges = ranges[::-1]
        is_contracting = all(ranges[i] >= ranges[i+1] for i in range(len(ranges)-1))
        
        plan['vcp_status'] = "収縮傾向（Tightness）" if is_contracting else "拡大または不規則"
        plan['vcp_desc'] = " -> ".join([f"{r:.1%}" for r in ranges])
        
        # 2. ブレイクアウト・ポイント (52週高値)
        h52 = hist_df['Close'].iloc[-252:].max()
        plan['buy_point'] = h52
        
        # 3. リスク管理
        curr_p = data.get("price", hist_df['Close'].iloc[-1])
        stop_loss_pct = 0.07 # 基本 7%
        plan['stop_loss_price'] = h52 * (1 - stop_loss_pct)
        
        # 4. 推奨ポジションサイズ (数学的算出)
        # 総資産の 1.25% を 1トレードのリスクとする (Equity Risk)
        # ポジションサイズ = Equity Risk % / Stop Loss %
        equity_risk = 0.0125 
        rec_size = min(0.25, equity_risk / stop_loss_pct) # 最大25%に制限
        plan['position_size_pct'] = rec_size
        
    except Exception as e:
        print(f"TRADE PLAN ERROR: {e}")
    return plan

def create_radar_chart(scores: dict):
    """5軸の統合診断レーダーチャートを作成する"""
    categories = list(scores.keys())
    values = list(scores.values())
    
    # 閉じた多角形にするために最初の値を追加
    values_full = values + [values[0]]
    categories_full = categories + [categories[0]]
    
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_full,
        theta=categories_full,
        fill='toself',
        name='Stock Profile',
        line_color='#34d399',
        fillcolor='rgba(52, 211, 153, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False,
                gridcolor='rgba(255, 255, 255, 0.1)'
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.1)',
                linecolor='rgba(255, 255, 255, 0.3)',
                tickfont=dict(size=10)
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=60, t=30, b=30),
        height=350
    )
    
    return fig

@st.cache_data(ttl=3600)
def evaluate_sepa(ticker: str) -> dict:
    """マーク・ミネルヴィニのトレンド・テンプレート（Stage 2）を判定する"""
    results = {}
    try:
        stock = yf.Ticker(ticker)
        # 2年分のデータを取得 (200日MAと、その80日前を計算するため)
        hist = stock.history(period="2y")
        if hist.empty or len(hist) < 280:
            return {}

        close = hist['Close']
        ma50 = close.rolling(50).mean()
        ma150 = close.rolling(150).mean()
        ma200 = close.rolling(200).mean()

        latest_p = close.iloc[-1]
        c_ma50 = ma50.iloc[-1]
        c_ma150 = ma150.iloc[-1]
        c_ma200 = ma200.iloc[-1]
        
        # 52週高値・安値
        h52 = close.iloc[-252:].max()
        l52 = close.iloc[-252:].min()

        # 1. 株価 > MA150 かつ 株価 > MA200
        results['1. 株価 > MA150 & MA200'] = {
            'pass': latest_p > c_ma150 and latest_p > c_ma200,
            'desc': f"株価(${latest_p:.2f}) が MA150(${c_ma150:.2f}) と MA200(${c_ma200:.2f}) を上回っている"
        }

        # 2. MA150 > MA200
        results['2. MA150 > MA200'] = {
            'pass': c_ma150 > c_ma200,
            'desc': f"MA150(${c_ma150:.2f}) が MA200(${c_ma200:.2f}) より上にある"
        }

        # 3. MA200が4ヶ月（80日）上昇
        ma200_80d = ma200.iloc[-80]
        results['3. MA200の上昇推移'] = {
            'pass': c_ma200 > ma200_80d,
            'desc': f"現在のMA200(${c_ma200:.2f}) が 80日前(${ma200_80d:.2f}) より高い"
        }

        # 4. MA50 > MA150 & MA50 > MA200
        results['4. MA50が他MAより上'] = {
            'pass': c_ma50 > c_ma150 and c_ma50 > c_ma200,
            'desc': f"短期MA50(${c_ma50:.2f}) が 中長期MAの上にある"
        }

        # 5. 株価 > MA50
        results['5. 株価 > MA50'] = {
            'pass': latest_p > c_ma50,
            'desc': f"株価(${latest_p:.2f}) が 短期MA50(${c_ma50:.2f}) を上回っている"
        }

        # 6. 52週安値から+25%以上
        dist_low = (latest_p - l52) / l52
        results['6. 52週安値からの反発'] = {
            'pass': dist_low >= 0.25,
            'desc': f"株価が52週安値(${l52:.2f})から {dist_low:+.1%} (基準+25%以上)"
        }

        # 7. 52週高値から25%以内
        dist_high = (h52 - latest_p) / h52
        results['7. 52週高値圏での推移'] = {
            'pass': dist_high <= 0.25,
            'desc': f"株価が52週高値(${h52:.2f})から -{dist_high:.1%} (基準25%以内)"
        }

        # 8. RS相対比較 (対S&P500)
        h_spy = yf.Ticker("SPY").history(period="1y")['Close']
        spy_perf = (h_spy.iloc[-1] / h_spy.iloc[0]) - 1
        stock_perf = (close.iloc[-1] / close.iloc[-252]) - 1
        rs_ok = stock_perf > spy_perf
        results['8. 相対的強さ (RS)'] = {
            'pass': rs_ok,
            'desc': f"自身の騰落率({stock_perf:+.1%}) が S&P500({spy_perf:+.1%}) を上回っている"
        }

    except Exception as e:
        print(f"SEPA ERROR: {e}")
    return results

@st.cache_data(ttl=3600)
def evaluate_canslim(ticker: str) -> dict:
    """CAN SLIM成長株スコアリングを計算する"""
    results = {}
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # C (Current Earnings): 直近四半期EPS成長率 >= 25%
        try:
            q_eps = stock.quarterly_income_stmt.loc['Basic EPS']
            if len(q_eps) >= 5: # 1年前と比較するために5つ必要
                latest_q = q_eps.iloc[0]
                year_ago_q = q_eps.iloc[4]
                c_growth = (latest_q - year_ago_q) / abs(year_ago_q) if year_ago_q != 0 else 0
                results['C'] = {'pass': c_growth >= 0.25, 'val': f"{c_growth:+.1%}", 'help': "直近四半期のEPSが前年同期比で25%以上成長しているか。"}
            else:
                results['C'] = {'pass': False, 'val': "データ不足", 'help': "比較に十分な四半期データがありません。"}
        except Exception:
            results['C'] = {'pass': False, 'val': "取得失敗", 'help': "四半期EPSを取得できませんでした。"}

        # A (Annual Earnings): 過去3年の年間EPS成長率 >= 25%
        try:
            a_eps = stock.income_stmt.loc['Basic EPS']
            if len(a_eps) >= 3:
                a_growth_1 = (a_eps.iloc[0] - a_eps.iloc[1]) / abs(a_eps.iloc[1]) if a_eps.iloc[1] != 0 else 0
                a_growth_2 = (a_eps.iloc[1] - a_eps.iloc[2]) / abs(a_eps.iloc[2]) if a_eps.iloc[2] != 0 else 0
                is_passing = a_growth_1 >= 0.25 and a_growth_2 >= 0.25
                results['A'] = {'pass': is_passing, 'val': f"直近YoY: {a_growth_1:+.1%}", 'help': "過去3年間の年間EPSが継続して高い成長を維持しているか。"}
            else:
                results['A'] = {'pass': False, 'val': "データ不足", 'help': "比較に十分な年間データがありません。"}
        except Exception:
            results['A'] = {'pass': False, 'val': "取得失敗", 'help': "年間EPSを取得できませんでした。"}

        # N (New Highs): 52週高値から15%以内
        high_52w = info.get('fiftyTwoWeekHigh')
        curr_p = info.get('currentPrice') or info.get('regularMarketPrice')
        if high_52w and curr_p:
            dist = (high_52w - curr_p) / high_52w
            results['N'] = {'pass': dist <= 0.15, 'val': f"高値から-{dist:.1%}", 'help': "株価が52週高値の15%以内にあり、上放れの準備ができているか。"}
        else:
            results['N'] = {'pass': False, 'val': "不明", 'help': "価格データを取得できませんでした。"}

        # L (Leader or Laggard): 対S&P500 相対強度
        try:
            h_stock = stock.history(period="1y")['Close']
            h_spy = yf.Ticker("SPY").history(period="1y")['Close']
            if not h_stock.empty and not h_spy.empty:
                perf_s = (h_stock.iloc[-1] / h_stock.iloc[0]) - 1
                perf_m = (h_spy.iloc[-1] / h_spy.iloc[0]) - 1
                rs_score = perf_s - perf_m
                results['L'] = {'pass': rs_score > 0, 'val': f"対市場: {rs_score:+.1%}", 'help': "S&P500の騰落率を上回る「市場のリーダー」銘柄であるか。"}
            else:
                results['L'] = {'pass': False, 'val': "データ不足", 'help': "相対比較用の価格データがありません。"}
        except Exception:
            results['L'] = {'pass': False, 'val': "取得失敗", 'help': "市場平均データを取得できませんでした。"}

        # S (Supply and Demand): 直近出来高 > 50日平均出来高
        try:
            h_vol = stock.history(period="60d")['Volume']
            if len(h_vol) >= 50:
                avg_vol_50 = h_vol.iloc[-51:-1].mean()
                curr_vol = h_vol.iloc[-1]
                is_heavy = curr_vol > avg_vol_50
                results['S'] = {'pass': is_heavy, 'val': f"平均比: {(curr_vol/avg_vol_50):.1f}倍", 'help': "出来高が50日平均を上回り、機関投資家の買いが集まっているか。"}
            else:
                results['S'] = {'pass': False, 'val': "データ不足", 'help': "50日分の出来高データがありません。"}
        except Exception:
            results['S'] = {'pass': False, 'val': "取得失敗", 'help': "出来高データを取得できませんでした。"}

    except Exception:
        pass
    return results

@st.cache_data(ttl=3600)
def evaluate_weinstein_stage(ticker: str) -> dict:
    """スタン・ワインスタインのステージ分析（1〜4段階 + サブステージ）を判定する"""
    res = {
        "stage": "Unknown",
        "sub_stage": "",
        "stage_label_ja": "判定不能",
        "sub_stage_label_ja": "",
        "full_label": "N/A",
        "full_label_ja": "判定不能",
        "entry_quality": "avoid",
        "entry_comment": "データ不足により判定できません。",
        "description": "",
        "reason": [],
        "latest_close": 0,
        "ma30": 0,
        "price_vs_ma_pct": 0,
        "ma_slope_pct": 0,
        "trend_status": "neutral",
        "volume_status": "normal",
        "breakout_status": "none",
        "rsi": 50,
        "distance_from_52w_high_pct": 0,
        "weeks_in_current_trend": 0
    }
    
    try:
        stock = yf.Ticker(ticker)
        # 30週MA算出のため、約3年分のデータを取得
        hist = stock.history(period="3y")
        if hist.empty or len(hist) < 200:
            return res

        # 日足 → 週足変換 (金利週末)
        logic = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }
        df_w = hist.resample('W-FRI').apply(logic).dropna()
        if len(df_w) < 40:
            return res

        # 指標計算
        df_w['MA30'] = df_w['Close'].rolling(30).mean()
        # 傾き（直近4週の変化率）
        df_w['MA30_Slope'] = (df_w['MA30'] - df_w['MA30'].shift(4)) / df_w['MA30'].shift(4)
        # 週足RSI
        df_w['RSI'] = compute_rsi(df_w['Close'], 14)
        # 52週出来高平均
        df_w['Vol_Avg'] = df_w['Volume'].rolling(52).mean()
        # 52週高値
        df_w['H52'] = df_w['High'].rolling(52).max()
        
        # 直近データの抽出
        latest = df_w.iloc[-1]
        p = latest['Close']
        ma30 = latest['MA30']
        slope = latest['MA30_Slope']
        rsi = latest['RSI']
        vol_avg = latest['Vol_Avg']
        h52 = latest['H52']
        
        if pd.isna(ma30) or pd.isna(slope):
            return res

        res['latest_close'] = p
        res['ma30'] = ma30
        res['price_vs_ma_pct'] = ((p - ma30) / ma30) * 100
        res['ma_slope_pct'] = slope * 100
        res['rsi'] = rsi
        res['distance_from_52w_high_pct'] = ((p - h52) / h52) * 100

        # --- 判定ロジック ---
        reasons = []
        stage = ""
        sub = ""
        
        # 基本トレンドと乖離
        dist_pct = res['price_vs_ma_pct']
        vol_ratio = latest['Volume'] / vol_avg if vol_avg > 0 else 1.0
        
        if slope > 0.005: # 上向き
            if p > ma30:
                stage = "Stage 2"
                res['stage_label_ja'] = "第2段階（上昇局面）"
                if dist_pct < 10:
                    sub = "early"
                    res['sub_stage_label_ja'] = "初期"
                    res['entry_quality'] = "ideal"
                    res['entry_comment'] = "ワインスタイン流の本命エントリー帯。ベースを抜けて上昇が始まったばかりの理想的な局面です。"
                    res['description'] = "ベース上抜け後の上昇初動局面です。"
                    reasons.append("30週線が明確に上向き")
                    reasons.append(f"株価が30週線の上方に位置（乖離 {dist_pct:.1f}%）")
                    if vol_ratio > 1.2: reasons.append("出来高が平均を上回り、買い圧力が強い")
                elif dist_pct > 25 or rsi > 70:
                    sub = "late"
                    res['sub_stage_label_ja'] = "後期"
                    res['entry_quality'] = "watch"
                    res['entry_comment'] = "上昇後半で新規エントリーは慎重に。すでにかなり伸びており、押し目待ちが賢明です。"
                    res['description'] = "トレンドは強いが、短期的には過熱感が見られます。"
                    reasons.append("30週線は上向きを維持")
                    reasons.append(f"株価が30週線から大きく乖離（{dist_pct:.1f}%）")
                    if rsi > 70: reasons.append("週足RSIが買われすぎ水準")
                else:
                    sub = "mid"
                    res['sub_stage_label_ja'] = "中期"
                    res['entry_quality'] = "good"
                    res['entry_comment'] = "健全な上昇トレンドを継続中。押し目買いの候補として有効な局面です。"
                    res['description'] = "安定した上昇トレンドが続いています。"
                    reasons.append("30週線が安定して右肩上がり")
                    reasons.append("株価が30週線の上で健全に推移")
            else:
                stage = "Stage 3"
                res['stage_label_ja'] = "第3段階（天井形成）"
                sub = "early"
                res['sub_stage_label_ja'] = "初期"
                res['entry_quality'] = "avoid"
                res['entry_comment'] = "上昇の勢いが鈍化。30週線を割り込んでおり、トレンド転換の警戒が必要です。"
                res['description'] = "上昇トレンドに陰りが見え始め、勢いが弱まっています。"
                reasons.append("30週線の上向きが弱まっている")
                reasons.append("価格が30週線を下回ってきた")

        elif slope < -0.005: # 下向き
            if p < ma30:
                stage = "Stage 4"
                res['stage_label_ja'] = "第4段階（下降局面）"
                if dist_pct < -20 or rsi < 30:
                    sub = "late"
                    res['sub_stage_label_ja'] = "後期"
                    res['entry_quality'] = "watch"
                    res['entry_comment'] = "過度な下落による売られすぎ水準。反転監視を開始できるが、買いはまだ早い局面です。"
                    res['description'] = "長期的な下降トレンドの最終局面、セリングクライマックスに近い可能性があります。"
                    reasons.append("30週線が急角度で下向き")
                    reasons.append(f"株価が30週線から下方へ大きく乖離（{dist_pct:.1f}%）")
                    if rsi < 30: reasons.append("週足RSIが売られすぎ水準")
                elif dist_pct > -5:
                    sub = "early"
                    res['sub_stage_label_ja'] = "初期"
                    res['entry_quality'] = "avoid"
                    res['entry_comment'] = "下降トレンドの初期段階。戻り売りが出やすく、基本は回避すべき局面です。"
                    res['description'] = "価格が30週線を割り込み、本格的な下落が始まっています。"
                    reasons.append("30週線が下向きに転換")
                    reasons.append("価格が長期MAの下で推移開始")
                else:
                    sub = "mid"
                    res['sub_stage_label_ja'] = "中期"
                    res['entry_quality'] = "avoid"
                    res['entry_comment'] = "安定した下降トレンド。保有は危険であり、静観を推奨します。"
                    res['description'] = "下落の勢いが強く、底打ちの兆候はまだ見られません。"
                    reasons.append("30週線が安定して下向き")
                    reasons.append("安値更新が続いている")
            else:
                stage = "Stage 1"
                res['stage_label_ja'] = "第1段階（底固め）"
                sub = "early"
                res['sub_stage_label_ja'] = "初期"
                res['entry_quality'] = "avoid"
                res['entry_comment'] = "底打ちの可能性はあるが、まだ信頼性は低い。30週線の反転を待つべき局面です。"
                res['description'] = "長期下落の後に価格が30週線上に戻ってきましたが、MAはまだ下向きです。"
                reasons.append("30週線は依然として下向き")
                reasons.append("価格が自律反発でMAを一時的に上抜けた状態")

        else: # 横ばい
            if p > ma30:
                recent_max = df_w['Close'].rolling(10).max().iloc[-2]
                if p > recent_max:
                    stage = "Stage 2"
                    res['stage_label_ja'] = "第2段階（上昇局面）"
                    sub = "early"
                    res['sub_stage_label_ja'] = "初期"
                    res['entry_quality'] = "ideal"
                    res['entry_comment'] = "ブレイクアウト確認！Stage 2入りの初動であり、本命のエントリーポイントです。"
                    reasons.append("30週線がフラットから上向きへ")
                    reasons.append("直近のレンジを高値で上抜けた")
                else:
                    stage = "Stage 1"
                    res['stage_label_ja'] = "第1段階（底固め）"
                    sub = "late"
                    res['sub_stage_label_ja'] = "後期"
                    res['entry_quality'] = "good"
                    res['entry_comment'] = "Stage 2入り前の有力候補。ブレイクアウト直前の仕込み時、または監視強化の局面です。"
                    res['description'] = "ベース形成が進み、ボラティリティが収縮しています。"
                    reasons.append("30週線がほぼフラット化")
                    reasons.append("価格がレンジ上限付近で推移")
            else:
                if slope > -0.002 and slope < 0.002: # フラット
                    stage = "Stage 1"
                    res['stage_label_ja'] = "第1段階（底固め）"
                    sub = "mid"
                    res['sub_stage_label_ja'] = "中期"
                    res['entry_quality'] = "watch"
                    res['entry_comment'] = "本格的なベース形成中。安値更新が止まり、エネルギーを蓄積している段階です。"
                    res['description'] = "30週線が横ばいになり、方向感を探っている状態です。"
                    reasons.append("30週線が完全にフラット")
                    reasons.append("方向感がなく、レンジ内での推移")
                else:
                    stage = "Stage 3"
                    res['stage_label_ja'] = "第3段階（天井形成）"
                    sub = "mid"
                    res['sub_stage_label_ja'] = "中期"
                    res['entry_quality'] = "avoid"
                    res['entry_comment'] = "天井圏での揉み合い。30週線を割り込んでおり、分配局面の可能性が高いです。"
                    res['description'] = "上昇トレンドが終わり、価格が不安定になっています。"
                    reasons.append("30週線の傾きが消失")
                    reasons.append("価格がMAを頻繁に跨ぎ、サポートが失われている")

        res['stage'] = stage
        res['sub_stage'] = sub
        res['full_label'] = f"{stage} {sub}"
        res['full_label_ja'] = f"{res['stage_label_ja']}・{res['sub_stage_label_ja']}"
        res['reason'] = reasons
        res['trend_status'] = "uptrend" if slope > 0.01 else ("downtrend" if slope < -0.01 else "sideways")
        res['volume_status'] = "above_average" if vol_ratio > 1.2 else ("below_average" if vol_ratio < 0.8 else "normal")
        res['breakout_status'] = "confirmed" if (stage == "Stage 2" and sub == "early") else "none"

        # トレンド継続週数
        count = 0
        tmp_df = df_w.iloc[::-1]
        cur_above = (p > ma30)
        for idx, row in tmp_df.iterrows():
            if pd.isna(row['MA30']): break
            if (row['Close'] > row['MA30']) == cur_above:
                count += 1
            else:
                break
        res['weeks_in_current_trend'] = count

    except Exception as e:
        print(f"WEINSTEIN ERROR: {e}")
        
    return res

# ─────────────────────────────────────────────
# Relative Strength 分析
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_relative_strength_data(ticker: str, sector: str) -> dict | None:
    """銘柄・SPY・セクターETF・QQQ の価格を取得し比較用辞書を返す。"""
    try:
        sector_etf = SECTOR_ETF_MAP.get(sector, "SPY")
        targets = [ticker, "SPY", sector_etf, "QQQ"]
        # 重複除去（sector_etf が SPY と一致する場合など）
        targets = list(dict.fromkeys(targets))

        price_dict: dict[str, pd.Series] = {}
        for t in targets:
            try:
                hist = yf.Ticker(t).history(period="2y", interval="1d")
                if not hist.empty:
                    price_dict[t] = hist["Close"]
            except Exception as e:
                print(f"RS Fetch: {t} skip - {e}")

        if ticker not in price_dict or "SPY" not in price_dict:
            return None

        df = pd.DataFrame(price_dict).ffill().dropna()
        if df.empty:
            return None

        return {
            "df": df,
            "ticker": ticker,
            "sector_etf": sector_etf,
            "sector": sector,
        }
    except Exception as e:
        print(f"RS DATA ERROR: {e}")
        return None


def _period_return(series: pd.Series, days: int) -> float | None:
    """series の末尾 days 個前からの騰落率（%）を返す。不足時は None。"""
    if len(series) <= days:
        return None
    return (series.iloc[-1] / series.iloc[-days] - 1) * 100


def calculate_relative_strength_metrics(rs_data: dict) -> dict:
    """期間別騰落率・超過リターン・RSスコア・RSラインを算出して返す。"""
    empty = {
        "stock_return_1m": None, "stock_return_3m": None,
        "stock_return_6m": None, "stock_return_12m": None,
        "spy_return_1m": None,   "spy_return_3m": None,
        "spy_return_6m": None,   "spy_return_12m": None,
        "sector_return_1m": None,"sector_return_3m": None,
        "sector_return_6m": None,"sector_return_12m": None,
        "excess_vs_spy_1m": None,"excess_vs_spy_3m": None,
        "excess_vs_spy_6m": None,"excess_vs_spy_12m": None,
        "excess_vs_sector_3m": None, "excess_vs_sector_6m": None,
        "rs_score": 0, "rs_status": "neutral",
        "rs_new_high": False, "sector_etf": "SPY",
        "rs_line": None,
    }
    if not rs_data:
        return empty

    df: pd.DataFrame = rs_data["df"]
    ticker: str = rs_data["ticker"]
    sector_etf: str = rs_data["sector_etf"]

    if ticker not in df.columns or "SPY" not in df.columns:
        return empty

    stk = df[ticker]
    spy = df["SPY"]
    sec = df[sector_etf] if sector_etf in df.columns else None

    period_days = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}

    m = {}
    for label, days in period_days.items():
        m[f"stock_return_{label}"] = _period_return(stk, days)
        m[f"spy_return_{label}"]   = _period_return(spy, days)
        m[f"sector_return_{label}"] = _period_return(sec, days) if sec is not None else None

        sr  = m[f"stock_return_{label}"]
        spr = m[f"spy_return_{label}"]
        secr = m[f"sector_return_{label}"]
        m[f"excess_vs_spy_{label}"] = (sr - spr) if (sr is not None and spr is not None) else None
        if label in ("3m", "6m"):
            m[f"excess_vs_sector_{label}"] = (sr - secr) if (sr is not None and secr is not None) else None

    # ── RSライン（株価 / SPY 比率）を直近1年分で計算 ──────────────
    recent_stk = stk.iloc[-252:] if len(stk) > 252 else stk
    recent_spy = spy.reindex(recent_stk.index).ffill()
    rs_line = (recent_stk / recent_spy) * 100   # 100基準化
    rs_line_norm = (rs_line / rs_line.iloc[0]) * 100  # 起点100に正規化
    m["rs_line"] = rs_line_norm

    # RSライン直近新高値判定（直近4週が過去1年の最高値か）
    if len(rs_line_norm) > 20:
        peak_prev = rs_line_norm.iloc[:-20].max()
        recent_max = rs_line_norm.iloc[-20:].max()
        m["rs_new_high"] = bool(recent_max >= peak_prev)
    else:
        m["rs_new_high"] = False

    # ── RSスコア計算（0〜100）──────────────────────────────────
    score = 0
    ex = {k: m.get(k) for k in [
        "excess_vs_spy_1m", "excess_vs_spy_3m", "excess_vs_spy_6m", "excess_vs_spy_12m",
        "excess_vs_sector_3m", "excess_vs_sector_6m",
    ]}

    # 対SPY
    if ex["excess_vs_spy_1m"]  is not None and ex["excess_vs_spy_1m"]  > 0: score += 10
    if ex["excess_vs_spy_3m"]  is not None and ex["excess_vs_spy_3m"]  > 0: score += 20
    if ex["excess_vs_spy_6m"]  is not None and ex["excess_vs_spy_6m"]  > 0: score += 20
    if ex["excess_vs_spy_12m"] is not None and ex["excess_vs_spy_12m"] > 0: score += 15
    # 対セクター
    if ex["excess_vs_sector_3m"] is not None and ex["excess_vs_sector_3m"] > 0: score += 15
    if ex["excess_vs_sector_6m"] is not None and ex["excess_vs_sector_6m"] > 0: score += 10
    # RSライン新高値ボーナス
    if m["rs_new_high"]: score += 10

    score = min(100, max(0, score))

    # ── ステータス判定 ──
    if score >= 65:
        rs_status = "strong"
    elif score >= 35:
        rs_status = "neutral"
    else:
        rs_status = "weak"

    m["rs_score"]  = score
    m["rs_status"] = rs_status
    m["sector_etf"] = sector_etf

    return m

# ─────────────────────────────────────────────
# エントリータイミング分析（週足 × 日足 整合判定）
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_entry_timing_price_data(ticker: str) -> pd.DataFrame:
    """日足価格データを約1年分取得して返す。"""
    try:
        hist = yf.Ticker(ticker).history(period="1y", interval="1d")
        if hist.empty:
            return pd.DataFrame()
        return hist[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception as e:
        print(f"ENTRY TIMING FETCH ERROR: {e}")
        return pd.DataFrame()


def _calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """シンプルなEMA平滑RSI。"""
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def calculate_entry_timing_indicators(daily_df: pd.DataFrame) -> pd.DataFrame:
    """日足DataFrameに各種テクニカル指標列を追加して返す。"""
    if daily_df.empty or len(daily_df) < 55:
        return daily_df
    df = daily_df.copy()
    df["MA20"]  = df["Close"].rolling(20).mean()
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA5"]   = df["Close"].rolling(5).mean()
    df["VOL_MA20"] = df["Volume"].rolling(20).mean()
    df["HIGH_20"]  = df["High"].rolling(20).max()
    df["HIGH_50"]  = df["High"].rolling(50).max()
    df["LOW_20"]   = df["Low"].rolling(20).min()
    df["RSI"] = _calc_rsi(df["Close"])
    # ATR
    hl = df["High"] - df["Low"]
    hcp = (df["High"] - df["Close"].shift()).abs()
    lcp = (df["Low"] - df["Close"].shift()).abs()
    df["ATR"] = pd.concat([hl, hcp, lcp], axis=1).max(axis=1).rolling(14).mean()
    # 乖離率
    df["PRICE_VS_MA20"] = (df["Close"] / df["MA20"] - 1) * 100
    df["PRICE_VS_MA50"] = (df["Close"] / df["MA50"] - 1) * 100
    df["PRICE_VS_MA5"]  = (df["Close"] / df["MA5"]  - 1) * 100
    df["VOLUME_RATIO"]  = df["Volume"] / df["VOL_MA20"].replace(0, 1)
    return df


def evaluate_daily_entry_setup(daily_df: pd.DataFrame) -> dict:
    """日足の指標だけ見てエントリーパターンと日足スコアを返す。"""
    base = {
        "daily_setup": "unknown",
        "daily_setup_label_ja": "不明",
        "daily_score": 0,
        "breakout_confirmed": False,
        "pullback_ready": False,
        "overextended": False,
        "risk_flag": False,
        "reason": [],
    }
    df = calculate_entry_timing_indicators(daily_df)
    if df.empty or len(df) < 55:
        base["reason"].append("データ不足")
        return base

    last = df.iloc[-1]
    prev_high_20 = df["High"].iloc[-21:-1].max() if len(df) > 21 else last["High"]

    price    = last["Close"]
    ma20     = last["MA20"]
    ma50     = last["MA50"]
    ma5      = last["MA5"]
    vol_r    = last["VOLUME_RATIO"]
    rsi      = last["RSI"]
    vs_ma20  = last["PRICE_VS_MA20"]
    vs_ma50  = last["PRICE_VS_MA50"]
    high_20  = last["HIGH_20"]
    low_20   = last["LOW_20"]
    atr      = last["ATR"]

    reason = []
    score = 50  # 中立ベース

    # ─── 基本ポジション条件 ───
    above_ma20 = price > ma20
    above_ma50 = price > ma50
    golden_cross = ma20 > ma50

    if above_ma50:
        score += 8
        reason.append("株価が50日線の上で推移")
    else:
        score -= 15
        reason.append("株価が50日線を下回る（弱気）")

    if above_ma20:
        score += 5
        reason.append("株価が20日線の上で推移")
    else:
        score -= 8
        reason.append("株価が20日線を下回る")

    if golden_cross:
        score += 8
        reason.append("20日線 > 50日線（ゴールデン配列）")
    else:
        score -= 5
        reason.append("20日線 < 50日線（デッドクロス）")

    # ─── ブレイクアウト確認 ───
    breakout = price >= prev_high_20 and vol_r >= 1.2
    if breakout:
        score += 15
        reason.append(f"直近高値ブレイクを出来高増（{vol_r:.1f}x）で確認")
        base["breakout_confirmed"] = True
    elif price >= prev_high_20 and vol_r < 1.2:
        score += 5
        reason.append("高値付近だが出来高が伴っていない（弱いブレイク）")
    else:
        score -= 3
        reason.append("直近高値ブレイクはまだ確認されていない")

    # ─── 押し目反発確認 ───
    near_ma20 = abs(vs_ma20) < 3.0
    near_ma50 = abs(vs_ma50) < 5.0
    rebounding = price > ma20 and df["Close"].iloc[-3:].is_monotonic_increasing
    if not breakout and above_ma50 and (near_ma20 or near_ma50) and rebounding:
        score += 12
        reason.append("20日/50日線付近からの健全な押し目反発")
        base["pullback_ready"] = True

    # ─── 伸び切り（過熱）確認 ───
    overex = vs_ma50 > 20 or rsi > 78 or (atr > 0 and (price - prev_high_20) / atr > 3)
    if overex:
        score -= 18
        reason.append(f"50日線乖離 {vs_ma50:.1f}% or RSI {rsi:.0f} — 過熱の可能性")
        base["overextended"] = True

    # ─── ブレイク失敗リスク ───
    recent_closes = df["Close"].iloc[-5:].values
    fail_risk = bool(above_ma20 == False and price < low_20)
    if fail_risk:
        score -= 20
        reason.append("直近安値を割り込んでいる（ブレイク失敗リスク）")
        base["risk_flag"] = True

    # 出来高トレンド
    if vol_r >= 1.5:
        score += 5
        reason.append(f"出来高が平均の {vol_r:.1f}倍（資金流入）")
    elif vol_r < 0.7:
        score -= 5
        reason.append("出来高が乾いている（関心薄）")

    # ─── パターン分類 ───
    score = max(0, min(100, score))

    if fail_risk or (not above_ma50 and not above_ma20 and not golden_cross):
        setup, label = "broken", "崩れ型"
    elif overex and not breakout:
        setup, label = "overextended", "伸び切り型"
    elif breakout:
        setup, label = "breakout", "ブレイクアウト型"
    elif base["pullback_ready"]:
        setup, label = "pullback", "押し目型"
    elif above_ma50 and not breakout:
        setup, label = "watch", "未確認型"
    else:
        setup, label = "watch", "監視型"

    base.update({
        "daily_setup": setup,
        "daily_setup_label_ja": label,
        "daily_score": score,
        "reason": reason,
    })
    return base


def evaluate_entry_timing(ticker: str, weekly_stage: dict) -> dict:
    """週足ステージ分析と日足エントリー判定を統合し、最終エントリー評価を返す。"""
    fallback = {
        "entry_status": "watch",
        "entry_status_label_ja": "監視",
        "entry_timing_score": 30,
        "timeframe_alignment": "misaligned",
        "timeframe_alignment_label_ja": "不整合",
        "entry_comment": "データ不足のため判断できません。",
        "weekly_summary": "—",
        "daily_summary": "—",
        "daily_detail": {},
    }

    # 日足データ取得と指標計算
    daily_df = fetch_entry_timing_price_data(ticker)
    if daily_df.empty:
        return fallback

    daily = evaluate_daily_entry_setup(daily_df)

    w_stage  = weekly_stage.get("stage", "Unknown")
    w_sub    = weekly_stage.get("sub_stage", "unknown")
    w_quality = weekly_stage.get("entry_quality", "avoid")
    d_setup  = daily.get("daily_setup", "unknown")
    d_score  = daily.get("daily_score", 30)

    # ─── 週足評価点 ───
    weekly_score = 0
    if w_stage == "Stage 2":
        if w_sub == "early":   weekly_score = 90
        elif w_sub == "mid":   weekly_score = 70
        elif w_sub == "late":  weekly_score = 45
    elif w_stage == "Stage 1":
        if w_sub == "late":    weekly_score = 55
        else:                  weekly_score = 25
    elif w_stage == "Stage 3":
        if w_sub == "early":   weekly_score = 30
        else:                  weekly_score = 10
    elif w_stage == "Stage 4":
        weekly_score = 5
    else:
        weekly_score = 20

    # ─── 整合性判定 ───
    bullish_weekly = w_stage == "Stage 2" or (w_stage == "Stage 1" and w_sub == "late")
    bearish_weekly = w_stage in ("Stage 3", "Stage 4")
    bullish_daily  = d_setup in ("breakout", "pullback")
    bearish_daily  = d_setup == "broken"

    if bullish_weekly and bullish_daily:
        alignment = "aligned"; align_ja = "整合（両方向き）"
    elif bullish_weekly and d_setup in ("watch", "overextended"):
        alignment = "partially_aligned"; align_ja = "部分整合（週足は良好・日足は条件待ち）"
    elif bullish_weekly and bearish_daily:
        alignment = "misaligned"; align_ja = "不整合（週足は良好・日足が崩れ）"
    elif bearish_weekly and bullish_daily:
        alignment = "misaligned"; align_ja = "不整合（日足だけ反発・週足は下降）"
    else:
        alignment = "partially_aligned" if not bearish_weekly else "misaligned"
        align_ja = "部分整合" if not bearish_weekly else "不整合"

    # ─── 総合スコア ───
    raw_score = weekly_score * 0.55 + d_score * 0.45
    if alignment == "aligned":       raw_score = min(100, raw_score + 10)
    elif alignment == "misaligned":  raw_score = max(0,   raw_score - 15)
    timing_score = int(round(max(0, min(100, raw_score))))

    # ─── エントリーステータス ───
    if alignment == "aligned" and bullish_weekly and d_setup == "breakout" and timing_score >= 65:
        status = "buy_now"; status_ja = "今すぐ買い"
    elif bullish_weekly and d_setup == "pullback" and alignment in ("aligned", "partially_aligned"):
        status = "buy_on_pullback"; status_ja = "押し目なら買い"
    elif alignment == "misaligned" or bearish_weekly or d_setup == "broken":
        status = "avoid"; status_ja = "見送り"
    else:
        status = "watch"; status_ja = "監視"

    # ─── コメント生成 ───
    comment_map = {
        ("buy_now",        "aligned"):           f"週足 {w_stage}/{w_sub}・日足ブレイクアウト確認済み。エントリーに踏み切りやすいタイミング。",
        ("buy_on_pullback","aligned"):           f"週足 {w_stage}/{w_sub}・日足は押し目からの反発。健全な調整後の買いタイミング。",
        ("buy_on_pullback","partially_aligned"): f"週足は {w_stage}（{w_sub}）で良好。日足はまだ条件待ち。押し目が確認できれば買い検討可。",
        ("watch",          "partially_aligned"): f"週足は {w_stage} だが日足の執行条件は未確認。ブレイクまたは押し目反発を待ちたい。",
        ("watch",          "misaligned"):        "週足と日足の方向が一致していない。無理に新規参入する局面ではない。",
        ("avoid",          "misaligned"):        f"週足 {w_stage}（{w_sub}）で大局が弱く、日足も崩れている。新規エントリーは推奨しない。",
    }
    entry_comment = comment_map.get(
        (status, alignment),
        f"週足 {w_stage}/{w_sub} × 日足 {daily.get('daily_setup_label_ja')} — 慎重に状況確認。"
    )

    return {
        "entry_status":              status,
        "entry_status_label_ja":     status_ja,
        "entry_timing_score":        timing_score,
        "timeframe_alignment":       alignment,
        "timeframe_alignment_label_ja": align_ja,
        "entry_comment":             entry_comment,
        "weekly_summary":            f"{w_stage} / {w_sub} ({w_quality})",
        "daily_summary":             daily.get("daily_setup_label_ja", "—"),
        "daily_detail":              daily,
    }



# ─────────────────────────────────────────────
# 決算品質分析 (Earnings Quality Analysis)
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_earnings_quality_data(ticker: str) -> dict | None:
    """決算品質分析に必要な四半期財務・株価データを収集して返す。"""
    try:
        stock = yf.Ticker(ticker)

        # ── 四半期財務（損益計算書 + CF）──────────────
        q_inc = stock.quarterly_financials
        q_cf  = stock.quarterly_cashflow
        q_bs  = stock.quarterly_balance_sheet

        if q_inc is None or q_inc.empty:
            return None

        q_inc = q_inc.T.sort_index()
        q_cf  = q_cf.T.sort_index()  if (q_cf  is not None and not q_cf.empty)  else pd.DataFrame()
        q_bs  = q_bs.T.sort_index()  if (q_bs  is not None and not q_bs.empty)  else pd.DataFrame()

        def _pick(df: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
            for c in candidates:
                if c in df.columns:
                    return pd.to_numeric(df[c], errors="coerce")
            return None

        rev  = _pick(q_inc, ["Total Revenue", "TotalRevenue", "Operating Revenue"])
        ni   = _pick(q_inc, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
        op   = _pick(q_inc, ["Operating Income", "OperatingIncome", "EBIT"])
        ocf  = _pick(q_cf,  ["Operating Cash Flow", "OperatingCashFlow",
                               "Total Cash From Operating Activities"])
        capex= _pick(q_cf,  ["Capital Expenditure", "CapitalExpenditure",
                               "Capital Expenditures"])

        # FCF = OCF - CapEx (CapExはマイナス値で格納されることが多い)
        fcf_series = None
        if ocf is not None and capex is not None:
            capex_abs = capex.abs()
            fcf_series = ocf - capex_abs

        # ── 決算日リスト ────────────────────────────────
        eq_dates = []
        try:
            cal = stock.calendar
            if cal is not None and not cal.empty:
                # yfinance の calendar はバージョンで形式が違う
                for col in ["Earnings Date", "earningsDate"]:
                    if col in cal.index:
                        dt = cal.loc[col].values[0]
                        if hasattr(dt, "date"):
                            eq_dates.append(dt.date())
        except Exception:
            pass

        # earnings_dates が取れなければ quarterly_financials の列日付を利用
        if not eq_dates:
            eq_dates = [d.date() for d in q_inc.index[-4:]]

        # ── 日足価格（1.5年分）──────────────────────────
        hist = stock.history(period="18mo", interval="1d")
        hist = hist[["Open", "High", "Low", "Close", "Volume"]].dropna() if not hist.empty else pd.DataFrame()

        return {
            "ticker": ticker,
            "rev":    rev,
            "ni":     ni,
            "op":     op,
            "ocf":    ocf,
            "capex":  capex,
            "fcf":    fcf_series,
            "q_dates": list(q_inc.index),
            "eq_dates": eq_dates,
            "hist":   hist,
        }
    except Exception as e:
        print(f"EQ FETCH ERROR: {e}")
        return None


def _growth(series: pd.Series, lag: int = 4) -> float | None:
    """lag 期前比の成長率(%)を返す。YoY=4, QoQ=1。"""
    if series is None or len(series) < lag + 1:
        return None
    old = series.iloc[-(lag + 1)]
    new = series.iloc[-1]
    if pd.isna(old) or pd.isna(new) or old == 0:
        return None
    return (new / old - 1) * 100


def _margin(rev: pd.Series | None, profit: pd.Series | None) -> float | None:
    """最新四半期の利益率(%)を返す。"""
    if rev is None or profit is None:
        return None
    r = rev.iloc[-1]; p = profit.iloc[-1]
    if pd.isna(r) or pd.isna(p) or r == 0:
        return None
    return (p / r) * 100


def _post_earnings_reaction(hist: pd.DataFrame, eq_date) -> dict:
    """決算日の翌営業日からの価格反応を計算する。"""
    empty = {"ret_1d": None, "ret_5d": None, "vol_ratio": None}
    if hist.empty or eq_date is None:
        return empty
    try:
        import datetime
        if isinstance(eq_date, datetime.datetime):
            eq_date = eq_date.date()
        idx = hist.index
        idx_dates = [d.date() if hasattr(d, "date") else d for d in idx]

        # 決算日以降の最初の取引日
        after = [i for i, d in enumerate(idx_dates) if d > eq_date]
        if not after:
            return empty

        i0 = after[0]
        p0 = hist["Close"].iloc[i0 - 1] if i0 > 0 else hist["Close"].iloc[i0]  # 直前終値
        p1 = hist["Close"].iloc[i0]       # 翌日終値
        p5 = hist["Close"].iloc[min(i0 + 4, len(hist) - 1)]  # 5日後終値

        ret_1d = (p1 / p0 - 1) * 100 if p0 != 0 else None
        ret_5d = (p5 / p0 - 1) * 100 if p0 != 0 else None

        vol_avg = hist["Volume"].iloc[max(0, i0 - 20):i0].mean()
        vol_day = hist["Volume"].iloc[i0]
        vol_ratio = vol_day / vol_avg if vol_avg > 0 else None

        return {"ret_1d": ret_1d, "ret_5d": ret_5d, "vol_ratio": vol_ratio}
    except Exception as e:
        print(f"POST EARNINGS ERR: {e}")
        return empty


def calculate_earnings_quality(eq_data: dict) -> dict:
    """四半期財務データを評価し earnings_quality_score と各指標を返す。"""
    fallback = {
        "earnings_quality_score": 0,
        "earnings_quality_status": "neutral",
        "summary_label_ja": "データ不足",
        "revenue_growth_pct": None, "net_income_growth_pct": None,
        "operating_cf_growth_pct": None, "margin_trend": "unknown",
        "margin_trend_label_ja": "判定不能", "fcf_trend": "unknown",
        "post_earnings_1d_return_pct": None, "post_earnings_5d_return_pct": None,
        "post_earnings_volume_ratio": None, "earnings_reaction": "unknown",
        "quality_flags": [], "risk_flags": [],
        "comment": "データが取得できませんでした。",
    }
    if not eq_data:
        return fallback

    rev   = eq_data.get("rev")
    ni    = eq_data.get("ni")
    op    = eq_data.get("op")
    ocf   = eq_data.get("ocf")
    fcf   = eq_data.get("fcf")
    hist  = eq_data.get("hist", pd.DataFrame())
    eq_dates = eq_data.get("eq_dates", [])

    # ── 成長率計算（YoY: lag=4） ────────────────────────
    rev_g  = _growth(rev,  4)
    ni_g   = _growth(ni,   4)
    ocf_g  = _growth(ocf,  4)
    fcf_g  = _growth(fcf,  4)

    # ── 利益率トレンド（直近2四半期で比較） ─────────────
    margin_now  = _margin(rev, ni)
    margin_prev = None
    if rev is not None and ni is not None and len(rev) >= 5 and len(ni) >= 5:
        rev_prev = rev.iloc[:-1]
        ni_prev  = ni.iloc[:-1]
        margin_prev = _margin(rev_prev, ni_prev)

    if margin_now is not None and margin_prev is not None:
        margin_delta = margin_now - margin_prev
        if margin_delta > 0.5:
            margin_trend    = "improving"
            margin_trend_ja = f"利益率改善 ({margin_delta:+.1f}pp)"
        elif margin_delta < -0.5:
            margin_trend    = "deteriorating"
            margin_trend_ja = f"利益率悪化 ({margin_delta:+.1f}pp)"
        else:
            margin_trend    = "stable"
            margin_trend_ja = "利益率横ばい"
    else:
        margin_trend    = "unknown"
        margin_trend_ja = "判定不能"

    # ── FCFトレンド ────────────────────────────────────
    if fcf_g is not None:
        fcf_trend = "improving" if fcf_g > 5 else ("deteriorating" if fcf_g < -5 else "stable")
    else:
        fcf_trend = "unknown"

    # ── 決算後株価反応（直近決算日を使用）────────────────
    latest_eq_date = eq_dates[-1] if eq_dates else None
    reaction = _post_earnings_reaction(hist, latest_eq_date)
    ret_1d  = reaction["ret_1d"]
    ret_5d  = reaction["ret_5d"]
    vol_r   = reaction["vol_ratio"]

    if ret_1d is not None:
        if ret_1d >= 3:
            er = "strongly_positive"
        elif ret_1d >= 0.5:
            er = "positive"
        elif ret_1d <= -3:
            er = "strongly_negative"
        elif ret_1d <= -0.5:
            er = "negative"
        else:
            er = "neutral"
    else:
        er = "unknown"

    # ── スコアリング（0〜100、ベース50） ─────────────────
    score = 50
    quality_flags: list[str] = []
    risk_flags:    list[str] = []

    # 売上成長
    if rev_g is not None:
        if rev_g >= 20:   score += 12; quality_flags.append(f"売上高成長 +{rev_g:.1f}% (YoY)")
        elif rev_g >= 10: score +=  7; quality_flags.append(f"売上高成長 +{rev_g:.1f}% (YoY)")
        elif rev_g >= 0:  score +=  2
        else:             score -= 10; risk_flags.append(f"売上高が前年同期比で減少 ({rev_g:.1f}%)")

    # 純利益成長
    if ni_g is not None:
        if ni_g >= 25:    score += 12; quality_flags.append(f"純利益成長 +{ni_g:.1f}% (YoY)")
        elif ni_g >= 10:  score +=  7; quality_flags.append(f"純利益成長 +{ni_g:.1f}% (YoY)")
        elif ni_g >= 0:   score +=  2
        else:             score -=  8; risk_flags.append(f"純利益が前年同期比で減少 ({ni_g:.1f}%)")
    # 赤字→黒字ボーナス
    if ni is not None and len(ni) >= 5:
        if ni.iloc[-5] < 0 < ni.iloc[-1]:
            score += 8; quality_flags.append("赤字→黒字転換を達成")

    # 営業CF
    if ocf_g is not None:
        if ocf_g >= 15:   score +=  8; quality_flags.append(f"営業CF改善 +{ocf_g:.1f}% (YoY)")
        elif ocf_g >= 0:  score +=  3
        else:             score -=  5; risk_flags.append(f"営業CFが前年同期比で悪化 ({ocf_g:.1f}%)")

    # 利益率トレンド
    if margin_trend == "improving":
        score +=  8; quality_flags.append(margin_trend_ja)
    elif margin_trend == "deteriorating":
        score -=  8; risk_flags.append(margin_trend_ja)

    # FCF
    if fcf_trend == "improving":
        score +=  5; quality_flags.append("FCF改善トレンド")
    elif fcf_trend == "deteriorating":
        score -=  4; risk_flags.append("FCF悪化傾向")
    elif fcf_trend == "unknown":
        risk_flags.append("FCFデータが取得できません")

    # 成長の質チェック（売上↑でも利益↓は減点）
    if rev_g is not None and ni_g is not None:
        if rev_g > 10 and ni_g < 0:
            score -= 6; risk_flags.append("売上は伸びているが利益が減少（利益率悪化懸念）")
        elif rev_g > 5 and ni_g > rev_g:
            score += 4; quality_flags.append("利益成長が売上成長を上回る（レバレッジ効果）")

    # 決算後市場反応
    if er == "strongly_positive":
        score += 10; quality_flags.append(f"決算翌日に強い上昇 +{ret_1d:.1f}%（市場が好感）")
    elif er == "positive":
        score +=  5; quality_flags.append(f"決算翌日に上昇 +{ret_1d:.1f}%")
    elif er == "strongly_negative":
        score -= 12; risk_flags.append(f"決算翌日に大幅下落 {ret_1d:.1f}%（市場が失望）")
    elif er == "negative":
        score -=  5; risk_flags.append(f"決算翌日に下落 {ret_1d:.1f}%")

    # 決算後5日
    if ret_5d is not None:
        if ret_5d >= 5:   score +=  5; quality_flags.append(f"決算後5日でも上昇継続 +{ret_5d:.1f}%")
        elif ret_5d < -5: score -=  5; risk_flags.append(f"決算後5日間でも下落 {ret_5d:.1f}%")

    # 出来高反応
    if vol_r is not None:
        if vol_r >= 2.0:  quality_flags.append(f"決算翌日の出来高が平均の {vol_r:.1f}倍（強い資金流入）")
        elif vol_r < 0.8: risk_flags.append("決算翌日の出来高が少ない（関心薄）")

    score = max(0, min(100, score))

    # ── ステータス判定 ─────────────────────────────────
    if score >= 70:
        status = "strong";  status_ja = "決算品質は高い"
    elif score >= 45:
        status = "neutral"; status_ja = "決算品質は平均的"
    else:
        status = "weak";    status_ja = "決算品質に懸念あり"

    # ── コメント生成 ────────────────────────────────────
    parts = []
    if rev_g is not None and rev_g > 10:
        parts.append(f"売上+{rev_g:.1f}%と力強い成長")
    if ni_g is not None and ni_g > 10:
        parts.append(f"純利益+{ni_g:.1f}%で利益も拡大")
    if margin_trend == "improving":
        parts.append("利益率も改善傾向")
    if er in ("positive", "strongly_positive"):
        parts.append("市場の受け止めも良好")
    if er in ("negative", "strongly_negative"):
        parts.append("ただし市場反応はネガティブで慎重評価が必要")
    comment = "。".join(parts) + "。" if parts else "詳細な評価には追加のデータが必要です。"

    return {
        "earnings_quality_score":     score,
        "earnings_quality_status":    status,
        "summary_label_ja":           status_ja,
        "revenue_growth_pct":         rev_g,
        "net_income_growth_pct":      ni_g,
        "operating_cf_growth_pct":    ocf_g,
        "fcf_growth_pct":             fcf_g,
        "margin_trend":               margin_trend,
        "margin_trend_label_ja":      margin_trend_ja,
        "margin_latest_pct":          margin_now,
        "fcf_trend":                  fcf_trend,
        "post_earnings_1d_return_pct": ret_1d,
        "post_earnings_5d_return_pct": ret_5d,
        "post_earnings_volume_ratio":  vol_r,
        "earnings_reaction":           er,
        "quality_flags":               quality_flags,
        "risk_flags":                  risk_flags,
        "comment":                     comment,
        # UI チャート用
        "_rev":  rev,
        "_ni":   ni,
        "_ocf":  ocf,
        "_q_dates": eq_data.get("q_dates", []),
    }


# ─────────────────────────────────────────────
# 需給分析 (Supply / Demand Analysis)
# ─────────────────────────────────────────────

@st.cache_data(ttl=1800)
def fetch_supply_demand_extended(ticker: str) -> dict:
    """fetch_supply_demand_data を拡張し、出来高スコア算出に必要な日足データも取得する。"""
    base = fetch_supply_demand_data(ticker)
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        # 追加: floatShares, sharesOutstanding
        base["float_shares"]    = info.get("floatShares")
        base["shares_outstanding"] = info.get("sharesOutstanding")
        base["avg_volume_10d"]  = info.get("averageVolume10days") or info.get("averageDailyVolume10Day")
        base["avg_volume_3m"]   = info.get("averageVolume")

        # 日足価格・出来高（1年分）
        hist = stock.history(period="1y", interval="1d")
        if not hist.empty:
            base["hist"] = hist[["Open", "High", "Low", "Close", "Volume"]].dropna()
        else:
            base["hist"] = pd.DataFrame()
    except Exception as e:
        print(f"SD EXTENDED ERROR: {e}")
        base.setdefault("hist", pd.DataFrame())
    return base


def calculate_supply_demand_score(sd_data: dict) -> dict:
    """需給スコアと各指標を集約して返す。"""
    fallback = {
        "supply_demand_score": 0,
        "supply_demand_status": "neutral",
        "summary_label_ja": "データ不足",
        "institutional_ownership_pct": None,
        "institutional_support": "unknown",
        "short_float_pct": None,
        "days_to_cover": None,
        "short_squeeze_potential": "unknown",
        "insider_bias": "neutral",
        "insider_bias_label_ja": "データなし",
        "volume_ratio_20d": None,
        "up_volume_strength": "unknown",
        "quality_flags": [],
        "risk_flags": [],
        "comment": "データが取得できませんでした。",
    }
    if not sd_data:
        return fallback

    quality_flags: list[str] = []
    risk_flags:    list[str] = []
    score = 50  # ベース

    # ── 1. 機関保有比率 ───────────────────────────────────
    inst_raw = sd_data.get("inst_ownership")
    inst_pct = round(inst_raw * 100, 1) if inst_raw is not None else None

    if inst_pct is not None:
        if inst_pct >= 70:
            score += 10; quality_flags.append(f"機関保有比率が高い ({inst_pct:.1f}%) — 安定した買い手基盤")
            inst_support = "strong"
        elif inst_pct >= 40:
            score +=  5; quality_flags.append(f"機関保有比率は中程度 ({inst_pct:.1f}%)")
            inst_support = "moderate"
        elif inst_pct >= 10:
            score -=  0; inst_support = "low"
        else:
            score -=  5; risk_flags.append(f"機関保有比率が低い ({inst_pct:.1f}%) — 機関の支えが弱い")
            inst_support = "weak"
    else:
        inst_support = "unknown"

    # ── 2. 空売り評価 ────────────────────────────────────
    short_float = sd_data.get("short_float")
    short_ratio = sd_data.get("short_ratio")
    short_pct   = round(short_float * 100, 1) if short_float is not None else None
    dtc         = round(short_ratio, 1)        if short_ratio is not None else None

    squeeze_potential = "unknown"
    if short_pct is not None:
        if short_pct >= 20:
            score += 8; quality_flags.append(f"空売り比率が高い ({short_pct:.1f}%) — 踏み上げ余地が大きい")
            squeeze_potential = "high"
        elif short_pct >= 10:
            score += 3; quality_flags.append(f"空売り比率が中程度 ({short_pct:.1f}%) — 踏み上げ余地あり")
            squeeze_potential = "medium"
        elif short_pct >= 5:
            score +=  0; squeeze_potential = "low"
        else:
            score -=  3; risk_flags.append(f"空売り比率が低い ({short_pct:.1f}%) — 踏み上げによる上昇は期待薄")
            squeeze_potential = "minimal"

    if dtc is not None:
        if dtc >= 5:
            score += 5; quality_flags.append(f"Days to Cover: {dtc:.1f}日 — 踏み上げ時の上昇インパクトが大きい")
        elif dtc <= 1:
            score -= 3; risk_flags.append(f"Days to Cover: {dtc:.1f}日 — ショートカバーは短期間で済む")

    # ── 3. インサイダー売買バイアス ──────────────────────
    insider_df = sd_data.get("insider_trades", pd.DataFrame())
    insider_bias   = "neutral"
    insider_bias_ja = "インサイダー中立"

    if insider_df is not None and not insider_df.empty and "Side" in insider_df.columns:
        try:
            # 直近3ヶ月に絞る
            cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=90)
            if "Date" in insider_df.columns:
                recent = insider_df[pd.to_datetime(insider_df["Date"], utc=True) >= cutoff]
            else:
                recent = insider_df

            buy_cnt  = int((recent["Side"] == "Buy").sum())
            sell_cnt = int((recent["Side"] == "Sell").sum())
            total    = buy_cnt + sell_cnt

            if total > 0:
                buy_ratio = buy_cnt / total
                if buy_ratio >= 0.6:
                    score += 8; insider_bias = "buying"; insider_bias_ja = "インサイダー買い優勢"
                    quality_flags.append(f"インサイダー買い優勢 (直近3ヶ月: 買{buy_cnt}件 / 売{sell_cnt}件)")
                elif buy_ratio <= 0.3:
                    score -= 8; insider_bias = "selling"; insider_bias_ja = "インサイダー売り優勢"
                    risk_flags.append(f"インサイダー売り優勢 (直近3ヶ月: 買{buy_cnt}件 / 売{sell_cnt}件)")
                else:
                    insider_bias = "mixed"; insider_bias_ja = "インサイダー売買混在"
        except Exception:
            pass

    # ── 4. 出来高分析 ──────────────────────────────────
    hist = sd_data.get("hist", pd.DataFrame())
    volume_ratio_20d = None
    up_vol_strength  = "unknown"

    if not hist.empty and len(hist) >= 25:
        vol   = hist["Volume"]
        close = hist["Close"]

        vol_ma20 = vol.rolling(20).mean()
        vol_ma50 = vol.rolling(50).mean() if len(hist) >= 55 else None

        last_vol   = vol.iloc[-1]
        last_ma20  = vol_ma20.iloc[-1]
        volume_ratio_20d = round(last_vol / last_ma20, 2) if last_ma20 > 0 else None

        # 直近20日の上昇日/下落日出来高比
        ret_20 = close.iloc[-20:].pct_change().fillna(0)
        volumes_20 = vol.iloc[-20:]
        up_days   = volumes_20[ret_20 > 0]
        down_days = volumes_20[ret_20 <= 0]
        up_vol_avg   = up_days.mean()   if len(up_days)   > 0 else 0
        down_vol_avg = down_days.mean() if len(down_days) > 0 else 1

        up_down_ratio = up_vol_avg / down_vol_avg if down_vol_avg > 0 else 1.0

        if up_down_ratio >= 1.5:
            score += 10; quality_flags.append(f"上昇日の出来高が下落日の {up_down_ratio:.1f}倍 — 需給改善")
            up_vol_strength = "strong"
        elif up_down_ratio >= 1.1:
            score +=  5; quality_flags.append("上昇日の出来高が下落日をやや上回る")
            up_vol_strength = "moderate"
        elif up_down_ratio < 0.8:
            score -=  8; risk_flags.append(f"下落日の出来高が上昇日の {1/up_down_ratio:.1f}倍 — 需給悪化")
            up_vol_strength = "weak"
        else:
            up_vol_strength = "neutral"

        # 直近出来高倍率スコア
        if volume_ratio_20d is not None:
            if volume_ratio_20d >= 2.0:
                score += 8; quality_flags.append(f"直近出来高が20日平均の {volume_ratio_20d:.1f}倍（強い資金流入）")
            elif volume_ratio_20d >= 1.3:
                score += 4
            elif volume_ratio_20d < 0.6:
                score -= 4; risk_flags.append(f"直近出来高が低調 ({volume_ratio_20d:.1f}x) — 市場の関心が薄れている")

        # 出来高トレンド（直近10日 vs 11〜20日前）
        vol_recent  = vol.iloc[-10:].mean()
        vol_earlier = vol.iloc[-20:-10].mean()
        if vol_earlier > 0:
            vol_trend_chg = (vol_recent / vol_earlier - 1) * 100
            if vol_trend_chg >= 20:
                score += 5; quality_flags.append(f"出来高が増加トレンド（直近10日平均が前期比 +{vol_trend_chg:.0f}%）")
            elif vol_trend_chg <= -20:
                score -= 4; risk_flags.append(f"出来高が減少トレンド（直近10日平均が前期比 {vol_trend_chg:.0f}%）")

    score = max(0, min(100, score))

    # ── ステータス ─────────────────────────────────────
    if score >= 68:
        status = "strong";  status_ja = "需給は良好"
    elif score >= 42:
        status = "neutral"; status_ja = "需給は中立"
    else:
        status = "weak";    status_ja = "需給に懸念あり"

    # ── コメント ───────────────────────────────────────
    parts = []
    if inst_support == "strong":
        parts.append("機関投資家の強いサポートがある")
    if squeeze_potential in ("high", "medium"):
        parts.append("空売り圧力による踏み上げ余地がある")
    if insider_bias == "buying":
        parts.append("インサイダーの買いが優勢")
    if up_vol_strength == "strong":
        parts.append("出来高を伴った上昇で需給改善")
    if insider_bias == "selling":
        parts.append("ただしインサイダーの売りに注意")
    if up_vol_strength == "weak":
        parts.append("出来高面では需給が弱い")
    comment = "、".join(parts) + "。" if parts else "総合的に判断可能なデータが限られています。"

    return {
        "supply_demand_score":        score,
        "supply_demand_status":       status,
        "summary_label_ja":           status_ja,
        "institutional_ownership_pct": inst_pct,
        "institutional_support":      inst_support,
        "short_float_pct":            short_pct,
        "days_to_cover":              dtc,
        "short_squeeze_potential":    squeeze_potential,
        "insider_bias":               insider_bias,
        "insider_bias_label_ja":      insider_bias_ja,
        "volume_ratio_20d":           volume_ratio_20d,
        "up_volume_strength":         up_vol_strength,
        "quality_flags":              quality_flags,
        "risk_flags":                 risk_flags,
        "comment":                    comment,
        "_hist":                      hist,
        "_insider_df":                insider_df,
    }


# ─────────────────────────────────────────────
# バリュエーション帯分析 (Valuation Band Analysis)
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_valuation_band_data(ticker: str) -> dict | None:
    """バリュエーション帯分析に必要なデータを収集する。"""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        # ── 現在値 ──────────────────────────────────────
        price       = info.get("currentPrice") or info.get("regularMarketPrice")
        pe_ttm      = info.get("trailingPE")
        pe_fwd      = info.get("forwardPE")
        pb          = info.get("priceToBook")
        mkt_cap     = info.get("marketCap")
        shares      = info.get("sharesOutstanding")
        total_debt  = info.get("totalDebt", 0) or 0
        cash        = info.get("totalCash", 0) or 0
        revenue_ttm = info.get("totalRevenue")
        eps_ttm     = info.get("trailingEps")
        eps_fwd     = info.get("forwardEps")
        rev_growth  = info.get("revenueGrowth")   # small float
        eps_growth  = info.get("earningsGrowth")  # small float
        fcf_raw     = info.get("freeCashflow")
        gross_margin= info.get("grossMargins")
        sector      = info.get("sector", "")

        # EV 簡易計算
        ev = (mkt_cap or 0) + total_debt - cash if mkt_cap else None

        # PSR
        psr = (mkt_cap / revenue_ttm) if mkt_cap and revenue_ttm and revenue_ttm > 0 else None

        # EV/Sales
        ev_sales = (ev / revenue_ttm) if ev and revenue_ttm and revenue_ttm > 0 else None

        # FCF Yield
        fcf_yield = (fcf_raw / mkt_cap * 100) if fcf_raw and mkt_cap and mkt_cap > 0 else None

        # PEG 風（PER / EPS成長率%）
        eps_growth_pct = eps_growth * 100 if eps_growth else None
        rev_growth_pct = rev_growth * 100 if rev_growth else None
        peg = (pe_ttm / eps_growth_pct) if pe_ttm and eps_growth_pct and eps_growth_pct > 0 else None

        # ── 過去レンジ推定（方法B: 価格÷年次EPS / 年次Sales で近似） ──
        hist_pe_values  = []
        hist_psr_values = []
        try:
            # 年次財務
            inc = stock.income_stmt   # 列=年度
            if inc is not None and not inc.empty:
                inc_t = inc.T.sort_index()
                for col in ["Net Income", "NetIncome", "Net Income Common Stockholders"]:
                    if col in inc_t.columns:
                        annual_ni = inc_t[col]
                        break
                else:
                    annual_ni = None

                for col in ["Total Revenue", "TotalRevenue", "Operating Revenue"]:
                    if col in inc_t.columns:
                        annual_rev = inc_t[col]
                        break
                else:
                    annual_rev = None

                shares_count = shares or 1
                price_hist_5y = stock.history(period="5y", interval="1mo")["Close"]

                for dt, row_date in inc_t.iterrows():
                    # その年度直後の1ヶ月の平均株価を取得
                    window = price_hist_5y.loc[
                        price_hist_5y.index >= pd.Timestamp(dt)
                    ].iloc[:3]  # 最大3ヶ月分
                    if window.empty:
                        continue
                    avg_price = window.mean()

                    if annual_ni is not None and dt in annual_ni.index:
                        ni_val = annual_ni.loc[dt]
                        if pd.notna(ni_val) and shares_count > 0 and ni_val > 0:
                            hist_eps = ni_val / shares_count
                            hist_pe  = avg_price / hist_eps if hist_eps > 0 else None
                            if hist_pe and 5 < hist_pe < 300:
                                hist_pe_values.append(hist_pe)

                    if annual_rev is not None and dt in annual_rev.index:
                        rev_val = annual_rev.loc[dt]
                        if pd.notna(rev_val) and mkt_cap and rev_val > 0:
                            hist_psr = avg_price * shares_count / rev_val if shares_count else None
                            if hist_psr and 0 < hist_psr < 100:
                                hist_psr_values.append(hist_psr)
        except Exception as _e:
            print(f"VAL HIST ERROR: {_e}")

        # ── 同業比較データ ──────────────────────────────
        peer_tickers = get_competitors(ticker)
        peer_data = []
        for pt in peer_tickers[:5]:
            try:
                pi = yf.Ticker(pt).info
                peer_data.append({
                    "ticker": pt,
                    "pe":  pi.get("trailingPE"),
                    "pb":  pi.get("priceToBook"),
                    "psr": (pi.get("marketCap") / pi.get("totalRevenue"))
                           if pi.get("marketCap") and pi.get("totalRevenue") else None,
                    "rev_growth": (pi.get("revenueGrowth") or 0) * 100,
                    "eps_growth": (pi.get("earningsGrowth") or 0) * 100,
                })
            except Exception:
                pass

        return {
            "ticker": ticker, "price": price, "sector": sector,
            "pe_ttm": pe_ttm, "pe_fwd": pe_fwd, "pb": pb,
            "psr": psr, "ev_sales": ev_sales, "peg": peg, "fcf_yield": fcf_yield,
            "mkt_cap": mkt_cap, "rev_growth_pct": rev_growth_pct,
            "eps_growth_pct": eps_growth_pct, "gross_margin": gross_margin,
            "hist_pe_values":  hist_pe_values,
            "hist_psr_values": hist_psr_values,
            "peer_data": peer_data,
        }
    except Exception as e:
        print(f"VAL BAND FETCH ERROR: {e}")
        return None


def _band_position(current: float, values: list[float]) -> float | None:
    """currentが values のリスト中で何%tile にあるかを返す (0〜1)。"""
    if not values or current is None:
        return None
    below = sum(1 for v in values if v <= current)
    return round(below / len(values), 2)


def calculate_valuation_band(vb_data: dict) -> dict:
    """バリュエーション帯スコアと各指標を算出して返す。"""
    fallback = {
        "valuation_score_v2": 50, "valuation_status": "fair",
        "valuation_label_ja": "データ不足", "current_pe": None,
        "historical_pe_median": None, "historical_pe_band_position": None,
        "current_psr": None, "historical_psr_median": None,
        "historical_psr_band_position": None, "peg": None, "fcf_yield": None,
        "peer_pe_median": None, "peer_psr_median": None,
        "peer_pe_gap": None, "peer_psr_gap": None,
        "valuation_tier": "fair", "quality_flags": [], "risk_flags": [],
        "comment": "データが取得できませんでした。",
    }
    if not vb_data:
        return fallback

    quality_flags: list[str] = []
    risk_flags:    list[str] = []
    score = 50  # ベース（50=fair）

    pe   = vb_data.get("pe_ttm")
    pb   = vb_data.get("pb")
    psr  = vb_data.get("psr")
    peg  = vb_data.get("peg")
    fcfy = vb_data.get("fcf_yield")
    rev_g = vb_data.get("rev_growth_pct")
    eps_g = vb_data.get("eps_growth_pct")
    hist_pe  = vb_data.get("hist_pe_values", [])
    hist_psr = vb_data.get("hist_psr_values", [])
    peers    = vb_data.get("peer_data", [])

    # ── A. 自社過去レンジ比較 ─────────────────────────────
    hist_pe_median = round(sorted(hist_pe)[len(hist_pe)//2], 1) if hist_pe else None
    hist_psr_median = round(sorted(hist_psr)[len(hist_psr)//2], 1) if hist_psr else None
    pe_band_pos  = _band_position(pe, hist_pe)   if pe  else None
    psr_band_pos = _band_position(psr, hist_psr) if psr else None

    hist_score_delta = 0
    if pe_band_pos is not None:
        if pe_band_pos <= 0.25:
            hist_score_delta += 15
            quality_flags.append(f"過去PER帯の下位25%圏（割安ゾーン） — 現在PER {pe:.1f}x / 中央値 {hist_pe_median:.1f}x")
        elif pe_band_pos <= 0.5:
            hist_score_delta += 7
            quality_flags.append(f"過去PER帯の中間以下（やや割安）— 現在PER {pe:.1f}x / 中央値 {hist_pe_median:.1f}x")
        elif pe_band_pos <= 0.75:
            hist_score_delta -= 5
            risk_flags.append(f"過去PER帯の上位50%圏（やや割高）— 現在PER {pe:.1f}x / 中央値 {hist_pe_median:.1f}x")
        else:
            hist_score_delta -= 15
            risk_flags.append(f"過去PER帯の上位25%内（割高ゾーン）— 現在PER {pe:.1f}x / 中央値 {hist_pe_median:.1f}x")

    if psr_band_pos is not None:
        if psr_band_pos <= 0.25:
            hist_score_delta += 8
            quality_flags.append(f"過去PSR帯の下位25%（割安）— 現在PSR {psr:.1f}x / 中央値 {hist_psr_median:.1f}x")
        elif psr_band_pos >= 0.75:
            hist_score_delta -= 8
            risk_flags.append(f"過去PSR帯の上位25%（割高）— 現在PSR {psr:.1f}x / 中央値 {hist_psr_median:.1f}x")

    score += hist_score_delta

    # ── B. 同業比較 ───────────────────────────────────────
    peer_pe_vals  = [p["pe"]  for p in peers if p.get("pe")  and p["pe"] > 0]
    peer_psr_vals = [p["psr"] for p in peers if p.get("psr") and p["psr"] > 0]
    peer_pe_med  = round(sorted(peer_pe_vals)[len(peer_pe_vals)//2], 1)  if peer_pe_vals  else None
    peer_psr_med = round(sorted(peer_psr_vals)[len(peer_psr_vals)//2], 1) if peer_psr_vals else None

    peer_pe_gap  = round((pe  / peer_pe_med  - 1) * 100, 1) if pe  and peer_pe_med  and peer_pe_med  > 0 else None
    peer_psr_gap = round((psr / peer_psr_med - 1) * 100, 1) if psr and peer_psr_med and peer_psr_med > 0 else None

    peer_score_delta = 0
    if peer_pe_gap is not None:
        if peer_pe_gap <= -20:
            peer_score_delta += 12
            quality_flags.append(f"同業比PER {peer_pe_gap:+.0f}% — 競合より大幅に割安")
        elif peer_pe_gap <= -5:
            peer_score_delta += 6
            quality_flags.append(f"同業比PER {peer_pe_gap:+.0f}% — 競合よりやや割安")
        elif peer_pe_gap >= 30:
            peer_score_delta -= 12
            risk_flags.append(f"同業比PER {peer_pe_gap:+.0f}% — 競合より大幅に割高（プレミアムが大きい）")
        elif peer_pe_gap >= 10:
            peer_score_delta -= 5
            risk_flags.append(f"同業比PER {peer_pe_gap:+.0f}% — 競合よりやや割高")

    if peer_psr_gap is not None:
        if peer_psr_gap <= -20:
            peer_score_delta += 8
        elif peer_psr_gap >= 30:
            peer_score_delta -= 8
            risk_flags.append(f"同業比PSR {peer_psr_gap:+.0f}% — 売上評価が競合より大幅に高い")

    score += peer_score_delta

    # ── C. 成長率調整後評価（PEG 的） ──────────────────────
    growth_score_delta = 0
    if peg is not None:
        if peg < 1.0:
            growth_score_delta += 15
            quality_flags.append(f"PEG {peg:.2f} < 1.0 — 成長率に対して過小評価（割安サイン）")
        elif peg < 1.5:
            growth_score_delta += 7
            quality_flags.append(f"PEG {peg:.2f} — 成長率に対して概ね妥当")
        elif peg < 2.5:
            growth_score_delta -= 0
        elif peg < 4.0:
            growth_score_delta -= 8
            risk_flags.append(f"PEG {peg:.2f} — 成長率に対して割高気味")
        else:
            growth_score_delta -= 15
            risk_flags.append(f"PEG {peg:.2f} — 成長率に対して大幅に割高（過熱の可能性）")
    elif pe and rev_g:
        # PEG代替: PER / 売上成長率でざっくり補正
        rough_peg = pe / rev_g if rev_g > 0 else None
        if rough_peg and rough_peg < 1.0:
            growth_score_delta += 10
            quality_flags.append(f"PER {pe:.1f}x / 売上成長率 {rev_g:.1f}% — 成長に対して妥当な評価")
        elif rough_peg and rough_peg > 3.0:
            growth_score_delta -= 10
            risk_flags.append(f"PER {pe:.1f}x / 売上成長率 {rev_g:.1f}% — 成長対比で割高気味")

    # PSR vs 成長率（高成長なら高PSRは許容）
    if psr and rev_g:
        psr_growth_ratio = psr / rev_g if rev_g > 0 else None
        if psr_growth_ratio and psr_growth_ratio < 0.3:
            growth_score_delta += 5
            quality_flags.append(f"PSR {psr:.1f}x / 売上成長 {rev_g:.1f}% — 収益性と整合的")
        elif psr_growth_ratio and psr_growth_ratio > 1.0:
            growth_score_delta -= 5
            risk_flags.append(f"PSR {psr:.1f}x / 売上成長 {rev_g:.1f}% — 成長率に対してPSRが高い")

    score += growth_score_delta

    # ── FCF Yield 補正 ────────────────────────────────────
    if fcfy is not None:
        if fcfy >= 4.0:
            score += 8; quality_flags.append(f"FCF利回り {fcfy:.1f}% — キャッシュ創出力が高い")
        elif fcfy >= 2.0:
            score += 3
        elif fcfy < 0:
            score -= 5; risk_flags.append(f"FCF利回りがマイナス ({fcfy:.1f}%) — FCF赤字")

    score = max(0, min(100, score))

    # ── ステータス判定 ─────────────────────────────────────
    if score >= 72:
        status = "cheap";    status_ja = "割安ゾーン（バリュー優位）"
    elif score >= 55:
        status = "fair";     status_ja = "適正評価（フェアバリュー付近）"
    elif score >= 38:
        status = "slightly_expensive"; status_ja = "やや割高（プレミアム圏）"
    else:
        status = "expensive"; status_ja = "割高ゾーン（過熱の可能性）"

    # ── コメント ───────────────────────────────────────────
    parts = []
    if pe_band_pos is not None and pe_band_pos <= 0.35:
        parts.append(f"自社の過去PERレンジで見ると割安")
    elif pe_band_pos is not None and pe_band_pos >= 0.75:
        parts.append("自社の過去PERレンジで見ると割高気味")
    if peer_pe_gap is not None and peer_pe_gap <= -10:
        parts.append("同業他社より低い評価倍率")
    elif peer_pe_gap is not None and peer_pe_gap >= 20:
        parts.append("同業他社より高い評価倍率（プレミアム）")
    if peg and peg < 1.5:
        parts.append("PEG（成長調整後PER）は良好")
    elif peg and peg > 3.0:
        parts.append("成長率対比でPERが高い点に注意")
    comment = "、".join(parts) + "。" if parts else "複数指標を総合した評価です。詳細は各項目をご確認ください。"

    return {
        "valuation_score_v2":          score,
        "valuation_status":            status,
        "valuation_label_ja":          status_ja,
        "current_pe":                  pe,
        "current_pe_fwd":              vb_data.get("pe_fwd"),
        "current_pb":                  pb,
        "current_psr":                 psr,
        "current_ev_sales":            vb_data.get("ev_sales"),
        "peg":                         peg,
        "fcf_yield":                   fcfy,
        "rev_growth_pct":              rev_g,
        "eps_growth_pct":              eps_g,
        "historical_pe_median":        hist_pe_median,
        "historical_pe_band_position": pe_band_pos,
        "historical_psr_median":       hist_psr_median,
        "historical_psr_band_position": psr_band_pos,
        "hist_pe_values":              hist_pe,
        "hist_psr_values":             hist_psr,
        "peer_pe_median":              peer_pe_med,
        "peer_psr_median":             peer_psr_med,
        "peer_pe_gap":                 peer_pe_gap,
        "peer_psr_gap":                peer_psr_gap,
        "peer_data":                   peers,
        "quality_flags":               quality_flags,
        "risk_flags":                  risk_flags,
        "comment":                     comment,
    }


# ─────────────────────────────────────────────
# イベントリスク判定 (Event Risk Analysis)
# ─────────────────────────────────────────────

# ── マクロイベントカレンダー（固定辞書 — 定期更新 or 外部API差し替え可能） ──
# 形式: {"名前": "YYYY-MM-DD"} — 直近 / 予定日を手動更新する簡易版
_MACRO_EVENT_CALENDAR: list[dict] = [
    # ── FOMC 2026年（年8回、概ね6週おき）──────────────────────────
    {"name": "FOMC",     "date": "2026-01-29", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-03-19", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-05-07", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-06-18", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-07-30", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-09-17", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-11-05", "type": "fomc"},
    {"name": "FOMC",     "date": "2026-12-17", "type": "fomc"},
    # ── CPI 2026年（毎月中旬、概ね第2週水曜）────────────────────────
    {"name": "CPI",      "date": "2026-01-14", "type": "cpi"},
    {"name": "CPI",      "date": "2026-02-11", "type": "cpi"},
    {"name": "CPI",      "date": "2026-03-11", "type": "cpi"},
    {"name": "CPI",      "date": "2026-04-10", "type": "cpi"},
    {"name": "CPI",      "date": "2026-05-13", "type": "cpi"},
    {"name": "CPI",      "date": "2026-06-10", "type": "cpi"},
    {"name": "CPI",      "date": "2026-07-09", "type": "cpi"},
    {"name": "CPI",      "date": "2026-08-12", "type": "cpi"},
    {"name": "CPI",      "date": "2026-09-09", "type": "cpi"},
    {"name": "CPI",      "date": "2026-10-14", "type": "cpi"},
    {"name": "CPI",      "date": "2026-11-12", "type": "cpi"},
    {"name": "CPI",      "date": "2026-12-10", "type": "cpi"},
    # ── 雇用統計 2026年（毎月第1金曜）──────────────────────────────
    {"name": "雇用統計", "date": "2026-01-09", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-02-06", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-03-06", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-04-03", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-05-01", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-06-05", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-07-02", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-08-07", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-09-04", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-10-02", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-11-06", "type": "jobs"},
    {"name": "雇用統計", "date": "2026-12-04", "type": "jobs"},
]

# セクター別イベント感応度マップ
_SECTOR_EVENT_SENSITIVITY: dict[str, dict] = {
    "Technology":             {"level": "high",   "ja": "テクノロジー — 規制・決算・金利変動に敏感"},
    "Consumer Cyclical":      {"level": "high",   "ja": "一般消費財 — 景気・消費指標に敏感"},
    "Communication Services": {"level": "high",   "ja": "通信/メディア — 広告単価・規制イベントに敏感"},
    "Financial Services":     {"level": "high",   "ja": "金融 — 金利・信用イベントに敏感"},
    "Healthcare":             {"level": "very_high", "ja": "ヘルスケア/バイオ — 承認・臨床試験結果で急変"},
    "Energy":                 {"level": "high",   "ja": "エネルギー — 原油価格・OPEC政策に敏感"},
    "Basic Materials":        {"level": "medium", "ja": "素材 — 商品市況・中国需要に感応"},
    "Industrials":            {"level": "medium", "ja": "資本財 — ISM・貿易・受注統計に感応"},
    "Real Estate":            {"level": "medium", "ja": "不動産 — 金利・住宅指標に感応"},
    "Utilities":              {"level": "low",    "ja": "公益 — イベント感応が低い安定セクター"},
    "Consumer Defensive":     {"level": "low",    "ja": "生活必需品 — 景気後退耐性が強い"},
}


@st.cache_data(ttl=1800)
def fetch_event_risk_data(ticker: str) -> dict:
    """イベントリスク判定に必要なデータを収集する。"""
    result: dict = {"ticker": ticker}
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        result["sector"]   = info.get("sector", "")
        result["industry"] = info.get("industry", "")
        result["beta"]     = info.get("beta")

        # ── 次回決算日 ────────────────────────────────────
        ed_info = fetch_next_earnings_date(ticker)
        result["earnings_date"] = ed_info["earnings_date"]

        # ── 配当落ち日 ────────────────────────────────────
        try:
            ex_div_raw = info.get("exDividendDate")
            if ex_div_raw:
                import datetime as _dt
                ex_div = _dt.date.fromtimestamp(ex_div_raw) if isinstance(ex_div_raw, (int, float)) else pd.Timestamp(ex_div_raw).date()
                result["ex_dividend_date"] = ex_div
        except Exception:
            pass

        # ── 過去決算ボラティリティ（post EQ 1日騰落の絶対値平均） ──
        try:
            eq_raw = fetch_earnings_quality_data(ticker)  # キャッシュ活用
            if eq_raw and not eq_raw.get("hist", pd.DataFrame()).empty:
                hist = eq_raw["hist"]
                avg_moves = []
                for eqd in eq_raw.get("eq_dates", [])[-4:]:
                    rxn = _post_earnings_reaction(hist, eqd)
                    if rxn.get("ret_1d") is not None:
                        avg_moves.append(abs(rxn["ret_1d"]))
                result["avg_earnings_move_pct"] = round(sum(avg_moves) / len(avg_moves), 1) if avg_moves else None
        except Exception:
            result["avg_earnings_move_pct"] = None

    except Exception as e:
        print(f"EVENT RISK FETCH ERROR: {e}")

    return result


def calculate_event_risk(er_data: dict) -> dict:
    """イベントリスクスコア（高いほどリスク大）と各指標を返す。"""
    import datetime as _dt
    today = _dt.date.today()

    quality_flags: list[str] = []  # 安心材料（リスクが低い要因）
    risk_flags:    list[str] = []  # 警戒材料

    score = 0  # 0=リスク低, 高ほどリスク大

    # ── 1. 個社決算リスク ──────────────────────────────
    earnings_date   = er_data.get("earnings_date")
    days_to_earn    = None
    earn_risk       = "unknown"
    earn_risk_ja    = "決算日不明"

    if earnings_date:
        days_to_earn = (earnings_date - today).days
        avg_move = er_data.get("avg_earnings_move_pct")

        if days_to_earn < 0:
            # 決算通過済み
            earn_risk = "passed"; earn_risk_ja = "決算通過済"
            quality_flags.append(f"直近決算は通過済み（{abs(days_to_earn)}日前）— イベント通過後の安定期")
        elif days_to_earn <= 3:
            earn_risk = "imminent"; earn_risk_ja = "決算直前（3日以内）"
            score += 35
            risk_flags.append(f"次回決算まで {days_to_earn}日 — 今すぐの新規エントリーはギャンブル性が高い")
            if avg_move and avg_move >= 5:
                score += 10
                risk_flags.append(f"過去の決算ジャンプが平均 ±{avg_move:.1f}% — 高ボラ銘柄")
        elif days_to_earn <= 7:
            earn_risk = "high"; earn_risk_ja = "決算接近（7日以内）"
            score += 25
            risk_flags.append(f"次回決算まで {days_to_earn}日 — 決算前の高ボラティリティ期")
            if avg_move and avg_move >= 5:
                score += 8; risk_flags.append(f"過去決算ジャンプ平均 ±{avg_move:.1f}%")
        elif days_to_earn <= 14:
            earn_risk = "medium"; earn_risk_ja = "決算2週間以内"
            score += 15
            risk_flags.append(f"次回決算まで {days_to_earn}日 — 決算前のポジション調整注意")
        elif days_to_earn <= 30:
            earn_risk = "low"; earn_risk_ja = "決算1ヶ月以内"
            score += 5
        else:
            earn_risk = "safe"; earn_risk_ja = f"決算まで余裕あり（{days_to_earn}日後）"
            quality_flags.append(f"次回決算まで {days_to_earn}日 — 決算リスク低")
    else:
        score += 8  # 不明は軽度リスク
        risk_flags.append("次回決算日が取得できませんでした — 不確実性あり")

    # ── 2. 配当落ち日 ──────────────────────────────────
    ex_div = er_data.get("ex_dividend_date")
    days_to_div = None
    if ex_div and isinstance(ex_div, _dt.date):
        days_to_div = (ex_div - today).days
        if 0 <= days_to_div <= 5:
            score += 8
            risk_flags.append(f"配当落ち日まで {days_to_div}日 — 短期の株価調整に注意")
        elif days_to_div < 0:
            quality_flags.append("直近の配当落ち日は通過済み")

    # ── 3. マクロイベント照合 ──────────────────────────
    beta  = er_data.get("beta") or 1.0
    macro_risk_level = "low"
    macro_risk_ja    = "マクロイベントなし（1週間以内）"
    nearest_macro_days = 999
    nearest_macro_name = ""

    for ev in _MACRO_EVENT_CALENDAR:
        try:
            ev_date = _dt.date.fromisoformat(ev["date"])
            diff    = (ev_date - today).days
            if 0 <= diff < nearest_macro_days:
                nearest_macro_days = diff
                nearest_macro_name = ev["name"]
        except Exception:
            pass

    if nearest_macro_days <= 3:
        macro_weight = min(int(15 * beta), 25)
        score += macro_weight
        macro_risk_level = "high"; macro_risk_ja = f"マクロ注意（{nearest_macro_name}まで{nearest_macro_days}日）"
        risk_flags.append(f"{nearest_macro_name} が {nearest_macro_days}日後 — ベータ {beta:.1f}x の銘柄は感応度が高い")
    elif nearest_macro_days <= 7:
        macro_weight = min(int(8 * beta), 15)
        score += macro_weight
        macro_risk_level = "medium"; macro_risk_ja = f"マクロ軽度注意（{nearest_macro_name}まで{nearest_macro_days}日）"
        risk_flags.append(f"{nearest_macro_name} が {nearest_macro_days}日後")
    elif nearest_macro_days <= 14:
        score += 3
        macro_risk_level = "low_medium"; macro_risk_ja = f"マクロ {nearest_macro_name} まで{nearest_macro_days}日"
    else:
        quality_flags.append("直近2週間に主要マクロイベントなし")

    # ── 4. セクター感応度 ─────────────────────────────
    sector  = er_data.get("sector", "")
    sec_cfg = _SECTOR_EVENT_SENSITIVITY.get(sector, {"level": "medium", "ja": "セクター感応度: 中"})
    sec_level = sec_cfg["level"]
    sec_label_ja = sec_cfg["ja"]
    sec_score_map = {"very_high": 15, "high": 8, "medium": 3, "low": 0}
    score += sec_score_map.get(sec_level, 3)

    if sec_level in ("very_high", "high"):
        risk_flags.append(f"セクター特性: {sec_label_ja}")
    else:
        quality_flags.append(f"セクター特性: {sec_label_ja}")

    # ── 5. event_window_flag ────────────────────────────
    event_window = (
        (days_to_earn is not None and 0 <= days_to_earn <= 7) or
        nearest_macro_days <= 5
    )
    high_vol_window = (
        (days_to_earn is not None and 0 <= days_to_earn <= 3) or
        (days_to_earn is not None and 0 <= days_to_earn <= 14 and beta >= 1.5)
    )

    score = max(0, min(100, score))

    # ── ステータス ─────────────────────────────────────
    if score >= 50:
        status = "high";   status_ja = "イベントリスクが高い"
    elif score >= 25:
        status = "medium"; status_ja = "イベントリスクは中程度"
    else:
        status = "low";    status_ja = "イベントリスクは低い"

    wait_flag = (score >= 30 and event_window)

    # ── コメント ───────────────────────────────────────
    parts = []
    if earn_risk in ("imminent", "high"):
        parts.append(f"決算が{days_to_earn}日後に迫っており、エントリーには慎重な判断が必要")
    if macro_risk_level in ("high", "medium"):
        parts.append(f"{nearest_macro_name}など主要マクロイベントが近い")
    if sec_level in ("very_high", "high"):
        parts.append("セクター特性上、イベントで大きく動きやすい")
    if not parts:
        parts.append("現時点ではイベントによる抑制要因は少ない")
    comment = "。".join(parts) + "。"

    return {
        "event_risk_score":            score,
        "event_risk_status":           status,
        "summary_label_ja":            status_ja,
        "days_to_earnings":            days_to_earn,
        "earnings_date":               str(earnings_date) if earnings_date else None,
        "earnings_risk_level":         earn_risk,
        "earnings_risk_label_ja":      earn_risk_ja,
        "avg_earnings_move_pct":       er_data.get("avg_earnings_move_pct"),
        "days_to_ex_dividend":         days_to_div,
        "macro_event_risk_level":      macro_risk_level,
        "macro_event_risk_label_ja":   macro_risk_ja,
        "nearest_macro_name":          nearest_macro_name,
        "nearest_macro_days":          nearest_macro_days if nearest_macro_days < 999 else None,
        "sector_event_sensitivity":    sec_level,
        "sector_event_sensitivity_label_ja": sec_label_ja,
        "event_window_flag":           event_window,
        "high_volatility_window":      high_vol_window,
        "wait_for_event_passage":      wait_flag,
        "quality_flags":               quality_flags,
        "risk_flags":                  risk_flags,
        "comment":                     comment,
        "beta":                        beta,
    }


# ─────────────────────────────────────────────
# CIO 7軸統合エンジン (build_cio_decision_inputs)
# ─────────────────────────────────────────────

@st.cache_data(ttl=1800)
def determine_stock_playbook(ticker: str, cio_inputs: dict) -> dict:
    """
    CIO 7軸スコアなどの統合データをもとに、銘柄の最適な戦術（Playbook）を判定する。
    """
    scores = cio_inputs.get("scores", {})
    total_score = cio_inputs.get("total_score", 50)
    
    trend = scores.get("trend_score", 50)
    entry = scores.get("entry_score", 50)
    rs_score = scores.get("rs_score", 50)
    event_risk = scores.get("event_safety_score", 50)  # イベント安全性 (低いと危険, 0-100)
    earn_score = scores.get("earnings_score", 50)
    
    pb_type = "avoid"
    label_ja = "回避型"
    reason = []
    flags = []
    
    # 基本判定ロジック
    if trend >= 65 and rs_score >= 55:
        if entry >= 60:
            pb_type = "breakout_initial"
            label_ja = "初動ブレイク型"
            reason.append("週足トレンドと相対強度(RS)が強気局面にある")
            reason.append("日足レベルでも直近高値更新や良好なエントリー位置にある")
            flags.extend(["順張り本命", "モメンタム強", "ブレイク追随"])
        else:
            pb_type = "pullback_continuation"
            label_ja = "押し目継続型"
            reason.append("週足トレンドは極めて良好だが、日足ではやや伸びきりか調整中")
            reason.append("下値支持線での反発を待つ方がリスクリワードが良い")
            flags.extend(["調整待ち優位", "移動平均線反発狙い"])
    elif 45 <= trend < 65:
        if rs_score >= 50 or earn_score >= 60:
            pb_type = "early_monitor"
            label_ja = "先回り監視型"
            reason.append("週足ベースの底打ち・ベース形成が進行中")
            reason.append("ファンダメンタルズやRSに改善の兆しがあるが、まだ明確なブレイクには至っていない")
            flags.extend(["ベース形成中", "アラート待機", "打診買い検討"])
        else:
            pb_type = "avoid"
            label_ja = "回避型"
            reason.append("トレンドが中途半端で、特筆すべき強みが見当たらない")
            flags.append("方向感欠如")
    else:
        pb_type = "avoid"
        label_ja = "回避型"
        reason.append("週足トレンドが下落局面（Stage3/4）、または全体として評価が低すぎる")
        flags.extend(["売り圧力優位", "資金拘束リスク", "逆張り厳禁"])
        
    # イベント通過待ちオーバーライド
    if event_risk < 45 and pb_type != "avoid":
        secondary_type = pb_type
        secondary_label = label_ja
        pb_type = "event_wait"
        label_ja = "イベント通過待ち型"
        reason.insert(0, "銘柄本来のトレンドは良いが、直近の決算やマクロイベントなどの不確実性が高い")
        flags.insert(0, "ボラティリティ警戒")
    else:
        secondary_type = None
        secondary_label = None

    # 行動指針のマッピング
    actions = {
        "breakout_initial": {
            "best": "直近高値更新のブレイク確認でエントリー。または浅い押し目で乗る",
            "avoid": "大きな押し目まで待ちすぎること、深い調整へのナンピン",
            "trigger": "日足での大陽線＋出来高増、新高値更新",
            "warning": "ブレイク直後からの陰線包み足や、出来高を伴う直近安値割れ",
            "conf": "high" if total_score >= 65 else "medium",
            "bg": "rgba(59,130,246,0.15)",
            "border": "#3b82f6"
        },
        "pullback_continuation": {
            "best": "20日線や50日線付近まで引き付け、反発を確認してからエントリー",
            "avoid": "移動平均線から大きく上方乖離した位置での無計画な飛び乗り",
            "trigger": "主要な移動平均線付近での下ヒゲや陽線反発",
            "warning": "50日移動平均線を明確に下抜け、かつ数日回復できない場合",
            "conf": "high" if total_score >= 60 else "medium",
            "bg": "rgba(16,185,129,0.15)",
            "border": "#10b981"
        },
        "early_monitor": {
            "best": "事前にブレイクラインを引き、アラートを設定して監視を続ける",
            "avoid": "トレンド転換確認前の思いつきの先回りフルポジション",
            "trigger": "ベース上限の明白な上抜けと相対強度(RS)の急上昇",
            "warning": "ベース下限の割り込み、悪決算による窓開け下落",
            "conf": "medium" if total_score >= 50 else "low",
            "bg": "rgba(168,85,247,0.15)",
            "border": "#a855f7"
        },
        "event_wait": {
            "best": "イベント（決算発表等）を無事通過した後の値動きを確認してからエントリー",
            "avoid": "イベント前の「ギャンブル的な決算跨ぎエントリー」",
            "trigger": "イベント通過後に悪材料出尽くしで上昇、または好決算後の横ばい保持",
            "warning": "ガイダンス下方修正や、サポートラインを大きく割るギャップダウン",
            "conf": "medium",
            "bg": "rgba(245,158,11,0.15)",
            "border": "#f59e0b"
        },
        "avoid": {
            "best": "見送り。他の有望なトレンド形成銘柄へ資金を向ける",
            "avoid": "「安くなってきたから」という理由での逆張り買い",
            "trigger": "週足ベースでのStage 2初期シグナルが明確に出るまで待機",
            "warning": "下落トレンドの継続、恒常的なRSの下落",
            "conf": "high" if trend < 35 else "medium",
            "bg": "rgba(239,68,68,0.15)",
            "border": "#ef4444"
        }
    }
    
    act_data = actions.get(pb_type, actions["avoid"])
    conf_level = act_data["conf"]
    conf_label = {"high": "高確信", "medium": "中程度の確信", "low": "低確信"}.get(conf_level, "不明")

    return {
        "stock_playbook_type": pb_type,
        "stock_playbook_type_label_ja": label_ja,
        "playbook_confidence": conf_level,
        "playbook_confidence_label_ja": conf_label,
        "secondary_type": secondary_type,
        "secondary_type_label_ja": secondary_label,
        "playbook_reason": reason,
        "best_action": act_data["best"],
        "avoid_action": act_data["avoid"],
        "trigger_condition": act_data["trigger"],
        "warning_condition": act_data["warning"],
        "playbook_flags": flags,
        "color_bg": act_data["bg"],
        "color_border": act_data["border"],
        "comment": f"現在の状況は【{label_ja}】です。「{act_data['best']}」を基本戦略としてください。"
    }

@st.cache_data(ttl=1800)
def calculate_scenario_expected_value(ticker: str, data: dict, cio_inputs: dict) -> dict:
    """
    Bull / Base / Bear の3シナリオから期待値（Expected Value）とリスクリワード（RR）を算出する。
    """
    price = data.get("price")
    base_eps = data.get("eps_trailing")
    
    if not price or base_eps is None or base_eps <= 0:
        return {
            "expected_value_score": 0, 
            "expected_value_status": "error", 
            "summary_label_ja": "データ不足またはEPSマイナス"
        }
        
    scores = cio_inputs.get("scores", {})
    trend = scores.get("trend_score", 50)
    
    # 成長率とPERの推定（未取得なら一定のデフォルトを置く）
    base_g = data.get("eps_growth") if data.get("eps_growth") is not None else data.get("revenue_growth")
    if base_g is None: 
        base_g = 0.08
    base_g = max(0.02, min(0.40, base_g)) # 2%〜40%でクランプ
    
    base_pe = data.get("pe_ratio")
    if base_pe is None or base_pe <= 0: 
        base_pe = 20
    base_pe = max(10.0, min(60.0, float(base_pe))) # 10〜60でクランプ
    
    # 割引率
    beta = data.get("beta", 1.0)
    if beta is None: beta = 1.0
    discount_rate = 0.05 + (beta * 0.05)
    
    # ── シナリオ設定 ──
    horizon = 5 # 5年後の収束先を見る（10年より実務的に近い）
    
    # Base Case
    base_prob = 0.50
    base_val = calculate_earnings_valuation(base_eps, base_g, horizon, base_pe, discount_rate)
    base_target = base_val["total_value"] if base_val else price
    
    # Bull Case (トレンドが良ければ確率を高める)
    bull_prob = 0.35 if trend >= 65 else (0.20 if trend <= 40 else 0.30)
    bull_g = min(0.50, base_g * 1.4)
    bull_pe = min(80.0, base_pe * 1.3)
    bull_val = calculate_earnings_valuation(base_eps, bull_g, horizon, bull_pe, discount_rate)
    bull_target = bull_val["total_value"] if bull_val else price * 1.2
    
    # Bear Case
    bear_prob = round(1.0 - base_prob - bull_prob, 2)
    bear_g = max(0.01, base_g * 0.5)
    bear_pe = max(8.0, base_pe * 0.6)
    bear_val = calculate_earnings_valuation(base_eps, bear_g, horizon, bear_pe, discount_rate)
    bear_target = bear_val["total_value"] if bear_val else price * 0.7
    
    # 余地計算
    bull_upside = (bull_target - price) / price * 100
    base_upside = (base_target - price) / price * 100
    bear_downside = (bear_target - price) / price * 100
    
    # 期待値 (EV)
    ev = (bull_target * bull_prob) + (base_target * base_prob) + (bear_target * bear_prob)
    ev_pct = (ev - price) / price * 100
    
    # リスクリワード比 (RR)
    risk = price - bear_target
    reward = bull_target - price
    if risk > 0:
        rr_ratio = reward / risk
    else:
        rr_ratio = 9.99 # 理論上、下値リスクがない（現在価格よりBearが高い）
        
    # スコア計算 (0-100)
    # 期待値 +20% で 80点, +0% で 50点, -20% で 20点
    ev_score = min(100, max(0, int(50 + (ev_pct * 1.5))))
    
    # フラグやラベル
    if ev_pct >= 10.0 and rr_ratio >= 1.5:
        status = "attractive"
        label = "🟢 期待値・RRともに魅力的"
    elif ev_pct > 0.0 or rr_ratio >= 1.0:
        status = "neutral"
        label = "🟡 期待値プラス (Upside 優位)"
    else:
        status = "unattractive"
        label = "🔴 期待値マイナス (Downside 警戒)"
        
    quality_flags = []
    risk_flags = []
    
    if base_upside > 0:
        quality_flags.append(f"ベースケースでも {base_upside:.1f}% の上昇余地あり")
    else:
        risk_flags.append(f"現在価格はベースターゲット(${base_target:.2f})を既に上回る")
        
    if rr_ratio >= 2.0:
        quality_flags.append(f"リスクリワード比が {rr_ratio:.1f}x と非対称に上値有利")
    elif rr_ratio < 1.0:
        risk_flags.append(f"リスクリワード比が {rr_ratio:.2f}x と下値余地の方が大きい")
        
    if ev_pct > 10:
        quality_flags.append(f"シナリオ加重期待値が +{ev_pct:.1f}% でポジティブ")
    elif ev_pct < 0:
        risk_flags.append(f"シナリオ加重期待値が {ev_pct:.1f}% でマイナス")
        
    return {
        "expected_value_score": ev_score,
        "expected_value_status": status,
        "summary_label_ja": label,
        "current_price": price,
        "bull_target_price": bull_target,
        "base_target_price": base_target,
        "bear_target_price": bear_target,
        "bull_upside_pct": bull_upside,
        "base_upside_pct": base_upside,
        "bear_downside_pct": bear_downside,
        "bull_probability": bull_prob,
        "base_probability": base_prob,
        "bear_probability": bear_prob,
        "expected_value_pct": ev_pct,
        "risk_reward_ratio": rr_ratio,
        "quality_flags": quality_flags,
        "risk_flags": risk_flags,
        "comment": f"シナリオ加重期待値は {ev_pct:+.1f}% で、{label} な水準です。"
    }

@st.cache_data(ttl=1800)
def build_cio_decision_inputs(ticker: str) -> dict:
    """
    7軸スコア統合エンジン。
    各分析関数を安全に呼び出し、スコアを収集・正規化して返す。
    個別関数が失敗してもフォールバック値で継続する。
    """
    details: dict = {}
    scores: dict  = {}

    # ── 1. トレンド (Stage分析 + SEPA) ──────────────────
    try:
        ws = evaluate_weinstein_stage(ticker)
        details["weinstein"] = ws
        
        ws_stage_str = ws.get("stage", "")
        stage_num = 0
        if "1" in ws_stage_str: stage_num = 1
        elif "2" in ws_stage_str: stage_num = 2
        elif "3" in ws_stage_str: stage_num = 3
        elif "4" in ws_stage_str: stage_num = 4
        
        sub = ws.get("sub_stage", "mid")
        # Stage2 = 満点方向。Stage1mid=60, Stage2early=75, Stage2mid=90, Stage2late=80
        stage_base = {1: 40, 2: 85, 3: 40, 4: 15}.get(stage_num, 50)
        sub_adj    = {"early": -8, "mid": 0, "late": -5}.get(sub, 0)
        trend_score = min(100, max(0, stage_base + sub_adj))

        # SEPA補正
        try:
            sepa = evaluate_sepa(ticker)
            details["sepa"] = sepa
            if sepa:
                sepa_pct = sum(1 for v in sepa.values() if v.get("pass")) / max(1, len(sepa))
                trend_score = int(trend_score * 0.65 + sepa_pct * 100 * 0.35)
        except Exception:
            pass
    except Exception:
        trend_score = 50

    scores["trend_score"] = min(100, max(0, trend_score))

    # ── 2. エントリータイミング ──────────────────────────
    try:
        _ws = details.get("weinstein") or evaluate_weinstein_stage(ticker)
        et  = evaluate_entry_timing(ticker, _ws)
        details["entry_timing"] = et
        entry_score = et.get("entry_timing_score", 50) or 50
    except Exception:
        entry_score = 50

    scores["entry_score"] = min(100, max(0, entry_score))

    # ── 3. 相対強度 ───────────────────────────────────────
    try:
        from_rs = calculate_relative_strength_metrics
        # セクター情報を取得（RSデータ取得に必須）
        sector_info = ""
        try:
            sector_info = yf.Ticker(ticker).info.get("sector", "")
        except:
            pass
        
        rs_raw  = fetch_relative_strength_data(ticker, sector_info)
        rs      = from_rs(rs_raw)
        details["rs"] = rs
        rs_score = rs.get("rs_score", 50) or 50
    except Exception:
        rs_score = 50

    scores["rs_score"] = min(100, max(0, rs_score))

    # ── 4. 決算品質 ───────────────────────────────────────
    try:
        eq_raw = fetch_earnings_quality_data(ticker)
        eq     = calculate_earnings_quality(eq_raw)
        details["earnings_quality"] = eq
        earnings_score = eq.get("earnings_quality_score", 50) or 50
    except Exception:
        earnings_score = 50

    scores["earnings_score"] = min(100, max(0, earnings_score))

    # ── 5. 需給 ──────────────────────────────────────────
    try:
        sd_raw = fetch_supply_demand_extended(ticker)
        sd     = calculate_supply_demand_score(sd_raw)
        details["supply_demand"] = sd
        sd_score = sd.get("supply_demand_score", 50) or 50
    except Exception:
        sd_score = 50

    scores["supply_demand_score"] = min(100, max(0, sd_score))

    # ── 6. バリュエーション ───────────────────────────────
    try:
        vb_raw = fetch_valuation_band_data(ticker)
        vb     = calculate_valuation_band(vb_raw)
        details["valuation"] = vb
        valuation_score = vb.get("valuation_score_v2", 50) or 50
    except Exception:
        valuation_score = 50

    scores["valuation_score"] = min(100, max(0, valuation_score))

    # ── 7. イベント安全性 (100 - event_risk_score) ──────
    try:
        er_raw = fetch_event_risk_data(ticker)
        er     = calculate_event_risk(er_raw)
        details["event_risk"] = er
        event_safety = max(0, 100 - (er.get("event_risk_score", 30) or 30))
    except Exception:
        event_safety = 70

    scores["event_safety_score"] = min(100, max(0, event_safety))

    # ── 総合スコア (7軸加重平均) ───────────────────────────
    # 重み設定: トレンド・エントリーをやや重く、イベント安全性を軽く
    weights = {
        "trend_score":         0.20,
        "entry_score":         0.20,
        "rs_score":            0.15,
        "earnings_score":      0.15,
        "supply_demand_score": 0.12,
        "valuation_score":     0.10,
        "event_safety_score":  0.08,
    }
    total = sum(scores.get(k, 50) * w for k, w in weights.items())
    # 残りの重み(100%に満たない場合)に対応するため正規化
    weight_sum = sum(weights.values())
    total_score = round(total / weight_sum, 1)

    return {
        "scores":       scores,
        "total_score":  total_score,
        "details":      details,
    }


def derive_final_judgment(cio_inputs: dict, ticker: str, data: dict) -> dict:
    """
    7軸スコアから最終投資判断を導く。
    AI プロンプトにも渡せる構造化辞書を返す。
    """
    scores       = cio_inputs.get("scores", {})
    total        = cio_inputs.get("total_score", 50)
    details      = cio_inputs.get("details", {})

    trend  = scores.get("trend_score", 50)
    entry  = scores.get("entry_score", 50)
    rs     = scores.get("rs_score", 50)
    earn   = scores.get("earnings_score", 50)
    sd     = scores.get("supply_demand_score", 50)
    val    = scores.get("valuation_score", 50)
    ev_sf  = scores.get("event_safety_score", 70)

    # ── 最終判定ロジック ─────────────────────────────────
    wait_event = (ev_sf < 40)  # イベントリスクが高い
    trend_ok   = (trend >= 60)
    entry_ok   = (entry >= 60)
    rs_ok      = (rs    >= 55)

    if total >= 72 and trend_ok and entry_ok and not wait_event:
        verdict = "buy"
        verdict_ja = "✅ 買い"
        verdict_desc = "7軸スコアが高水準で揃っており、今が積極的なエントリー好機です。"
    elif total >= 60 and trend_ok and not wait_event:
        verdict = "pullback_buy"
        verdict_ja = "📉 押し目買い"
        verdict_desc = "トレンドは良好ですが、エントリータイミングの改善を待って押し目で入るのが合理的です。"
    elif wait_event and total >= 55:
        verdict = "wait_event"
        verdict_ja = "⏳ イベント通過待ち"
        verdict_desc = "銘柄の質は高いですが、直近のイベントリスクが解消されてからエントリーを検討してください。"
    elif total >= 50:
        verdict = "monitor"
        verdict_ja = "👁️ 監視継続"
        verdict_desc = "条件がまだ揃っていません。ウォッチリストに入れて条件成立を待ちましょう。"
    else:
        verdict = "pass"
        verdict_ja = "🚫 見送り"
        verdict_desc = "複数の軸でリスクが顕在化しており、現時点での投資は推奨しにくい局面です。"

    # ── 強み ─────────────────────────────────────────────
    axis_list = [
        ("トレンド",         trend,  "週足ステージが良好で上昇トレンドが確立",  "トレンドが弱い局面"),
        ("エントリー",       entry,  "日足でも買いタイミングが整っている",       "エントリータイミング不適切"),
        ("相対強度",         rs,     "市場・セクターを上回るアウトパフォーマンス", "市場に劣後するパフォーマンス"),
        ("決算品質",         earn,   "直近決算が強く成長の質も高い",             "決算品質に懸念あり"),
        ("需給",             sd,     "出来高を伴い資金が流入している",           "需給が弱い"),
        ("バリュエーション", val,    "成長率対比で評価倍率が妥当圏内",           "割高ゾーンにある"),
        ("イベント安全性",   ev_sf,  "直近のイベントリスクが低い",               "決算・マクロイベントが近い"),
    ]
    strengths = [f"{nm}: {pos}" for nm, sc, pos, neg in axis_list if sc >= 65][:3]
    risks     = [f"{nm}: {neg}" for nm, sc, pos, neg in axis_list if sc <=  40][:3]

    if not strengths:
        strengths = ["現時点で明確な強みが見当たりません。更なるデータをお待ちください。"]
    if not risks:
        risks     = ["現時点で顕著なリスクはありません。"]

    # ── ベストエントリー条件 ──────────────────────────────
    entry_conditions = []
    if trend < 60:
        entry_conditions.append("週足がStage 2に移行し、主要MAを上回ること")
    if entry < 60:
        entry_conditions.append("日足ベースで押し目・ブレイクアウトのパターンが形成されること")
    if ev_sf < 50:
        entry_conditions.append("決算・マクロイベントが通過し、イベントリスクが解消されること")
    if rs < 55:
        entry_conditions.append("RSラインが市場を上回り、相対強度が改善すること")
    if not entry_conditions:
        entry_conditions = ["現在の好条件が維持されること、出来高を伴ったブレイクアウトの確認"]

    # ── 無効化条件 ────────────────────────────────────────
    invalidation = []
    price = data.get("price", 0) or 0
    if price > 0:
        stop_ref = round(price * 0.93, 2)
        invalidation.append(f"株価が ${stop_ref:.2f}（現在値比-7%）を下回って終値をつけた場合")
    invalidation.append("週足のStage 2から3への転換シグナルが出た場合")
    if earn < 50:
        invalidation.append("次の決算でEPS・売上が市場予想を大幅に下回った場合")

    # ── 投資家タイプ分類 ──────────────────────────────────
    if trend >= 65 and (rs >= 55) and entry >= 55:
        inv_type = "モメンタム型（週足Stage2 + 相対強度）"
    elif val >= 65 and earn >= 60:
        inv_type = "グロース・クオリティ型（決算品質 + バリュエーション整合）"
    elif sd >= 65:
        inv_type = "需給主導型（機関流入 + 踏み上げ余地）"
    else:
        inv_type = "ウォッチ段階（条件未整備）"

    return {
        "verdict":         verdict,
        "verdict_ja":      verdict_ja,
        "verdict_desc":    verdict_desc,
        "total_score":     total,
        "strengths":       strengths,
        "risks":           risks,
        "entry_conditions": entry_conditions,
        "invalidation":   invalidation,
        "investor_type":  inv_type,
        "scores":         scores,
        "wait_event_flag": wait_event,
    }


def create_recommendation_pie_chart(recs_summary: pd.DataFrame):
    """アナリストの推奨レーティング構成をパイチャートで表示。"""
    if recs_summary is None or recs_summary.empty:
        return None
    
    # 0m (最新) のデータを取得
    latest = recs_summary.iloc[0]
    labels = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
    values = [latest.get('strongBuy', 0), latest.get('buy', 0), latest.get('hold', 0), latest.get('sell', 0), latest.get('strongSell', 0)]
    
    # 全て0なら描画しない
    if sum(values) == 0:
        return None

    colors = ['#059669', '#10b981', '#64748b', '#ef4444', '#b91c1c']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        insidetextorientation='radial'
    )])
    
    fig.update_layout(
        **PLOTLY_LAYOUT,
        showlegend=False,
        height=300
    )
    return fig

@st.cache_data(ttl=300)
def fetch_analyst_data(ticker: str) -> dict:
    """アナリスト予想・SEC資料・インサイダー情報を取得する"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # SEC資料
        filings = []
        try:
            sec = stock.sec_filings
            if sec:
                # 10-K, 10-Q, 8-K を優先提示
                important_types = ['10-K', '10-Q', '8-K']
                for f in sec:
                    if f.get('type') in important_types:
                        filings.append({
                            'date': f.get('date'),
                            'type': f.get('type'),
                            'title': f.get('title'),
                            'url': f.get('edgarUrl')
                        })
        except Exception:
            pass

        # インサイダー取引
        insider = None
        try:
            insider = stock.insider_transactions
            if insider is not None and not insider.empty:
                insider = insider[['Start Date', 'Insider', 'Position', 'Transaction', 'Shares', 'Value']].copy()
        except Exception:
            pass

        return {
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_mean": info.get("targetMeanPrice"),
            "recommendation_key": info.get("recommendationKey"),
            "recs_summary": stock.recommendations_summary if hasattr(stock, 'recommendations_summary') else None,
            "filings": filings[:10], # 直近10件
            "insider": insider
        }
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def fetch_peers_data(target_ticker: str, peers: list) -> pd.DataFrame | None:
    """ターゲットと競合の財務比較データを取得する"""
    tickers = [target_ticker] + peers
    data_list = []
    
    for t in tickers:
        try:
            # サーバー負荷軽減のため1秒待機
            time.sleep(1)
            
            stock = yf.Ticker(t)
            info = stock.info
            data_list.append({
                "ティッカー": t,
                "企業名": info.get("shortName", t) if info.get("shortName") else "—",
                "時価総額(M)": info.get("marketCap", 0) / 1_000_000 if info.get("marketCap") else None,
                "売上成長率(%)": info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") is not None else None,
                "営業利益率(%)": info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") is not None else None,
                "PER": info.get("trailingPE", None),
                "配当利回り(%)": info.get("dividendYield", 0) if info.get("dividendYield") is not None else None,
            })
        except Exception:
            pass
            
    if not data_list:
        return None
        
    df = pd.DataFrame(data_list)
    return df

PERIOD_MAP = {
    "1ヶ月": "1mo",
    "6ヶ月": "6mo",
    "1年": "1y",
    "5年": "5y",
}


@st.cache_data(ttl=300)
def fetch_price_history(ticker: str, period: str) -> pd.DataFrame | None:
    """yfinance から株価履歴を取得し、SMA50 / SMA200 / RSI を計算する。"""
    try:
        stock = yf.Ticker(ticker)
        # SMA200 の計算に十分なデータが必要なので、常に最大期間を取得してから切り取る
        max_period = "max" if period in ("1y", "5y") else "2y"
        df = stock.history(period=max_period, auto_adjust=True)

        if df is None or df.empty or len(df) < 20:
            return None

        df = df.reset_index()
        # Date 列を timezone-naive に変換
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

        # --- 移動平均 ---
        df["SMA50"] = df["Close"].rolling(window=50).mean()
        df["SMA200"] = df["Close"].rolling(window=200).mean()

        # --- RSI (14日) ---
        df["RSI"] = compute_rsi(df["Close"], window=14)

        # 期間でフィルタ
        now = pd.Timestamp.now()
        delta_map = {
            "1mo": pd.DateOffset(months=1),
            "6mo": pd.DateOffset(months=6),
            "1y": pd.DateOffset(years=1),
            "5y": pd.DateOffset(years=5),
        }
        cutoff = now - delta_map.get(period, pd.DateOffset(years=1))
        df = df[df["Date"] >= cutoff].copy()

        if df.empty:
            return None

        return df
    except Exception:
        return None


def compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """RSI（相対力指数）を計算する。"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ─────────────────────────────────────────────
# グラフ作成
# ─────────────────────────────────────────────

def create_revenue_chart(dates, revenue, net_income):
    """売上高 & 純利益の棒グラフを作成。"""
    fig = go.Figure()

    if revenue:
        fig.add_trace(go.Bar(
            x=dates,
            y=revenue,
            name="売上高",
            marker=dict(
                color="rgba(0, 210, 255, 0.75)",
                line=dict(color="rgba(0, 210, 255, 1)", width=1),
            ),
            hovertemplate="<b>%{x}</b><br>売上高: $%{y:,.1f}M<extra></extra>",
        ))

    if net_income:
        fig.add_trace(go.Bar(
            x=dates,
            y=net_income,
            name="純利益",
            marker=dict(
                color="rgba(168, 85, 247, 0.75)",
                line=dict(color="rgba(168, 85, 247, 1)", width=1),
            ),
            hovertemplate="<b>%{x}</b><br>純利益: $%{y:,.1f}M<extra></extra>",
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="売上高 & 純利益（百万ドル）", font=dict(size=16, color="#e2e8f0")),
        barmode="group",
        yaxis_title="百万ドル ($M)",
        xaxis_title="年度",
        height=420,
    )
    return fig


def create_cashflow_chart(dates, operating_cf):
    """営業キャッシュフローの推移グラフを作成。"""
    # 正負で色を分ける
    colors = ["rgba(52, 211, 153, 0.8)" if v >= 0 else "rgba(248, 113, 113, 0.8)"
              for v in operating_cf]
    line_colors = ["rgba(52, 211, 153, 1)" if v >= 0 else "rgba(248, 113, 113, 1)"
                   for v in operating_cf]

    fig = go.Figure()

    # 棒グラフ（正負で色分け）
    fig.add_trace(go.Bar(
        x=dates,
        y=operating_cf,
        name="営業CF",
        marker=dict(color=colors, line=dict(color=line_colors, width=1)),
        hovertemplate="<b>%{x}</b><br>営業CF: $%{y:,.1f}M<extra></extra>",
    ))

    # トレンドライン
    fig.add_trace(go.Scatter(
        x=dates,
        y=operating_cf,
        mode="lines+markers",
        name="トレンド",
        line=dict(color="rgba(250, 204, 21, 0.9)", width=2, dash="dot"),
        marker=dict(size=7, color="rgba(250, 204, 21, 1)"),
        hovertemplate="<b>%{x}</b><br>営業CF: $%{y:,.1f}M<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="営業キャッシュフロー推移（百万ドル）", font=dict(size=16, color="#e2e8f0")),
        yaxis_title="百万ドル ($M)",
        xaxis_title="年度",
        height=420,
        showlegend=True,
    )
    return fig



def create_fcf_chart(dates, fcf_values):
    """フリーキャッシュフロー推移グラフを作成。"""
    colors = ["rgba(52, 211, 153, 0.8)" if v >= 0 else "rgba(248, 113, 113, 0.8)" for v in fcf_values]
    line_colors = ["rgba(52, 211, 153, 1)" if v >= 0 else "rgba(248, 113, 113, 1)" for v in fcf_values]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates,
        y=fcf_values,
        name="FCF",
        marker=dict(color=colors, line=dict(color=line_colors, width=1)),
        hovertemplate="<b>%{x}</b><br>フリーCF: $%{y:,.1f}M<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="フリーキャッシュフロー推移($M)", font=dict(size=14, color="#e2e8f0")),
        yaxis_title="百万ドル ($M)",
        xaxis_title="年度",
        height=320,
    )
    fig.update_xaxes(type='category')
    return fig


def create_short_term_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """短期モード用のテクニカルチャート（ローソク足＋5/10/20日線＋出来高）を作成する。"""
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    import pandas as pd
    
    df_plot = df.copy()
    # 欠損日（土日等）を詰めるために日付を文字列として扱う
    if pd.api.types.is_datetime64_any_dtype(df_plot['Date']):
        df_plot['Date_str'] = df_plot['Date'].dt.strftime('%Y-%m-%d')
    else:
        df_plot['Date_str'] = df_plot['Date'].astype(str)

    # MAの計算
    if "MA5" not in df_plot.columns: df_plot["MA5"] = df_plot["Close"].rolling(window=5).mean()
    if "MA10" not in df_plot.columns: df_plot["MA10"] = df_plot["Close"].rolling(window=10).mean()
    if "MA20" not in df_plot.columns:  df_plot["MA20"] = df_plot["Close"].rolling(window=20).mean()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
        subplot_titles=(f"{ticker} 短期トレンドチャート (Short-Term Price Action)", "出来高 (Volume)"),
    )
    
    # 上段: ローソク足
    fig.add_trace(
        go.Candlestick(
            x=df_plot["Date_str"],
            open=df_plot["Open"], high=df_plot["High"],
            low=df_plot["Low"], close=df_plot["Close"],
            name="価格",
            increasing_line_color="#10b981", # 陽線（緑）
            decreasing_line_color="#ef4444", # 陰線（赤）
        ),
        row=1, col=1
    )
    
    # 上段: 移動平均線
    lines = [("MA5", "#38bdf8", "MA 5"), ("MA10", "#facc15", "MA 10"), ("MA20", "#f472b6", "MA 20")]
    for col, color, name in lines:
        sub_df = df_plot.dropna(subset=[col])
        if not sub_df.empty:
            fig.add_trace(
                go.Scatter(x=sub_df["Date_str"], y=sub_df[col], name=name, line=dict(color=color, width=1.5), hoverinfo="skip"),
                row=1, col=1
            )
            
    # 下段: 出来高
    colors = ["#ef4444" if row['Close'] < row['Open'] else "#10b981" for _, row in df_plot.iterrows()]
    fig.add_trace(
        go.Bar(x=df_plot["Date_str"], y=df_plot["Volume"], name="出来高", marker_color=colors),
        row=2, col=1
    )
    
    fig.update_layout(
        **{**PLOTLY_LAYOUT, "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)},
        height=600,
        showlegend=True,
        xaxis_rangeslider_visible=False,
    )
    
    # X軸の表示設定（非営業日の隙間を潰す）
    fig.update_xaxes(type='category', categoryorder='category ascending', nticks=15)
    
    return fig


def create_technical_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """株価 + SMA + RSI のテクニカルチャートを make_subplots で作成。"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{ticker}  終値 & 移動平均線", "RSI（相対力指数）"),
    )

    # --- 上段: 終値 ---
    fig.add_trace(
        go.Scatter(
            x=df["Date"], y=df["Close"],
            name="終値",
            line=dict(color="#60a5fa", width=1.8),
            hovertemplate="%{x|%Y-%m-%d}<br>終値: $%{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # --- SMA50 ---
    sma50 = df.dropna(subset=["SMA50"])
    if not sma50.empty:
        fig.add_trace(
            go.Scatter(
                x=sma50["Date"], y=sma50["SMA50"],
                name="SMA 50",
                line=dict(color="#fbbf24", width=1.3, dash="dash"),
                hovertemplate="%{x|%Y-%m-%d}<br>SMA50: $%{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # --- SMA200 ---
    sma200 = df.dropna(subset=["SMA200"])
    if not sma200.empty:
        fig.add_trace(
            go.Scatter(
                x=sma200["Date"], y=sma200["SMA200"],
                name="SMA 200",
                line=dict(color="#f472b6", width=1.3, dash="dot"),
                hovertemplate="%{x|%Y-%m-%d}<br>SMA200: $%{y:.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # --- 下段: RSI ---
    rsi_data = df.dropna(subset=["RSI"])
    if not rsi_data.empty:
        # RSI の色分け（買われ過ぎ/売られ過ぎ）
        fig.add_trace(
            go.Scatter(
                x=rsi_data["Date"], y=rsi_data["RSI"],
                name="RSI",
                line=dict(color="#a78bfa", width=1.5),
                hovertemplate="%{x|%Y-%m-%d}<br>RSI: %{y:.1f}<extra></extra>",
            ),
            row=2, col=1,
        )

        # 買われ過ぎライン (70)
        fig.add_hline(
            y=70, line_dash="dash", line_color="rgba(248, 113, 113, 0.6)",
            annotation_text="70 (買われ過ぎ)",
            annotation_font_color="#f87171",
            annotation_font_size=10,
            annotation_position="top left",
            row=2, col=1,
        )
        # 売られ過ぎライン (30)
        fig.add_hline(
            y=30, line_dash="dash", line_color="rgba(52, 211, 153, 0.6)",
            annotation_text="30 (売られ過ぎ)",
            annotation_font_color="#34d399",
            annotation_font_size=10,
            annotation_position="bottom left",
            row=2, col=1,
        )

        # RSI 70-100 と 0-30 の背景色
        fig.add_hrect(
            y0=70, y1=100,
            fillcolor="rgba(248, 113, 113, 0.08)", line_width=0,
            row=2, col=1,
        )
        fig.add_hrect(
            y0=0, y1=30,
            fillcolor="rgba(52, 211, 153, 0.08)", line_width=0,
            row=2, col=1,
        )

    # --- レイアウト ---
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#c9d1d9"),
        margin=dict(l=50, r=30, t=60, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=13,
            font_family="Inter, sans-serif",
        ),
        height=600,
        hovermode="x unified",
    )

    # 軸スタイル
    for i in range(1, 3):
        fig.update_xaxes(
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.1)",
            row=i, col=1,
        )
        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.1)",
            row=i, col=1,
        )

    fig.update_yaxes(title_text="株価 ($)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
    fig.update_xaxes(title_text="日付", row=2, col=1)

    # サブタイトルの色
    fig.update_annotations(font_color="#e2e8f0", font_size=14)

    return fig


# ─────────────────────────────────────────────
# AI 分析ロジック
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """\
あなたはウォール街で20年の経験を持つプロの金融アナリストです。
提供された広範なデータ（財務推移、効率性指標、競合比較、アナリストコンセンサス、インサイダー取引、DCFバリュエーション、テクニカル）を多角的に統合分析し、
投資家が意思決定を行うための深い洞察を日本語で提供してください。単なるデータの羅列ではなく、複数の指標間の矛盾や相乗効果についても言及してください。

## 出力フォーマット（必ず Markdown で）

### 💪 強み
- （箇条書き 3〜5 項目）

### ⚠️ 弱み・リスク
- （箇条書き 3〜5 項目）

### 📝 総合コメント
（2〜3文で総合的な見解を述べる）

## ルール
- 必ず **日本語** で回答する
- 具体的な数値を引用して根拠を示す
- 投資推奨・非推奨の断定は避け、あくまで分析に留める
- 簡潔で読みやすい文体にする
"""


def build_analysis_prompt(
    ticker: str,
    data: dict,
    fin: dict | None = None,
    hist_df: pd.DataFrame | None = None,
    adv_fin: dict | None = None,
    peers_df: pd.DataFrame | None = None,
    analyst: dict | None = None,
    dcf_val: float | None = None
) -> str:
    """取得済みデータからLLM用の詳細なユーザープロンプトを組み立てる。"""
    lines = [f"## 銘柄基本情報: {data['name']} ({ticker})"]
    lines.append(f"- セクター: {data.get('sector', '不明')}")
    lines.append(f"- 現在株価: ${data.get('price', '—')}")
    lines.append(f"- 時価総額: ${data.get('market_cap', '—'):,}" if data.get('market_cap') else "- 時価総額: —")
    lines.append(f"- PER: {data.get('pe_ratio', '—')} / PBR: {data.get('pb_ratio', '—')}")
    
    div_yield = data.get('dividend_yield')
    lines.append(f"- 配当利回り: {div_yield:.2f}%" if div_yield is not None else "- 配当利回り: なし/不明")

    # 財務推移
    if fin:
        lines.append("\n## 財務推移（過去数年）")
        if fin.get("dates") and fin.get("revenue"):
            for i, d in enumerate(fin["dates"]):
                rev = fin["revenue"][i]
                ni = f" / 純利益: ${fin['net_income'][i]:,.1f}M" if fin.get("net_income") and i < len(fin["net_income"]) else ""
                lines.append(f"- {d}: 売上高 ${rev:,.1f}M{ni}")

    # 詳細財務指標
    if adv_fin:
        lines.append("\n## 詳細財務指標 (収益性・安全性)")
        lines.append(f"- ROE: {fmt_percent(adv_fin.get('ROE'))} (利益率: {fmt_percent(adv_fin.get('Net Margin'))}, 回転率: {fmt_ratio(adv_fin.get('Asset Turnover'))}, レバレッジ: {fmt_ratio(adv_fin.get('Financial Leverage'))})")
        lines.append(f"- ROIC: {fmt_percent(adv_fin.get('ROIC'))}")
        lines.append(f"- 財務健全性: 自己資本比率 {fmt_percent(adv_fin.get('Equity Ratio'))}, 流動比率 {fmt_percent(adv_fin.get('Current Ratio'))}, D/Eレシオ {fmt_ratio(adv_fin.get('D/E Ratio'))}")
        lines.append(f"- キャッシュフローの質: 営業CF/純利益 {fmt_ratio(adv_fin.get('Operating CF / Net Income'))}")

    # バリュエーション (DCF)
    if dcf_val:
        gap = (dcf_val - data['price']) / data['price'] if data.get('price') else 0
        lines.append(f"\n## バリュエーション (DCF分析)")
        lines.append(f"- 算出された理論株価: ${dcf_val:,.2f} (現在値との乖離: {gap:+.1%})")

    # 競合比較
    if peers_df is not None and not peers_df.empty:
        lines.append("\n## 競合他社比較 (ピアグループ内ランキング)")
        idx_list = peers_df.index[peers_df['ティッカー'] == ticker].tolist()
        if idx_list:
            row = peers_df.iloc[idx_list[0]]
            lines.append(f"- 総合順位: {row.get('総合順位')}位 (全{len(peers_df)}社中)")
        
        peer_summary = "比較対象: " + ", ".join(peers_df['ティッカー'].tolist())
        lines.append(f"- {peer_summary}")

    # アナリスト予想
    if analyst:
        lines.append("\n## 証券アナリスト予想 & コンセンサス")
        lines.append(f"- 目標株価: 平均 ${analyst.get('target_mean', '—')}, 最高 ${analyst.get('target_high', '—')}, 最低 ${analyst.get('target_low', '—')}")
        lines.append(f"- 推奨度 (Recommendation): {analyst.get('recommendation_key', '—')}")
        
        insider = analyst.get("insider")
        if insider is not None and not insider.empty:
            lines.append("\n## インサイダー取引 (直近動向)")
            for _, r in insider.head(3).iterrows():
                lines.append(f"- {r['Start Date']}: {r['Insider']} ({r['Position']}) が {r['Transaction']} - {r['Shares']}株")

    # テクニカル
    if hist_df is not None and not hist_df.empty:
        latest = hist_df.iloc[-1]
        lines.append("\n## テクニカル指標")
        lines.append(f"- RSI(14): {latest.get('RSI', 0):.1f}")
        sma50, sma200 = latest.get("SMA50"), latest.get("SMA200")
        if pd.notna(sma50) and pd.notna(sma200):
            lines.append(f"- SMA50/200クロス: {'ゴールデンクロス' if sma50 > sma200 else 'デッドクロス'}")

    lines.append("\nこれらの多岐にわたるデータを統合し、現在の価格が妥当か、今後の投資機会とリスクはどこにあるかをプロの視点で分析してください。")
    return "\n".join(lines)


def get_gemini_api_key() -> str | None:
    """APIキーを API.txt → st.secrets → 環境変数 → サイドバー入力 の順で取得する。"""
    # 1) API.txt
    api_file = os.path.join(os.path.dirname(__file__), "API.txt")
    if os.path.exists(api_file):
        try:
            with open(api_file, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    # 2) st.secrets
    try:
        key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        if key:
            return key
    except Exception:
        pass

    # 3) 環境変数
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key

    # 4) サイドバー入力
    return None





def render_growth_driver_cards(drivers_data: list):
    """成長ドライバをカード形式で表示する (Streamlit)"""
    num_map = {1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤", 6: "⑥", 7: "⑦"}
    icon_map = {"positive": "◎", "neutral": "△", "critical": "⚠️"}
    
    html_all = ""
    for d in drivers_data:
        driver_id = d.get("id", 1)
        num_icon = num_map.get(driver_id, str(driver_id))
        status = d.get("status", "neutral")
        icon = icon_map.get(status, "△")
        theme = d.get("theme", "")
        impact = d.get("impact", "")
        
        html_card = f"""
        <div class="growth-card status-{status}">
            <div class="growth-card-num">{num_icon}</div>
            <div class="growth-card-content">
                <div class="growth-card-theme">{theme}</div>
                <div class="growth-card-impact">{icon} {impact}</div>
            </div>
        </div>
        """
        html_all += html_card
        
    st.markdown(html_all, unsafe_allow_html=True)


def call_gemini(api_key_ignored: str, system_prompt: str, user_prompt: str) -> str:
    """Gemini API を呼び出してテキストを返す (google-genai 1.0+ 対応)"""
    if not GENAI_AVAILABLE:
        return "AI機能が利用できません（APIキー未設定またはライブラリ不足）。"
    try:
        response = AI_CLIENT.models.generate_content(
            model="gemini-3-flash-preview",
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt
            ),
            contents=user_prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# ─────────────────────────────────────────────
# ユーティリティ・コールバック
# ─────────────────────────────────────────────
def handle_detail_view(ticker):
    """テーマ検索結果から個別分析へ遷移するためのコールバック。"""
    st.session_state.app_mode = "個別銘柄分析"
    st.session_state.active_ticker = ticker


@st.cache_data(ttl=3600)
def get_sector_sentiment_data():
    """全銘柄の成長ドライバーを集計し、セクター別のポジティブ率を算出する。"""
    db_path = os.path.join(os.path.dirname(__file__), "growth_drivers_db.json")
    meta_path = os.path.join(os.path.dirname(__file__), "ticker_metadata.json")
    
    if not os.path.exists(db_path) or not os.path.exists(meta_path):
        return None
        
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            drivers_db = json.load(f)
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        sector_stats = {} # {sector: {"positive": 0, "total": 0}}
        
        for ticker, drivers in drivers_db.items():
            meta = metadata.get(ticker, {})
            sector = meta.get("sector", "Unknown")
            if sector == "Unknown" or not sector:
                continue
                
            if sector not in sector_stats:
                sector_stats[sector] = {"positive": 0, "total": 0}
            
            for d in drivers:
                sector_stats[sector]["total"] += 1
                if d.get("status") == "positive":
                    sector_stats[sector]["positive"] += 1
        
        # DataFrame化
        records = []
        for sector, stats in sector_stats.items():
            if stats["total"] > 0:
                ratio = (stats["positive"] / stats["total"]) * 100
                records.append({
                    "sector_en": sector,
                    "sector_ja": SECTOR_JA_MAP.get(sector, sector),
                    "positive_ratio": ratio,
                    "total_drivers": stats["total"]
                })
        
        df = pd.DataFrame(records)
        return df.sort_values("positive_ratio", ascending=True) # Plotly水平バー用に昇順
    except Exception as e:
        print(f"Sentiment Aggregation Error: {e}")
        return None

def render_sector_sentiment_chart():
    """セクター別センチメントチャートを表示。"""
    st.markdown("### 📊 業種別ポジティブ・センチメント (熱度指数)")
    st.markdown('<div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 20px;">各銘柄の成長ドライバーにおける「Positive」評価の割合を集計。どの業界に将来的な追い風が集中しているかを可視化します。</div>', unsafe_allow_html=True)
    
    df = get_sector_sentiment_data()
    if df is None or df.empty:
        st.info("データ集計中です...")
        return

    # 熱いセクターの上位表示用
    top_sectors = df.sort_values("positive_ratio", ascending=False).head(3)
    cols = st.columns(3)
    for i, (_, row) in enumerate(top_sectors.iterrows()):
        cols[i].metric(
            label=f"🔥 Hot Sector #{i+1}",
            value=row["sector_ja"],
            delta=f"{row['positive_ratio']:.1f}% Positive"
        )
    
    # Plotlyチャート作成
    fig = go.Figure()
    
    # カラーグラデーションの設定 (Blue -> Red)
    colors = []
    for val in df["positive_ratio"]:
        # 0 - 100 を 0 - 1 に正規化
        norm = val / 100
        # 簡易的なグラデーション計算 (R, G, B)
        r = int(255 * norm)
        b = int(255 * (1 - norm))
        colors.append(f"rgb({r}, 100, {b})")

    fig.add_trace(go.Bar(
        y=df["sector_ja"],
        x=df["positive_ratio"],
        orientation='h',
        marker=dict(
            color=df["positive_ratio"],
            colorscale="Viridis", # または自作カスタム
            line=dict(color='rgba(255, 255, 255, 0.1)', width=1)
        ),
        hovertemplate="<b>%{y}</b><br>熱度: %{x:.1f}%<br>解析ドライバー数: %{customdata}<extra></extra>",
        customdata=df["total_drivers"]
    ))

    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(
        height=500,
        xaxis_title="ファンダメンタル熱度 (Positive比率 %)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=10, b=40)
    )
    fig.update_xaxes(range=[0, 100])
    
    st.plotly_chart(fig, use_container_width=True)
    st.divider()


def render_sector_analyzer():
    """セクター分析画面を表示。"""
    st.title("📊 Sector Analyzer")
    st.markdown('<div class="subtitle">業種別のファンダメンタル・センチメントを分析し、資金の流入・流出を予測します</div>', unsafe_allow_html=True)
    render_sector_sentiment_chart()


def render_theme_explorer():
    """テーマ・キーワード検索画面を表示。"""
    st.title("🔭 Theme Explorer")
    st.markdown('<div class="subtitle">データベースを横断検索し、共通の成長要因を持つ銘柄を炙り出します</div>', unsafe_allow_html=True)
    
    # DBの読み込み
    drivers_db = {}
    db_path = os.path.join(os.path.dirname(__file__), "growth_drivers_db.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                drivers_db = json.load(f)
        except Exception:
            pass

    if not drivers_db:
        st.error("データベース (growth_drivers_db.json) が読み込めませんでした。")
        return

    # クイック検索タグ
    st.markdown("##### 🏷️ 人気のキーワード")
    tags = ["AI", "半導体", "データセンター", "クラウド", "自動運転", "セキュリティ", "原子力", "iPhone", "EV", "広告", "中国"]
    tag_cols = st.columns(len(tags))
    for i, tag in enumerate(tags):
        if tag_cols[i].button(tag, use_container_width=True):
            st.session_state.theme_search_query = tag
            st.rerun()

    # 検索入力
    search_query = st.text_input("🔍 キーワード検索 (部分一致)", key="theme_search_query", placeholder="例: データセンター, 核融合, サイバーセキュリティ, 量子...")

    if search_query:
        query = search_query.lower()
        results = []
        for t, drivers in drivers_db.items():
            for d in drivers:
                if query in d.get("theme", "").lower() or query in d.get("impact", "").lower():
                    results.append({
                        "ticker": t,
                        "theme": d.get("theme"),
                        "impact": d.get("impact"),
                        "status": d.get("status", "neutral")
                    })
        
        if results:
            st.success(f"**{len(results)}** 件の成長ドライバが一致しました。")
            
            # 結果表示
            for i, res in enumerate(results):
                with st.container():
                    col_card, col_btn = st.columns([5, 1])
                    with col_card:
                        st.markdown(f"""
                        <div class="theme-card">
                            <div class="theme-card-header">
                                <span class="theme-ticker">{res['ticker']}</span>
                                <span class="theme-name">{res['theme']}</span>
                            </div>
                            <div class="theme-match">
                                <b>【分析結果】</b>: {res['impact']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_btn:
                        st.write("<br>" * 2, unsafe_allow_html=True)
                        st.button(
                            "詳細分析 ➔", 
                            key=f"go_{res['ticker']}_{i}", 
                            on_click=handle_detail_view, 
                            args=(res['ticker'],)
                        )
        else:
            st.warning(f"🔍 『{search_query}』に一致するテーマは見つかりませんでした。別のキーワード（日本語・英語）をお試しください。")


def render_top_summary_cards(ticker: str, data: dict):
    """
    最上部（タブ群の上）で個別銘柄の重要ステータスを一瞬で把握するためのサマリー帯。
    データが存在しない項目は「—」で流す。
    """
    try:
        with st.spinner("分析サマリーをロード中..."):
            cio_inputs  = build_cio_decision_inputs(ticker)
        
        scores      = cio_inputs.get("scores", {})
        total_score = cio_inputs.get("total_score", "—")
        
        # AI/ジャッジ系の情報を抽出
        final_judge = derive_final_judgment(cio_inputs, ticker, data)
        verdict_ja  = final_judge.get("verdict_ja", "—")
        
        # Weinstein Stage
        stage = "—"
        if "weinstein" in cio_inputs.get("details", {}):
            ws = cio_inputs["details"]["weinstein"]
            ws_stg = ws.get('stage', 'Stage ?')
            if ws_stg in ("Unknown", "?", ""):
                ws_stg = "Stage ?"
            stage = f"{ws_stg} {ws.get('sub_stage', '')}".strip()
            
        # Entry Timing
        entry_status = "—"
        if "entry_timing" in cio_inputs.get("details", {}):
            et = cio_inputs["details"]["entry_timing"]
            st_text = et.get("entry_status_label_ja", "—")
            # 少し文字列を詰める
            entry_status = st_text.replace("️", "").replace(" ", "").split("（")[0][:6] 
            
        # RS
        rs_score = scores.get("rs_score", "—")
        if isinstance(rs_score, (int, float)): rs_score = f"{int(rs_score)}"
            
        # Event Risk
        event_status = "—"
        if "event_safety_score" in scores:
            score = scores["event_safety_score"]
            if score >= 70: event_status = "🟢 低(安全)"
            elif score >= 40: event_status = "🟡 中(注意)"
            else: event_status = "🔴 高(警戒)"
            
        # Expected Value
        ev_str = "—"
        scenario_res = calculate_scenario_expected_value(ticker, data, cio_inputs)
        if scenario_res and scenario_res.get("expected_value_status") != "error":
            ev_pct = scenario_res.get("expected_value_pct", 0)
            ev_str = f"{ev_pct:+.1f}%"
            
        st.markdown("<div style='padding: 12px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        cols = st.columns(7)
        cols[0].metric("CIO 点数", f"{total_score}")
        cols[1].metric("AI 判定", verdict_ja.replace("️",""))
        cols[2].metric("Stage", stage)
        cols[3].metric("Entry", entry_status)
        cols[4].metric("RS", rs_score)
        cols[5].metric("Event", event_status)
        cols[6].metric("EV (期待値)", ev_str)
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:
        # 全体を壊さないようにフォールバック
        pass

def render_trading_decision_summary(ticker: str, data: dict):
    """
    タブ展開前に、売買判断に必要な要点を短く箇条書きでまとめるセクション。
    """
    try:
        import streamlit as st
        cio_inputs = build_cio_decision_inputs(ticker)
        
        # 1. ステージ
        stage_text = "取得不可"
        if "weinstein" in cio_inputs.get("details", {}):
            ws = cio_inputs["details"]["weinstein"]
            stage_text = f"{ws.get('stage', '')} {ws.get('sub_stage', '')}".strip()
            
        # 2. RS
        rs_text = "取得不可"
        if "rs" in cio_inputs.get("details", {}):
            status_map = {"strong": "強い (Strong)", "neutral": "中立 (Neutral)", "weak": "弱い (Weak)"}
            rs_status = cio_inputs["details"]["rs"].get("rs_status", "neutral")
            rs_text = status_map.get(rs_status, "不明")
            
        # 3. エントリー
        entry_text = "取得不可"
        if "entry_timing" in cio_inputs.get("details", {}):
            entry_text = cio_inputs["details"]["entry_timing"].get("entry_status_label_ja", "不明")
            
        # 4. イベント
        evt_score = cio_inputs.get("scores", {}).get("event_safety_score", 50)
        if evt_score >= 70: event_text = "通過済みまたは低リスク"
        elif evt_score >= 40: event_text = "直近イベントあり注意"
        else: event_text = "高リスク（決算直前など）"
            
        # 5. シナリオ期待値
        scenario_res = calculate_scenario_expected_value(ticker, data, cio_inputs)
        ev_text = "取得不可"
        if scenario_res and scenario_res.get("expected_value_status") != "error":
            ev_text = f"ベースケース上値 {scenario_res.get('base_upside_pct', 0):+.1f}% (総合期待値 {scenario_res.get('expected_value_pct', 0):+.1f}%)"
            
        # 6. 銘柄タイプ (Playbook)
        pb = determine_stock_playbook(ticker, cio_inputs)
        pb_text = pb.get("stock_playbook_type_label_ja", "不明")

        st.markdown("##### 📝 現在の売買判断サマリー")
        with st.container(border=True):
            st.markdown(f"""
- **現在のトレンド**: {stage_text}
- **RS (相対強度)**: {rs_text}
- **エントリー判定**: {entry_text}
- **銘柄タイプ**: {pb_text}
- **イベントリスク**: {event_text}
- **シナリオ期待値**: {ev_text}
            """)
    except Exception as e:
        pass

def evaluate_short_term_breakout(df: pd.DataFrame) -> dict:
    """日足データから短期ブレイク状態を判定する"""
    if df is None or len(df) < 25:
        return {"short_breakout_status": "none", "short_breakout_status_label_ja": "取得不可", "comment": "十分なデータがありません。", "reason": []}

    # 指標計算
    current_idx = -1
    current_price = df["Close"].iloc[current_idx]
    current_vol = df["Volume"].iloc[current_idx]
    
    # 直近20日高値 (今日を除外した過去20日間)
    hist_20 = df.iloc[-21:-1]
    high_20 = hist_20["High"].max()
    
    # 出来高20日平均
    vol_ma20 = hist_20["Volume"].mean()
    vol_ratio = current_vol / vol_ma20 if vol_ma20 > 0 else 0
    
    # MA計算
    ma5 = df["Close"].rolling(window=5).mean().iloc[current_idx]
    ma10 = df["Close"].rolling(window=10).mean().iloc[current_idx]
    ma20 = df["Close"].rolling(window=20).mean().iloc[current_idx]
    
    # 条件判定
    is_above_high = current_price > high_20
    is_near_high = current_price > high_20 * 0.985
    good_vol = vol_ratio > 1.2
    bullish_ma = ma5 > ma10 > ma20
    
    res = {
        "status_id": "monitor",
        "label": "監視",
        "score": 50,
        "reason": [],
        "high_20": high_20,
        "vol_ratio": vol_ratio,
        "dist_to_high_pct": (current_price / high_20 - 1) * 100
    }
    
    if is_above_high and good_vol and bullish_ma:
        res.update({"status_id": "breakout_candidate", "label": "ブレイク候補 🚀", "score": 90})
        res["reason"] = ["株価が20日高値を上抜け", "出来高が20日平均を1.2倍以上上回る", "5日・10日・20日線がパーフェクトオーダー"]
    elif is_near_high and bullish_ma:
        res.update({"status_id": "breakout_approaching", "label": "ブレイク接近 📈", "score": 75})
        res["reason"] = ["株価が20日高値に接近中", "短期移動平均線が上向きの並び"]
    elif current_price < ma20 or ma5 < ma10:
        res.update({"status_id": "pass", "label": "見送り ⚖️", "score": 20})
        res["reason"] = ["短期トレンドが崩れている", "20日線を下回っている"]
    else:
        res.update({"status_id": "monitor", "label": "監視 👁️", "score": 50})
        res["reason"] = ["トレンドは崩れていないが、明確なブレイクセットアップ以前"]
    
    # コメント生成
    if res["status_id"] == "breakout_candidate":
        res["comment"] = "短期的にはブレイク仕掛け候補として監視・エントリー検討が可能な状態。"
    elif res["status_id"] == "breakout_approaching":
        res["comment"] = "高値更新準備中。出来高を伴う上抜けが発生するか、あるいは押し目を形成するかを注視。"
    elif res["status_id"] == "pass":
        res["comment"] = "トレンドが弱く、短期トレードの対象とはなりにくい局面です。"
    else:
        res["comment"] = "現時点では明確な短期ブレイクセットアップは見られません。"
        
    return res

def calculate_short_term_snapshot(ticker: str, data: dict) -> dict:
    """短期モード用の重要指標を計算して返す"""
    res = {
        "price": data.get("price"),
        "chg_pct": None,
        "high_dist": None,
        "vol_ratio": None,
        "trend": "—",
        "judgment": "未実装"
    }
    
    # 前日比%
    P = data.get("price")
    prev_P = data.get("prev_close")
    if P and prev_P and prev_P > 0:
        res["chg_pct"] = (P / prev_P - 1) * 100
        
    # 高値からの距離
    h52 = data.get("fifty_two_week_high")
    if P and h52 and h52 > 0:
        res["high_dist"] = (P / h52 - 1) * 100
        
    # 直近出来高倍率 (10日平均 / 3ヶ月平均)
    v10 = data.get("avg_vol_10d")
    v3m = data.get("avg_vol_3m")
    if v10 and v3m and v3m > 0:
        res["vol_ratio"] = v10 / v3m
        
    # 短期トレンド (既存のキャッシュ済み日足履歴を流用して 20日SMA と比較)
    hist = fetch_price_history(ticker, "6mo")
    if hist is not None and not hist.empty and len(hist) >= 20:
        try:
            sma20 = hist["Close"].rolling(window=20).mean().iloc[-1]
            current = hist["Close"].iloc[-1]
            # 簡易判定
            if current > sma20 * 1.015:
                res["trend"] = "上向き ↗"
            elif current < sma20 * 0.985:
                res["trend"] = "下向き ↘"
            else:
                res["trend"] = "横ばい →"
                
            # --- 短期ブレイク判定の呼び出し ---
            breakout_res = evaluate_short_term_breakout(hist)
            res["judgment"] = breakout_res.get("label", "不明")
            res["breakout_details"] = breakout_res
            # --------------------------------

            # --- VWAP/ギャップ判定の呼び出し ---
            vwap_res = evaluate_short_term_vwap_gap(data)
            res["vwap_details"] = vwap_res
            # --------------------------------

            # --- 短期セットアップ総合判定の呼び出し ---
            setup_res = evaluate_short_term_setup(data, breakout_res, vwap_res, res["trend"])
            res["setup_details"] = setup_res
            res["judgment"] = setup_res.get("label", "不明")
            # --------------------------------

            # --- 短期ウォッチ条件判定の呼び出し ---
            watchlist_res = evaluate_short_term_watchlist_conditions(data, breakout_res, vwap_res, res["trend"])
            res["watchlist_details"] = watchlist_res
            # --------------------------------

            # --- 短期アラート条件の呼び出し ---
            alert_res = evaluate_short_term_alert_conditions(data, breakout_res, vwap_res, res["trend"], setup_res)
            res["alert_details"] = alert_res
            # --------------------------------
        except Exception:
            pass
            
    return res

def evaluate_short_term_alert_conditions(data: dict, breakout_res: dict, vwap_res: dict, trend_label: str, setup_res: dict) -> dict:
    """注目すべき上下のトリガー条件を整理する"""
    upside = []
    downside = []
    
    # 20日高値
    h20 = breakout_res.get("high_20", 0)
    if breakout_res.get("status_id") == "breakout_candidate":
        upside.append(f"20日高値(${h20:.2f})を上放れ継続")
    else:
        upside.append(f"20日高値(${h20:.2f})を明確に突破")
        
    # VWAP
    vwap_val = vwap_res.get("vwap_approx", 0)
    if vwap_res.get("status_id") in ["strong_today", "gap_monitor"]:
        upside.append("当日VWAP上での推移を維持")
        downside.append(f"VWAP(${vwap_val:.2f})を明確に割り込み")
    else:
        upside.append(f"VWAP(${vwap_val:.2f})を上抜けて安定")
        downside.append("VWAP下での推移継続（弱気圏）")

    # 出来高
    upside.append("出来高倍率 1.2x以上の維持または再加速")
    
    # 当日動向
    downside.append("当日高値を更新できず失速")
    if data.get("price", 0) < data.get("open", 0):
        downside.append("寄り付き価格を回復できず（陰線化）")
    else:
        downside.append("寄り付き価格(Open)を割り込み")

    # トレンド
    downside.append("5日移動平均線を下抜け")
    downside.append("20日移動平均線を割り込み（トレンド転換）")

    # 優先度
    score = setup_res.get("score", 0)
    priority = "low"
    label = "監視優先度：低"
    if score >= 75:
        priority = "high"; label = "監視優先度：最高 🔥"
    elif score >= 50 or breakout_res.get("status_id") == "breakout_approaching":
        priority = "medium"; label = "監視優先度：中 👁️"

    return {
        "alert_priority": priority,
        "alert_priority_label_ja": label,
        "upside_alerts": upside[:3],
        "downside_alerts": downside[:3],
        "primary_trigger": upside[0],
        "primary_risk_trigger": downside[0],
        "comment": "セットアップ完成間近のため、最上位トリガーを注視。" if priority == "high" else "条件が整うまで、上下の境界線を監視。"
    }

def evaluate_short_term_watchlist_conditions(data: dict, breakout_res: dict, vwap_res: dict, trend_label: str) -> dict:
    """現在の状態に対して足りない条件と仕掛けトリガーを特定する"""
    conditions = [
        {"id": "breakout", "label": "20日高値更新 (ブレイク)", "met": breakout_res.get("status_id") == "breakout_candidate"},
        {"id": "volume", "label": "出来高倍率 1.2x以上", "met": breakout_res.get("vol_ratio", 0) >= 1.2},
        {"id": "vwap", "label": "VWAP上を維持", "met": vwap_res.get("status_id") in ["strong_today", "gap_monitor"]},
        {"id": "trend", "label": "5/10/20日線 パーフェクトオーダー", "met": "上向き" in trend_label},
        {"id": "gap_hold", "label": "当日寄り付き価格を維持", "met": data.get("price", 0) >= data.get("open", 0)}
    ]
    
    met_count = sum(1 for c in conditions if c["met"])
    missing = [c["label"] for c in conditions if not c["met"]]
    
    # ステータス決定
    status_id = "monitor"
    label = "監視継続"
    if met_count == 5:
        status_id = "setup_ready"
        label = "条件ほぼ完成"
    elif met_count == 4:
        status_id = "one_missing"
        label = "仕掛け条件まであと1つ"
    elif met_count == 3:
        status_id = "two_missing"
        label = "仕掛け条件まであと2つ"
    elif met_count <= 1:
        status_id = "far"
        label = "条件不足大"

    # 次のトリガーとアクション
    next_trigger = "条件不足のため、まずはトレンドの転換待ち"
    action = "全条件の充足を待ってから仕掛けを検討"
    
    if missing:
        if "20日高値更新 (ブレイク)" in missing:
            next_trigger = "直近20日高値の上抜けを出来高伴って確認"
            action = "ブレイク時にVWAP上であれば打診買い検討"
        elif "出来高倍率 1.2x以上" in missing:
            next_trigger = "価格維持したまま、出来高の急増を確認"
            action = "エネルギーが乗ってくれば本格エントリー"
        elif "VWAP上を維持" in missing:
            next_trigger = "VWAPラインへの回帰と反発を確認"
            action = "当日の平均コストを上回るまでは静観"
        else:
            next_trigger = f"{missing[0]}の充足を確認"
            action = "セットアップ完成を待つ"
    else:
        next_trigger = "セットアップ完成済み。エントリータイミングを精査"
        action = "現在値でのリスクリワードを考慮してエントリー"

    return {
        "status_id": status_id,
        "label": label,
        "conditions": conditions,
        "missing_conditions": missing,
        "next_trigger": next_trigger,
        "action_if_triggered": action,
        "met_count": met_count,
        "total_count": len(conditions)
    }

def evaluate_short_term_vwap_gap(data: dict) -> dict:
    """当日データから簡易的なVWAP / ギャップ状態を判定する"""
    # 簡易VWAP (Typical Price)
    P = data.get("price")
    H = data.get("day_high")
    L = data.get("day_low")
    O = data.get("open")
    prev_C = data.get("prev_close")
    
    # yfinanceのデータが不完全な場合のガード
    if not all([P, H, L, O, prev_C]):
        return {"status_id": "none", "label": "データ不足", "score": 0, "reason": ["必要な当日データ(OHLC)が取得できませんでした。"]}

    vwap_approx = (H + L + P) / 3
    gap_pct = (O / prev_C - 1) * 100 if prev_C > 0 else 0
    price_vs_vwap_pct = (P / vwap_approx - 1) * 100 if vwap_approx > 0 else 0
    
    res = {
        "status_id": "neutral",
        "label": "中立",
        "score": 50,
        "gap_pct": gap_pct,
        "vwap_approx": vwap_approx,
        "price_vs_vwap_pct": price_vs_vwap_pct,
        "reason": [],
        "comment": ""
    }
    
    # 判定ロジック
    is_gap_up = gap_pct >= 0.5
    is_strong_gap = gap_pct >= 2.0
    is_above_vwap = P > vwap_approx * 1.002
    is_holding_gap = P >= O # 寄り付き価格を維持
    
    if is_gap_up and is_above_vwap and is_holding_gap:
        res.update({"status_id": "strong_today", "label": "当日強い 🔥", "score": 85})
        res["reason"] = ["ギャップアップで寄り付き", "現在値がVWAPを上回る", "寄り付き価格を維持（ギャップ維持）"]
    elif is_gap_up:
        res.update({"status_id": "gap_monitor", "label": "ギャップ監視 👀", "score": 65})
        res["reason"] = ["ギャップアップしているがVWAP付近で攻防中"]
    elif P < vwap_approx * 0.998 and P < O:
        res.update({"status_id": "weak", "label": "弱い ⚠️", "score": 30})
        res["reason"] = ["VWAPを下回る推移", "寄り付き後に失速"]
        
    # コメント
    if res["status_id"] == "strong_today":
        res["comment"] = "当日の資金流入が強く、高値圏で安定した買い優勢の展開です。"
    elif res["status_id"] == "weak":
        res["comment"] = "寄り付き後の売り圧力が強く、短期的な警戒が必要な状態です。"
    else:
        res["comment"] = "方向感を探る展開です。VWAPを支えに反発できるか、あるいは割り込むかを注視。"
        
    return res

def evaluate_short_term_setup(data: dict, breakout_res: dict, vwap_res: dict, trend_label: str) -> dict:
    """短期ブレイク判定、VWAP、トレンドを統合して総合評価を行う"""
    score = 0
    reasons = []
    
    # 1. ブレイク要素 (最大30)
    b_id = breakout_res.get("status_id")
    if b_id == "breakout_candidate": score += 30; reasons.append("20日高値ブレイク成立中")
    elif b_id == "breakout_approaching": score += 20; reasons.append("20日高値に接近・準備中")
    elif b_id == "monitor": score += 10
    
    # 2. VWAP要素 (最大20)
    v_id = vwap_res.get("status_id")
    if v_id == "strong_today": score += 20; reasons.append("当日VWAPを鮮明に上抜け")
    elif v_id == "gap_monitor": score += 10
    elif v_id == "weak": score -= 20; reasons.append("当日VWAPを下回る弱気推移")
    
    # 3. トレンド/MA要素 (最大20)
    if "上向き" in trend_label: score += 20; reasons.append("短期移動平均線が良好な並び")
    elif "横ばい" in trend_label: score += 5
    elif "下向き" in trend_label: score -= 20; reasons.append("短期トレンドが下向き")
    
    # 4. 出来高要素 (最大15)
    vol_ratio = breakout_res.get("vol_ratio", 0)
    if vol_ratio > 1.5: score += 15; reasons.append("出来高が極めて強い")
    elif vol_ratio > 1.1: score += 10; reasons.append("出来高が平均を上回る")
    
    # 5. ギャップ維持 (最大15)
    gap_pct = vwap_res.get("gap_pct", 0)
    p_vs_v = vwap_res.get("price_vs_vwap_pct", 0)
    if gap_pct > 1.0 and p_vs_v > 0.5: score += 15; reasons.append("ギャップアップ後の強さを維持")
    
    score = max(0, min(100, score))
    
    # ステータス決定
    status_id = "monitor"
    label = "監視 👁️"
    action = "仕掛け条件を待機。現状は一部のシグナルが不足しています。"
    risk = "直近安値やVWAP割れを撤退基準に設定。"
    
    if score >= 75:
        status_id = "setup_candidate"
        label = "仕掛け候補 🚀"
        action = "短期的には絶好のセットアップ。出来高の維持を確認しつつエントリー検討。"
        risk = "当日安値または20日移動平均線を最終防衛ラインに。"
    elif score >= 55:
        if "上向き" in trend_label and b_id == "breakout_candidate":
             status_id = "buy_the_dip"
             label = "押し待ち ⏳"
             action = "トレンドは強いが当日は過熱気味。一段の押し目を待ってからの参入が有利。"
             risk = "高値での飛び乗りによる「振るい落とし」に注意。"
        else:
             status_id = "monitor"
             label = "監視 👁️"
             action = "トレンドは悪くないが、爆発的なエネルギー待ちの状態。"
    elif score < 35:
        status_id = "pass"
        label = "見送り ⚖️"
        action = "短期的な優位性がなく、リスクが高い局面。他の銘柄を優先。"
        risk = "底なしの下落やダラダラ下げに巻き込まれないよう注意。"
        
    return {
        "status_id": status_id,
        "label": label,
        "score": score,
        "reasons": reasons,
        "action_hint": action,
        "risk_hint": risk,
        "trend_label": trend_label
    }

def render_short_term_summary_cards(ticker: str, data: dict, snap: dict = None):
    """短期モード用の横並びサマリーカードを描画する"""
    import streamlit as st
    
    if snap is None:
        with st.spinner("短期スナップショットを取得中..."):
            snap = calculate_short_term_snapshot(ticker, data)
        
    st.markdown("<div style='padding: 12px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
    cols = st.columns(6)
    
    p_str = f"${snap['price']:.2f}" if snap['price'] else "—"
    cols[0].metric("現在値", p_str)
    
    chg_str = f"{snap['chg_pct']:+.2f}%" if snap['chg_pct'] is not None else "—"
    cols[1].metric("前日比", chg_str)
    
    hd_str = f"{snap['high_dist']:+.1f}%" if snap['high_dist'] is not None else "—"
    cols[2].metric("高値距離", hd_str)
    
    vr_str = f"{snap['vol_ratio']:.2f}x" if snap['vol_ratio'] is not None else "—"
    cols[3].metric("出来高倍率", vr_str)
    
    cols[4].metric("短期トレンド", snap['trend'])
    cols[5].metric("短期判定", snap['judgment'])
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_short_term_setup_panel(snap: dict):
    """短期セットアップ総合判定の詳細パネルを表示する"""
    import streamlit as st
    if "setup_details" not in snap:
        return
        
    det = snap["setup_details"]
    
    # 判定によって背景色を変更
    bg_color = "rgba(16,185,129,0.05)" # 緑系 (仕掛け候補, 押し待ち)
    border_color = "rgba(16,185,129,0.2)"
    if det["status_id"] == "pass":
        bg_color = "rgba(239,68,68,0.05)" # 赤系 (見送り)
        border_color = "rgba(239,68,68,0.2)"
    elif det["status_id"] == "monitor":
        bg_color = "rgba(249,115,22,0.05)" # オレンジ系 (監視)
        border_color = "rgba(249,115,22,0.2)"

    st.markdown(f"""
        <div style='padding: 20px; background: {bg_color}; border-radius: 12px; border: 2px solid {border_color}; margin-bottom: 24px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div style='font-size: 1.5rem; font-weight: 700; color: #f8fafc;'>
                    総合判定: <span style='color: #10b981;'>{det['label']}</span>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 0.8rem; color: #94a3b8;'>セットアップスコア</div>
                    <div style='font-size: 2rem; font-weight: 800; color: #10b981;'>{det['score']}<span style='font-size: 1rem;'> pts</span></div>
                </div>
            </div>
            <div style='margin-top: 15px; grid-template-columns: 1fr 1fr; display: grid; gap: 20px;'>
                <div>
                    <div style='font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 5px;'>💡 アクション方針</div>
                    <div style='font-size: 0.95rem; color: #e2e8f0;'>{det['action_hint']}</div>
                </div>
                <div>
                    <div style='font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 5px;'>⚠️ リスク管理</div>
                    <div style='font-size: 0.95rem; color: #e2e8f0;'>{det['risk_hint']}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_short_term_breakout_panel(snap: dict):
    """短期ブレイク判定の詳細パネルを表示する"""
    import streamlit as st
    if "breakout_details" not in snap:
        return
        
    det = snap["breakout_details"]
    
    with st.container(border=True):
        st.markdown(f"##### 🚀 短期ブレイク判定: {det.get('label', '—')}")
        c1, c2, c3 = st.columns([1, 1, 3])
        c1.metric("判定スコア", f"{det.get('score', 0)}")
        c2.metric("20日高値", f"${det.get('high_20', 0):.2f}")
        c3.markdown(f"**分析コメント:**  \n{det.get('comment', '')}")
        
        if det.get("reason"):
            st.markdown("**判定理由:**")
            reason_html = "".join([f"<span style='background:rgba(16,185,129,0.1); color:#10b981; padding:2px 8px; border-radius:4px; margin-right:8px; font-size:0.85rem;'>✅ {r}</span>" for r in det["reason"]])
            st.markdown(reason_html, unsafe_allow_html=True)

def render_short_term_vwap_panel(snap: dict):
    """短期VWAP/ギャップ判定の詳細パネルを表示する"""
    import streamlit as st
    if "vwap_details" not in snap:
        return
        
    det = snap["vwap_details"]
    
    with st.container(border=True):
        st.markdown(f"##### 💹 寄り付き・VWAP分析: {det.get('label', '—')}")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        c1.metric("ギャップ率", f"{det.get('gap_pct', 0):+.2f}%")
        c2.metric("VWAP乖離", f"{det.get('price_vs_vwap_pct', 0):+.2f}%")
        c3.metric("判定スコア", f"{det.get('score', 0)}")
        c4.markdown(f"**分析コメント:**  \n{det.get('comment', '')}")
        
        if det.get("reason"):
            st.markdown("**判定ポイント:**")
            reason_html = "".join([f"<span style='background:rgba(56,189,248,0.1); color:#38bdf8; padding:2px 8px; border-radius:4px; margin-right:8px; font-size:0.85rem;'>🔹 {r}</span>" for r in det["reason"]])
            st.markdown(reason_html, unsafe_allow_html=True)

def get_analysis_style_mode() -> str:
    """
    中長期モード/短期モード の表示切替用UIを生成し、選択されたモードを返す。
    """
    import streamlit as st
    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
    mode = st.radio(
        "⏱️ 分析スタイル",
        options=["中長期モード", "短期モード"],
        index=0,
        horizontal=True,
        help="中長期: ファンダメンタルズやトレンド分析を含むフル機能です。\n短期: 短期トレード向けの機能を今後拡張していくモードです。"
    )
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    return mode

def get_analysis_display_mode() -> str:
    """
    かんたんモード/詳細モード の表示切替用UIを生成し、選択されたモードを返す。
    """
    import streamlit as st
    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
    mode = st.radio(
        "🔎 表示モード",
        options=["かんたんモード", "詳細モード"],
        index=0,
        horizontal=True,
        help="かんたん: 売買判断に必要な重要タブのみを表示します。\n詳細: 全ての分析タブを表示します。"
    )
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    return mode

def render_stock_analyzer():
    """個別銘柄の詳細分析画面を表示。"""
    st.title("Momentum Master US")
    st.markdown('<div class="subtitle">AI-Powered Institutional Grade Stock Analysis Dashboard</div>', unsafe_allow_html=True)

    # 入力ソース
    ticker = st.text_input("📈 分析したいティッカーを入力", key="active_ticker", help="例: NVDA, AVGO, TSLA").upper()
    
    if ticker:
        with st.spinner(f"{ticker} のデータを取得中..."):
            data, error_detail = fetch_stock_data(ticker)
            
        if not data:
            st.error(f"❌ '{ticker}' のデータが見つかりませんでした。")
            if error_detail:
                with st.expander("🛠️ エラーの詳細を確認する"):
                    st.code(error_detail, language="text")
                    st.info("💡 ヒント: ティッカーが正しいか、ネットワーク接続、または yfinance の一時的な制限を確認してください。")
        else:
            # yfinanceに表示用セクター名等を追加
            data["sector_display"] = SECTOR_JA_MAP.get(data.get("sector"), data.get("sector"))
            data["industry_display"] = INDUSTRY_JA_MAP.get(data.get("industry"), data.get("industry"))

            # ヘッダー情報
            st.markdown(f'<div class="company-name">{data["name"]} ({ticker})</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="company-sector">{data["sector_display"]} | {data["industry_display"]} | {data["exchange"]}</div>', unsafe_allow_html=True)
            
            # --- 分析スタイル切替 ---
            style_mode = get_analysis_style_mode()
            
            tab_basic = tab_fund = tab_chart = tab_peers = tab_canslim = tab_sepa = tab_weinstein = tab_rs = tab_entry = tab_earnings = tab_sd = tab_val = tab_scenario = tab_event = tab_risk = tab_cio = tab_playbook = tab_ai_final = None

            if style_mode == "中長期モード":
                # 最上部サマリーカード帯
                render_top_summary_cards(ticker, data)
                
                # ─── タブ切り替え ───
                display_mode = get_analysis_display_mode()
                
                # 売買判断サマリーの表示
                render_trading_decision_summary(ticker, data)

                if display_mode == "かんたんモード":
                    tabs = st.tabs([
                        "📊 基本情報", "🔍 チャート", "📈 ステージ分析", "⚡ RS分析", "⏱ エントリー判定", "🎯 CIO判断", "✅ AIジャッジ"
                    ])
                    tab_basic, tab_chart, tab_weinstein, tab_rs, tab_entry, tab_cio, tab_ai_final = tabs
                else:
                    tabs = st.tabs([
                        "📊 基本情報", "🔍 チャート", "📈 財務/バリュ", "🏢 競合比較", "📈 ステージ分析", "🏆 SEPA分析", "⚡ RS分析", "⏱ エントリー判定", "🎲 シナリオ分析", "🗂️ 銘柄タイプ", "🧾 決算品質", "⚖️ 需給分析", "📏 バリュエーション帯", "📅 イベントリスク", "🛡️ リスク/予想", "💰 CAN SLIM", "🎯 CIO判断", "✅ AIジャッジ"
                    ])
                    (tab_basic, tab_chart, tab_fund, tab_peers, tab_weinstein, tab_sepa, tab_rs, tab_entry, tab_scenario, tab_playbook, tab_earnings, tab_sd, tab_val, tab_event, tab_risk, tab_canslim, tab_cio, tab_ai_final) = tabs
            else:
                # 短期データ取得
                with st.spinner("短期データを解析中..."):
                    snap = calculate_short_term_snapshot(ticker, data)

                # 短期サマリーカード表示
                render_short_term_summary_cards(ticker, data, snap=snap)
                
                # --- 短期総合判定 (最も重要なジャッジを最上部に) ---
                render_short_term_setup_panel(snap)
                
                # 判定の根拠を横並びで表示
                col_left, col_right = st.columns(2)
                with col_left:
                     # 短期ブレイク詳細表示
                     render_short_term_breakout_panel(snap)
                with col_right:
                     # 短期VWAP詳細表示
                     render_short_term_vwap_panel(snap)
                
                # 短期AIジャッジの表示
                render_short_term_ai_judge(ticker, data, snap)
                
                # 短期ウォッチリスト条件表示
                render_short_term_watchlist_panel(snap)
                
                # 短期アラート条件表示
                render_short_term_alert_panel(snap)

                # 短期モード
                tabs = st.tabs(["📊 基本情報", "🔍 チャート"])
                tab_basic, tab_chart = tabs

            # 1. 基本情報
            if tab_basic:
                with tab_basic:
                    st.divider()
                
                    # --- 成長ドライバ・データベースの読み込み ---
                    drivers_db = {}
                    db_path = os.path.join(os.path.dirname(__file__), "growth_drivers_db.json")
                    if os.path.exists(db_path):
                        try:
                            with open(db_path, "r", encoding="utf-8") as f:
                                drivers_db = json.load(f)
                        except Exception:
                            pass
                    # ----------------------------------------
    
                    st.markdown('<div class="section-title">🏢 事業紹介 (日本語訳)</div>', unsafe_allow_html=True)
                    with st.spinner("事業概要を翻訳中..."):
                        summary = get_translated_summary(data.get("long_summary", ""))
                        st.markdown(f'<div class="ai-report">{summary}</div>', unsafe_allow_html=True)
                
                    # --- 成長ドライバ・カード (DB対応) ---
                    if ticker in drivers_db:
                        st.write("<br>", unsafe_allow_html=True)
                        st.markdown(f"### 📈 {ticker} 主要成長ドライバ分析 (Summary)")
                        render_growth_driver_cards(drivers_db[ticker])
                    # ------------------------------------
                
                    st.divider()
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.markdown('<div class="section-title">📊 主要指標</div>', unsafe_allow_html=True)
                        st.markdown(f"**🏢 所属セクター:** {data.get('sector_display', '—')}")
                        st.markdown(f"**🏭 所属業界:** {data.get('industry_display', '—')}")
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.metric("時価総額", fmt_number(data.get("market_cap"), prefix="$"))
                        st.metric("PER", fmt_ratio(data.get("pe_ratio")))
                        st.metric("PBR", fmt_ratio(data.get("pb_ratio")))
                        div_y = data.get("dividend_yield")
                        st.metric("配当利回り", f"{div_y:.2f}%" if div_y else "N/A")
                    with col_m2:
                        st.markdown('<div class="section-title">💹 52週レンジ</div>', unsafe_allow_html=True)
                        render_52week_range(data.get("price"), data.get("fifty_two_week_low"), data.get("fifty_two_week_high"))
                        st.metric("現在週価", fmt_number(data.get("price"), prefix="$"), 
                                  delta=f"{((data['price']/data['prev_close'] - 1)*100):.2f}%" if data.get('price') and data.get('prev_close') else None)
    
            # 2. 財務・本質価値
            if tab_fund:
                with tab_fund:
                    st.divider()
                    # F-Score
                    st.markdown('<div class="section-title">🛡️ ピオトロスキー F-Score</div>', unsafe_allow_html=True)
                    f_res = calculate_f_score(ticker)
                    if f_res:
                        score = sum([v['pass'] for v in f_res.values()])
                        col_f1, col_f2 = st.columns([1, 2])
                        with col_f1:
                            if score >= 8: st.success(f"💎 スコア: {score}/9")
                            elif score <= 3: st.error(f"⚠️ スコア: {score}/9")
                            else: st.warning(f"⚖️ スコア: {score}/9")
                            st.progress(score/9)
                        with col_f2:
                            st.caption("9つの財務指標（収益性・安全性・効率性）による健全性評価。")
                        with st.expander("詳細内訳", expanded=True):
                            for k, v in f_res.items():
                                is_pass = v['pass']
                                icon = "✅" if is_pass else "❌"
                                val = v['val']
                                reason = v.get('reason', '')
                            
                                if is_pass:
                                    bg_color = "rgba(52, 211, 153, 0.1)"
                                    border_color = "#34d399"
                                    label_color = "#6ee7b7"
                                    reason_color = "#a7f3d0"
                                else:
                                    bg_color = "rgba(248, 113, 113, 0.1)"
                                    border_color = "#f87171"
                                    label_color = "#fca5a5"
                                    reason_color = "#fecaca"
                            
                                st.markdown(f"""
                                <div style="background: {bg_color}; border-left: 3px solid {border_color}; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-weight: 600; color: {label_color};">{icon} {k}</span>
                                        <span style="font-size: 0.85rem; color: #94a3b8;">{val}</span>
                                    </div>
                                    <div style="font-size: 0.8rem; color: {reason_color}; margin-top: 4px;">💬 {reason}</div>
                                </div>
                                """, unsafe_allow_html=True)
                
                    st.divider()
                    # 業績チャート
                    fin_period = st.radio("📅 表示期間", ["年次", "四半期"], horizontal=True, key="fin_period")
                
                    if fin_period == "年次":
                        fin, fin_err = fetch_financials(ticker)
                    else:
                        fin, fin_err = fetch_quarterly_financials(ticker)
                
                    if fin:
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            st.plotly_chart(create_revenue_chart(fin["dates"], fin.get("revenue"), fin.get("net_income")), use_container_width=True)
                        with col_c2:
                            st.plotly_chart(create_cashflow_chart(fin.get("cf_dates", fin["dates"]), fin.get("operating_cf", [])), use_container_width=True)
                    else:
                        st.info("財務データが取得できませんでした。")
                        if fin_err:
                            with st.expander("詳細なエラー"):
                                st.write(fin_err)
    
                    st.divider()
                    # 利益ベースの理論株価 (Earnings Valuation with Discounting)
                    st.markdown('<div class="section-title">💰 理論株価 (バリュエーション分析)</div>', unsafe_allow_html=True)
                    st.caption("将来の利益を『目標年利』で現在価値に割り引いた、今日の適正株価の推定値です。")
                
                    base_eps = data.get("eps_trailing")
                    if base_eps and base_eps > 0:
                        col_v1, col_v2 = st.columns(2)
                        col_v3, col_v4 = st.columns(2)
                    
                        # 1. 想定成長率 (売上成長率を採用)
                        default_g = int(data.get("revenue_growth", 0.1) * 100) if data.get("revenue_growth") is not None else 10
                        default_g = max(0, min(50, default_g))
                        g_rate = col_v1.slider("想定成長率 (%)", 0, 50, default_g, help="今後数年間の年平均成長率のシミュレーション値") / 100
                    
                        # 2. 投資ホライズン
                        horizon = col_v2.slider("投資ホライズン (年)", 1, 20, 10, help="何年分の利益を積み上げるか")
                    
                        # 3. 期待想定PER
                        default_pe = int(data.get("pe_ratio", 20)) if data.get("pe_ratio") is not None else 20
                        default_pe = max(5, min(100, default_pe))
                        target_pe = col_v3.slider("期待想定PER", 5, 100, default_pe, help="出口時点での適正な株価収益率")
                    
                        # --- ダイナミック目標年利の算出 ---
                        # 式: 5% (Base) + Beta * 5% + EPS_Growth * 20%
                        beta = data.get("beta", 1.0) if data.get("beta") is not None else 1.0
                        eps_g = data.get("eps_growth", data.get("revenue_growth", 0.1)) if data.get("eps_growth") is not None else 0.1
                        dynamic_r = 0.05 + (beta * 0.05) + (max(0, eps_g) * 0.2)
                        default_r = int(dynamic_r * 100)
                        default_r = max(5, min(30, default_r))
                    
                        # 4. 目標年利 (期待収益率・割引率)
                        r_rate = col_v4.slider("💡 目標年利 (期待収益率) %", 5, 30, default_r, help=f"リスク(Beta:{beta:.2f})と成長性から自動算出された推奨値です。") / 100
                        # -------------------------------
                    
                        val_res = calculate_earnings_valuation(base_eps, g_rate, horizon, target_pe, r_rate)
                    
                        if val_res:
                            total_val = val_res["total_value"]
                            curr_price = data['price']
                            gap = (total_val - curr_price) / curr_price
                        
                            # 判定ラベル
                            if gap > 0.3:
                                status, color = "🟢 大幅な割安 (Strong Buy)", "#10b981"
                            elif gap > 0:
                                status, color = "🟡 割安 (Fair)", "#f59e0b"
                            elif gap > -0.2:
                                status, color = "⚪ 適正 (Fair)", "#6b7280"
                            else:
                                status, color = "🔴 割高 (Overvalued)", "#ef4444"
    
                            st.write("---")
                            v_col1, v_col2 = st.columns([1, 1.5])
                        
                            with v_col1:
                                st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; border-left: 5px solid {color};">
                                    <h4 style="margin:0; font-size: 0.8rem; color: #9ca3af;">今日の適正価格（理論株価）</h4>
                                    <h2 style="margin: 5px 0; color: #ffffff;">${total_val:.2f}</h2>
                                    <p style="margin:0; font-size: 1.1rem; color: {color}; font-weight:700;">{status}</p>
                                    <p style="margin:0; font-size: 0.9rem; color: #9ca3af;">安全域: {gap:+.1%}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                            with v_col2:
                                st.write(f"**現在の株価位置** (適正価格に対して)")
                                progress = min(1.0, curr_price / total_val) if total_val > 0 else 0
                                st.progress(progress)
                                st.caption(f"現在値: ${curr_price:.2f} / 理論株価: ${total_val:.2f}")
                                st.caption(f"※ 目標年利 {r_rate:.1%} を達成するために、今買うべき「今の価値」を算出しています。")
    
                            st.write("<br>", unsafe_allow_html=True)
                            with st.expander("📊 10年後の将来価値シミュレーション（割引前）"):
                                c1, c2 = st.columns(2)
                                c1.write(f"📂 **{horizon}年間の累積利益 (将来値)**")
                                c1.subheader(f"${val_res['final_eps'] * horizon:.2f}") # 単純加算イメージ（実際は複利累積）
                                c2.write(f"📈 **{horizon}年後の予測株価**")
                                c2.subheader(f"${val_res['future_price']:.2f}")
                                st.caption(f"※ これらの将来価値合計を、年率 {r_rate:.1%} で割り戻したものが上記の「適正価格」です。")
                    else:
                        st.warning("⚠️ 利益(EPS)が取得できない、または赤字のためバリュエーションをスキップしました。")
    
            # 3. チャート
            if tab_chart:
                with tab_chart:
                    st.divider()
                    if style_mode == "短期モード":
                        st.markdown("### 📊 短期テクニカルチャート")
                        # 短期用の描画（直近6ヶ月をデフォルトとして使用）
                        short_hist = fetch_price_history(ticker, "6mo")
                        if short_hist is not None:
                            st.plotly_chart(create_short_term_chart(short_hist, ticker), use_container_width=True)
                    else:
                        period = st.selectbox("期間", ["1ヶ月", "6ヶ月", "1年", "5年"], index=2)
                        hist = fetch_price_history(ticker, PERIOD_MAP[period])
                        if hist is not None:
                            st.plotly_chart(create_technical_chart(hist, ticker), use_container_width=True)
    
            # 4. 競合比較
            if tab_peers:
                with tab_peers:
                    st.divider()
                
                    with st.spinner("競合他社のデータを抽出・取得中（約5〜10秒）…"):
                        peers = get_competitors(ticker)
                    
                    if not peers:
                        st.warning("この銘柄の競合他社が見つかりませんでした。ETFやデータ不足の銘柄である可能性があります。")
                    else:
                        st.markdown(f"**{ticker}** の関連・競合他社: " + ", ".join(peers))
                    
                        with st.spinner("各社の財務推移を比較中…"):
                            peers_df = fetch_peers_data(ticker, peers)
                    
                        if peers_df is not None and not peers_df.empty:
                            st.markdown("### 📊 ピア・グループ比較マトリックス")
                        
                            # ─── 総合順位の算出 ───
                            rank_cols = {}
                            rank_cols["売上成長率"] = peers_df["売上成長率(%)"].rank(ascending=False, na_option='bottom')
                            rank_cols["営業利益率"] = peers_df["営業利益率(%)"].rank(ascending=False, na_option='bottom')
                            rank_cols["PER"] = peers_df["PER"].replace(0, float('inf')).rank(ascending=True, na_option='bottom')
                            rank_cols["配当利回り"] = peers_df["配当利回り(%)"].rank(ascending=False, na_option='bottom')
                        
                            # 総合スコア = 各順位の合計（低いほど良い）
                            total_rank_score = rank_cols["売上成長率"] + rank_cols["営業利益率"] + rank_cols["PER"] + rank_cols["配当利回り"]
                            peers_df["総合順位"] = total_rank_score.rank(ascending=True).astype(int)
                        
                            # 総合順位でソート
                            peers_df = peers_df.sort_values("総合順位").reset_index(drop=True)
                        
                            avg_rev = peers_df["売上成長率(%)"].mean()
                            avg_margin = peers_df["営業利益率(%)"].mean()
                            avg_pe = peers_df["PER"].mean()
                            avg_div = peers_df["配当利回り(%)"].mean()
    
                            def highlight_matrix(row):
                                styles = [''] * len(row)
                                try:
                                    green_bg = 'background-color: rgba(52, 211, 153, 0.2); color: #a7f3d0;'
                                    gold_bg = 'background-color: rgba(250, 204, 21, 0.2); color: #fde68a; font-weight: bold;'
                                
                                    if pd.notna(row["売上成長率(%)"]) and row["売上成長率(%)"] > avg_rev:
                                        styles[peers_df.columns.get_loc("売上成長率(%)")] = green_bg
                                
                                    if pd.notna(row["営業利益率(%)"]) and row["営業利益率(%)"] > avg_margin:
                                        styles[peers_df.columns.get_loc("営業利益率(%)")] = green_bg
                                    
                                    if pd.notna(row["PER"]) and row["PER"] < avg_pe and row["PER"] > 0:
                                        styles[peers_df.columns.get_loc("PER")] = green_bg
                                    
                                    if pd.notna(row["配当利回り(%)"]) and row["配当利回り(%)"] > avg_div:
                                        styles[peers_df.columns.get_loc("配当利回り(%)")] = green_bg
                                
                                    # 総合1位はゴールド
                                    if row["総合順位"] == 1:
                                        styles[peers_df.columns.get_loc("総合順位")] = gold_bg
                                    
                                    if row["ティッカー"] == ticker:
                                        for i in range(len(styles)):
                                            if styles[i] == '':
                                                styles[i] = 'background-color: rgba(255, 255, 255, 0.05); font-weight: bold; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;'
                                            else:
                                                styles[i] += ' font-weight: bold; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;'
                                except Exception:
                                    pass
                                return styles
    
                            styled_df = peers_df.style.apply(highlight_matrix, axis=1)
                            styled_df = styled_df.format({
                                "時価総額(M)": "${:,.0f}",
                                "売上成長率(%)": "{:.1f}%",
                                "営業利益率(%)": "{:.1f}%",
                                "PER": "{:.1f}x",
                                "配当利回り(%)": "{:.2f}%",
                                "総合順位": "{}位"
                            }, na_rep="—")
                        
                            st.dataframe(styled_df, use_container_width=True, hide_index=True)
                        
                            # ─── 各指標の1位表示 ───
                            st.markdown("<br>##### 🏆 各指標の1位", unsafe_allow_html=True)
                            total_comps = len(peers_df)
                        
                            col_top1, col_top2, col_top3, col_top4 = st.columns(4)
                        
                            # 売上成長率1位
                            valid_rev = peers_df["売上成長率(%)"].dropna()
                            if not valid_rev.empty:
                                top_rev_idx = valid_rev.idxmax()
                                top_rev = peers_df.loc[top_rev_idx]
                                col_top1.metric("🥇 売上成長率", top_rev["ティッカー"], f"{top_rev['売上成長率(%)']:.1f}%")
                        
                            # 営業利益率1位
                            valid_margin = peers_df["営業利益率(%)"].dropna()
                            if not valid_margin.empty:
                                top_margin_idx = valid_margin.idxmax()
                                top_margin = peers_df.loc[top_margin_idx]
                                col_top2.metric("🥇 営業利益率", top_margin["ティッカー"], f"{top_margin['営業利益率(%)']:.1f}%")
                        
                            # PER最安（0以下を除外）
                            valid_pe = peers_df[peers_df["PER"] > 0]["PER"].dropna()
                            if not valid_pe.empty:
                                top_pe_idx = valid_pe.idxmin()
                                top_pe = peers_df.loc[top_pe_idx]
                                col_top3.metric("🥇 PER（最安）", top_pe["ティッカー"], f"{top_pe['PER']:.1f}x")
                        
                            # 配当利回り1位
                            valid_div = peers_df["配当利回り(%)"].dropna()
                            if not valid_div.empty:
                                top_div_idx = valid_div.idxmax()
                                top_div = peers_df.loc[top_div_idx]
                                col_top4.metric("🥇 配当利回り", top_div["ティッカー"], f"{top_div['配当利回り(%)']:.2f}%")
                        
                            # ─── 対象銘柄のランキング ───
                            st.markdown(f"<br>##### 📍 {ticker} のピアグループ内順位", unsafe_allow_html=True)
                            idx = peers_df.index[peers_df['ティッカー'] == ticker].tolist()
                            if idx:
                                i = idx[0]
                                tgt_row = peers_df.iloc[i]
                            
                                r_rev = int(rank_cols["売上成長率"].iloc[peers_df.index == i].values[0]) if i < len(rank_cols["売上成長率"]) else "—"
                                r_margin = int(rank_cols["営業利益率"].iloc[peers_df.index == i].values[0]) if i < len(rank_cols["営業利益率"]) else "—"
                                r_pe = int(rank_cols["PER"].iloc[peers_df.index == i].values[0]) if i < len(rank_cols["PER"]) else "—"
                                overall = int(tgt_row["総合順位"])
                            
                                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                                col_p1.metric("売上成長率", f"{r_rev}位", f"全{total_comps}社中", delta_color="off")
                                col_p2.metric("営業利益率", f"{r_margin}位", f"全{total_comps}社中", delta_color="off")
                                col_p3.metric("PER（低いほど上位）", f"{r_pe}位", f"全{total_comps}社中", delta_color="off")
                                col_p4.metric("🏅 総合順位", f"{overall}位", f"全{total_comps}社中", delta_color="off")
                        else:
                            st.info("データが不足しているため一覧を作成できませんでした。")
    
            # 5. CAN SLIM
            if tab_canslim:
                with tab_canslim:
                    st.divider()
                
                    with st.spinner("CAN SLIM 成長スコアを算出中…"):
                        cs_results = evaluate_canslim(ticker)
                
                    if not cs_results:
                        st.info("この銘柄の成長株スコアを算出できませんでした。")
                    else:
                        # 総合的な適合スコア
                        passes = [v['pass'] for v in cs_results.values()]
                        score_pct = (sum(passes) / len(passes)) * 100
                    
                        col_s1, col_s2 = st.columns([1, 2])
                        with col_s1:
                            st.markdown(f"### 総合適合度: {score_pct:.0f}%")
                        with col_s2:
                            st.progress(score_pct / 100)
                    
                        st.markdown("<br>", unsafe_allow_html=True)
                    
                        # チェックリスト (横並び)
                        cols = st.columns(len(cs_results))
                        for i, (key, res) in enumerate(cs_results.items()):
                            with cols[i]:
                                status = "✅ Pass" if res['pass'] else "❌ Fail"
                                color = "#34d399" if res['pass'] else "#f87171"
                                st.markdown(f"""
                                    <div style='text-align:center;'>
                                        <div style='font-size: 1.6rem; font-weight:bold; color:{color};'>{key}</div>
                                        <div style='font-size: 1.1rem; margin: 8px 0;'>{status}</div>
                                        <div style='font-size: 0.8rem; color:#94a3b8;'>{res['val']}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.caption(f"<div style='text-align:center;'>{res['help']}</div>", unsafe_allow_html=True)
    
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.info("💡 **CAN SLIM法とは**: ウィリアム・オニールが提唱した、大化け株を捉えるための7つの指標です（ここではM:市場の方向性、I:機関投資家の保有を除く5項目をスコアリングしています）。")
    
            # 6. SEPA
            if tab_sepa:
                with tab_sepa:
                    st.divider()
                    st.markdown('<div class="section-title">🏆 マーク・ミネルヴィニ SEPA分析 (Trend Template)</div>', unsafe_allow_html=True)
                    sepa = evaluate_sepa(ticker)
                    if sepa:
                        # 適合項目カウント
                        matches = sum([1 for v in sepa.values() if v['pass']])
                        total = len(sepa)
                        if matches == total:
                            st.success(f"💎 全項目適合 ({matches}/{total}): 強気トレンドの第2ステージに合致しています。")
                        elif matches >= 5:
                            st.warning(f"⚖️ 適合項目: {matches}/{total}")
                        else:
                            st.error(f"⚠️ 適合項目: {matches}/{total}")
                    
                        st.markdown("<br>", unsafe_allow_html=True)
                        for k, v in sepa.items():
                            st.markdown(f"**{k}**: {'✅' if v['pass'] else '❌'}  \n*{v['desc']}*")
    
            # 6. Weinstein Stage Analysis
            if tab_weinstein:
                with tab_weinstein:
                    st.divider()
                    st.markdown('<div class="section-title">📊 スタン・ワインスタイン・ステージ分析</div>', unsafe_allow_html=True)
                
                    with st.spinner("週足データを解析中..."):
                        w_stage = evaluate_weinstein_stage(ticker)
                
                    if w_stage["stage"] != "Unknown":
                        # ステージ表示カード
                        col_wa, col_wb = st.columns([1, 2])
                    
                        with col_wa:
                            # ステージの色設定
                            stage_colors = {
                                "Stage 1": "#64748b", # Gray
                                "Stage 2": "#10b981", # Green
                                "Stage 3": "#f59e0b", # Orange
                                "Stage 4": "#ef4444"  # Red
                            }
                            s_color = stage_colors.get(w_stage["stage"], "#ffffff")
                        
                            st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.05); border-left: 5px solid {s_color}; border-radius: 12px; padding: 20px; text-align: center;">
                                    <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 5px;">現在のステージ</div>
                                    <div style="font-size: 2rem; font-weight: 800; color: {s_color};">{w_stage['stage']}</div>
                                    <div style="font-size: 1.1rem; font-weight: 600; color: #e2e8f0;">{w_stage['sub_stage_label_ja']}</div>
                                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 5px;">({w_stage['stage_label_ja']})</div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                            # エントリー適性
                            quality_labels = {
                                "ideal": "💎 最良 (Ideal)",
                                "good": "✅ 良好 (Good)",
                                "watch": "🔭 監視 (Watch)",
                                "avoid": "⚠️ 回避 (Avoid)"
                            }
                            q_color = "#10b981" if w_stage['entry_quality'] in ["ideal", "good"] else ("#f59e0b" if w_stage['entry_quality'] == "watch" else "#ef4444")
                            st.markdown(f"""
                                <div style="margin-top: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; padding: 12px; text-align: center; border: 1px solid {q_color};">
                                    <span style="font-weight: 700; color: {q_color};">{quality_labels.get(w_stage['entry_quality'], '不明')}</span>
                                </div>
                            """, unsafe_allow_html=True)

                        with col_wb:
                            st.markdown(f"### {w_stage['entry_comment']}")
                            st.write(w_stage['description'])
                        
                            st.markdown("#### 判定理由")
                            for r in w_stage['reason']:
                                st.markdown(f"- {r}")
                            
                            # メトリクス
                            st.divider()
                            m1, m2, m3 = st.columns(3)
                            m1.metric("30週線乖離", f"{w_stage['price_vs_ma_pct']:+.1f}%")
                            m2.metric("30週線傾き", f"{w_stage['ma_slope_pct']:+.1f}%")
                            m3.metric("継続週数", f"{w_stage['weeks_in_current_trend']}週")

                        # チャート表示
                        st.divider()
                        st.markdown("#### 📈 週足チャート & 30週移動平均線")
                        # 週足データの再取得（チャート描画用）
                        hist_3y = yf.Ticker(ticker).history(period="3y")
                        if not hist_3y.empty:
                            logic_w = {'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}
                            df_chart_w = hist_3y.resample('W-FRI').apply(logic_w).dropna()
                            df_chart_w['MA30'] = df_chart_w['Close'].rolling(30).mean()
                        
                            fig_w = go.Figure()
                            # ローソク足
                            fig_w.add_trace(go.Candlestick(
                                x=df_chart_w.index, open=df_chart_w['Open'], high=df_chart_w['High'], low=df_chart_w['Low'], close=df_chart_w['Close'],
                                name="週足株価"
                            ))
                            # MA30
                            fig_w.add_trace(go.Scatter(
                                x=df_chart_w.index, y=df_chart_w['MA30'], line=dict(color='#00d2ff', width=2), name="30週移動平均線"
                            ))
                        
                            fig_w.update_layout(
                                **PLOTLY_LAYOUT,
                                height=500,
                                xaxis_rangeslider_visible=False,
                                title=f"{ticker} 週足分析 (WeinStein Stage Analysis)"
                            )
                            st.plotly_chart(fig_w, use_container_width=True)
                    else:
                        st.warning("この銘柄のステージ分析データを取得できませんでした。")
    
            # RS分析タブ
            if tab_rs:
                with tab_rs:
                    st.divider()
                    st.markdown('<div class="section-title">⚡ Relative Strength 分析（相対強度）</div>', unsafe_allow_html=True)
                    st.caption("S&P500・セクターETFに対して、この銘柄が相対的にどれほど強いかを定量評価します。")

                    # ── データ取得 ──────────────────────────────────────
                    sector_raw = data.get("sector", "")
                    with st.spinner("比較データを取得中（SPY / セクターETF / QQQ）…"):
                        rs_raw = fetch_relative_strength_data(ticker, sector_raw)

                    if rs_raw is None:
                        st.warning("⚠️ RS分析に必要なデータを取得できませんでした。")
                    else:
                        rs = calculate_relative_strength_metrics(rs_raw)
                        sector_etf_used = rs.get("sector_etf", "N/A")

                        # ── スコアゲージ & 総合判定 ────────────────────
                        rs_score   = rs.get("rs_score", 0)
                        rs_status  = rs.get("rs_status", "neutral")
                        rs_new_hi  = rs.get("rs_new_high", False)

                        status_cfg = {
                            "strong":  ("💪 強い (Strong)",   "#10b981", "rgba(16,185,129,0.12)"),
                            "neutral": ("⚖️ 中立 (Neutral)",  "#f59e0b", "rgba(245,158,11,0.12)"),
                            "weak":    ("📉 弱い (Weak)",     "#ef4444", "rgba(239,68,68,0.12)"),
                        }
                        s_label, s_color, s_bg = status_cfg.get(rs_status, status_cfg["neutral"])

                        col_score, col_verdict = st.columns([1, 2])
                        with col_score:
                            gauge_pct  = rs_score
                            gauge_rest = 100 - gauge_pct
                            fig_gauge = go.Figure(go.Pie(
                                values=[gauge_pct, gauge_rest],
                                hole=0.72,
                                marker_colors=[s_color, "rgba(255,255,255,0.05)"],
                                textinfo="none",
                                sort=False,
                            ))
                            fig_gauge.add_annotation(
                                text=f"<b>{rs_score}</b>",
                                x=0.5, y=0.55, font=dict(size=36, color=s_color),
                                showarrow=False
                            )
                            fig_gauge.add_annotation(
                                text="RS Score",
                                x=0.5, y=0.38, font=dict(size=12, color="#94a3b8"),
                                showarrow=False
                            )
                            fig_gauge.update_layout(
                                **{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=10, b=0)},
                                showlegend=False,
                                height=220,
                            )
                            st.plotly_chart(fig_gauge, use_container_width=True)

                        with col_verdict:
                            st.markdown(f'<div style="background:{s_bg}; border-left:5px solid {s_color}; border-radius:12px; padding:18px 20px; margin-bottom:12px;"><div style="font-size:1.5rem; font-weight:800; color:{s_color};">{s_label}</div><div style="font-size:0.85rem; color:#94a3b8; margin-top:4px;">使用セクターETF: <b style="color:#e2e8f0;">{sector_etf_used}</b>{"&nbsp;&nbsp;|&nbsp;&nbsp;<span style=\'color:#34d399;\'>📈 RSライン新高値更新中！</span>" if rs_new_hi else ""}</div></div>', unsafe_allow_html=True)

                            # スコア内訳コメント
                            ex_spy3m  = rs.get("excess_vs_spy_3m")
                            ex_spy6m  = rs.get("excess_vs_spy_6m")
                            ex_sec3m  = rs.get("excess_vs_sector_3m")
                            bullets = []
                            if ex_spy3m  is not None: bullets.append(f"対SPY 3M超過: **{ex_spy3m:+.1f}pp**")
                            if ex_spy6m  is not None: bullets.append(f"対SPY 6M超過: **{ex_spy6m:+.1f}pp**")
                            if ex_sec3m  is not None: bullets.append(f"対{sector_etf_used} 3M超過: **{ex_sec3m:+.1f}pp**")
                            if rs_new_hi: bullets.append("RSラインが直近高値を更新")
                            for b in bullets:
                                st.markdown(f"- {b}")

                        # ── 期間別パフォーマンス比較テーブル ────────────
                        st.divider()
                        st.markdown("#### 📊 期間別パフォーマンス比較")

                        def fmt_pct(v):
                            if v is None: return "—"
                            arrow = "▲" if v >= 0 else "▼"
                            color = "#34d399" if v >= 0 else "#f87171"
                            return f"<span style='color:{color};'>{arrow} {v:+.1f}%</span>"

                        periods_ui = [("1ヶ月", "1m"), ("3ヶ月", "3m"), ("6ヶ月", "6m"), ("12ヶ月", "12m")]
                        rows = []
                        for label, key in periods_ui:
                            stk_r  = rs.get(f"stock_return_{key}")
                            spy_r  = rs.get(f"spy_return_{key}")
                            sec_r  = rs.get(f"sector_return_{key}")
                            ex_spy = rs.get(f"excess_vs_spy_{key}")
                            ex_sec = rs.get(f"excess_vs_sector_{key}")
                            rows.append({
                                "期間": label,
                                f"{ticker}": fmt_pct(stk_r),
                                "SPY": fmt_pct(spy_r),
                                sector_etf_used: fmt_pct(sec_r),
                                "vs SPY": fmt_pct(ex_spy),
                                f"vs {sector_etf_used}": fmt_pct(ex_sec) if ex_sec is not None else "—",
                            })

                        tbl_html = "<table style='width:100%;border-collapse:collapse;font-size:0.9rem;'>"
                        # ヘッダー
                        tbl_html += "<tr>" + "".join(
                            f"<th style='padding:8px 12px;text-align:center;color:#94a3b8;border-bottom:1px solid rgba(255,255,255,0.1);'>{col}</th>"
                            for col in rows[0].keys()
                        ) + "</tr>"
                        # 行
                        for r in rows:
                            tbl_html += "<tr>" + "".join(
                                f"<td style='padding:8px 12px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.05);'>{v}</td>"
                                for v in r.values()
                            ) + "</tr>"
                        tbl_html += "</table>"
                        st.markdown(tbl_html, unsafe_allow_html=True)

                        # ── RSラインチャート ─────────────────────────────
                        st.divider()
                        st.markdown("#### 📈 RSライン（対SPY）　— 上昇 → 市場よりアウトパフォーム")

                        rs_line_series = rs.get("rs_line")
                        if rs_line_series is not None and not rs_line_series.empty:
                            # 価格も重ねて表示可能なようにサブプロット構成
                            fig_rs = make_subplots(
                                rows=2, cols=1,
                                shared_xaxes=True,
                                row_heights=[0.65, 0.35],
                                vertical_spacing=0.04,
                            )
                            # 上段: 正規化株価比較（ticker, SPY, セクター）
                            df_price = rs_raw["df"]
                            t0 = df_price.index[-252] if len(df_price) > 252 else df_price.index[0]
                            df_1y = df_price.loc[t0:].copy()
                            norm_base = df_1y.iloc[0]
                            df_norm = (df_1y / norm_base) * 100

                            line_cfg = {
                                ticker: ("#00d2ff", 2.5),
                                "SPY":  ("#94a3b8", 1.5),
                                sector_etf_used: ("#a78bfa", 1.5),
                            }
                            for col_name, (lcolor, lwidth) in line_cfg.items():
                                if col_name in df_norm.columns:
                                    fig_rs.add_trace(go.Scatter(
                                        x=df_norm.index, y=df_norm[col_name],
                                        name=col_name,
                                        line=dict(color=lcolor, width=lwidth),
                                    ), row=1, col=1)

                            # 下段: RSライン
                            rs_color = s_color
                            fig_rs.add_trace(go.Scatter(
                                x=rs_line_series.index,
                                y=rs_line_series.values,
                                name="RSライン",
                                fill="tozeroy",
                                fillcolor=s_bg,
                                line=dict(color=rs_color, width=2),
                            ), row=2, col=1)
                            # 基準線 100
                            fig_rs.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                                             row=2, col=1)

                            fig_rs.update_layout(
                                **{**PLOTLY_LAYOUT, "height": 550, "legend": dict(orientation="h", yanchor="bottom", y=1.01, x=0)},
                            )
                            fig_rs.update_yaxes(title_text="パフォーマンス (100基準)", row=1, col=1)
                            fig_rs.update_yaxes(title_text="RSライン", row=2, col=1)
                            st.plotly_chart(fig_rs, use_container_width=True)
                            st.caption("※ RSライン = 株価 / SPY の比率。100以上で推移 → SPYより強い。上昇トレンド中が理想。")
                        else:
                            st.info("RSラインチャートの生成に必要なデータが不足しています。")

            # ⏱ エントリー判定タブ
            if tab_entry:
                with tab_entry:
                    st.divider()
                    st.markdown('<div class="section-title">⏱ 週足 × 日足 エントリータイミング判定</div>', unsafe_allow_html=True)
                    st.caption("週足の大局トレンドと日足の執行タイミングを結合し、「今買ってよい状態か」を判断します。")

                    with st.spinner("週足・日足データを解析中..."):
                        entry_ws = evaluate_weinstein_stage(ticker)
                        entry_result = evaluate_entry_timing(ticker, entry_ws)

                    status     = entry_result.get("entry_status", "watch")
                    status_ja  = entry_result.get("entry_status_label_ja", "監視")
                    score_et   = entry_result.get("entry_timing_score", 0)
                    alignment  = entry_result.get("timeframe_alignment", "misaligned")
                    align_ja   = entry_result.get("timeframe_alignment_label_ja", "不整合")
                    comment_et = entry_result.get("entry_comment", "")
                    daily_d    = entry_result.get("daily_detail", {})

                    status_cfg = {
                        "buy_now":         ("🟢 今すぐ買い",    "#10b981", "rgba(16,185,129,0.15)"),
                        "buy_on_pullback": ("🟡 押し目なら買い", "#f59e0b", "rgba(245,158,11,0.15)"),
                        "watch":           ("🔵 監視",           "#3b82f6", "rgba(59,130,246,0.15)"),
                        "avoid":           ("🔴 見送り",         "#ef4444", "rgba(239,68,68,0.15)"),
                    }
                    st_label, st_color, st_bg = status_cfg.get(status, status_cfg["watch"])

                    align_cfg = {
                        "aligned":           ("✅ 整合",    "#10b981"),
                        "partially_aligned": ("⚠️ 部分整合", "#f59e0b"),
                        "misaligned":        ("❌ 不整合",   "#ef4444"),
                    }
                    al_icon, al_color = align_cfg.get(alignment, ("⚠️", "#f59e0b"))

                    # ── 上段: サマリーカード ─────────────────────────────
                    col_e1, col_e2, col_e3 = st.columns([1.2, 1, 1])

                    with col_e1:
                        score_color_e = "#10b981" if score_et >= 65 else ("#f59e0b" if score_et >= 40 else "#ef4444")
                        st.markdown(
                            f'<div style="background:{st_bg}; border-left:6px solid {st_color}; border-radius:12px; padding:18px 20px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">エントリー判定</div>'
                            f'<div style="font-size:1.6rem; font-weight:900; color:{st_color}; margin-top:4px;">{st_label}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    with col_e2:
                        score_color_e = "#10b981" if score_et >= 65 else ("#f59e0b" if score_et >= 40 else "#ef4444")
                        st.markdown(
                            f'<div style="text-align:center; padding:12px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">タイミングスコア</div>'
                            f'<div style="font-size:2.4rem; font-weight:900; color:{score_color_e};">{score_et}</div>'
                            f'<div style="font-size:0.8rem; color:#64748b;">/ 100</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    with col_e3:
                        st.markdown(
                            f'<div style="text-align:center; padding:12px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">時間軸整合性</div>'
                            f'<div style="font-size:1.05rem; font-weight:700; color:{al_color}; margin-top:8px;">{al_icon} {align_ja}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    st.markdown(f'<div class="ai-report" style="margin-top:12px;">{comment_et}</div>', unsafe_allow_html=True)

                    # ── 週足 vs 日足 詳細カード ──────────────────────────
                    st.divider()
                    col_w, col_d = st.columns(2)

                    with col_w:
                        st.markdown("##### 📅 週足判定（大局）")
                        w_stg = entry_ws.get("stage", "—")
                        w_sub = entry_ws.get("sub_stage", "—")
                        w_lbl = entry_ws.get("stage_label_ja", "—")
                        w_ql  = entry_ws.get("entry_quality", "—")
                        wq_colors = {"ideal": "#10b981", "good": "#34d399", "watch": "#f59e0b", "avoid": "#ef4444"}
                        wq_col = wq_colors.get(w_ql, "#94a3b8")
                        st.markdown(f"**ステージ**: `{w_stg}` / `{w_sub}`")
                        st.markdown(f"**ラベル**: {w_lbl}")
                        st.markdown(f'**エントリー適性**: <span style="color:{wq_col}; font-weight:700;">{w_ql}</span>', unsafe_allow_html=True)
                        w_comment = entry_ws.get("entry_comment", "")
                        if w_comment:
                            st.caption(w_comment)

                    with col_d:
                        st.markdown("##### 📆 日足判定（執行）")
                        d_lbl   = daily_d.get("daily_setup_label_ja", "—")
                        d_score = daily_d.get("daily_score", 0)
                        d_brk   = daily_d.get("breakout_confirmed", False)
                        d_pull  = daily_d.get("pullback_ready", False)
                        d_over  = daily_d.get("overextended", False)
                        d_risk  = daily_d.get("risk_flag", False)

                        d_icons = []
                        if d_brk:  d_icons.append("✅ ブレイクアウト確認")
                        if d_pull: d_icons.append("✅ 押し目反発")
                        if d_over: d_icons.append("⚠️ 伸びきり注意")
                        if d_risk: d_icons.append("🚨 崩れリスク")

                        score_color_d = "#10b981" if d_score >= 65 else ("#f59e0b" if d_score >= 40 else "#ef4444")
                        st.markdown(
                            f'**パターン**: {d_lbl} &nbsp; <span style="color:{score_color_d}; font-weight:700;">{d_score}pt</span>',
                            unsafe_allow_html=True
                        )
                        for ic in d_icons:
                            st.markdown(f"- {ic}")
                        st.markdown("**判定根拠:**")
                        for r in daily_d.get("reason", [])[:5]:
                            st.markdown(f"  - {r}")

                    # ── 日足チャート (MA20 / MA50) ─────────────────────
                    st.divider()
                    st.markdown("#### 📆 日足チャート (20日線 / 50日線)")
                    entry_daily_df = fetch_entry_timing_price_data(ticker)
                    if not entry_daily_df.empty and len(entry_daily_df) >= 55:
                        df_ind = calculate_entry_timing_indicators(entry_daily_df)
                        fig_ed = go.Figure()
                        fig_ed.add_trace(go.Candlestick(
                            x=df_ind.index, open=df_ind["Open"], high=df_ind["High"],
                            low=df_ind["Low"], close=df_ind["Close"], name="日足"
                        ))
                        fig_ed.add_trace(go.Scatter(
                            x=df_ind.index, y=df_ind["MA20"],
                            line=dict(color="#f59e0b", width=1.5), name="20日線"
                        ))
                        fig_ed.add_trace(go.Scatter(
                            x=df_ind.index, y=df_ind["MA50"],
                            line=dict(color="#a78bfa", width=1.5), name="50日線"
                        ))
                        fig_ed.update_layout(
                            **{**PLOTLY_LAYOUT, "height": 480, "xaxis_rangeslider_visible": False,
                               "title": f"{ticker} 日足 (MA20 / MA50)"},
                        )
                        st.plotly_chart(fig_ed, use_container_width=True)
                    else:
                        st.info("日足チャートの生成に必要なデータが不足しています。")

            # 🧾 決算品質タブ
            if tab_earnings:
                with tab_earnings:
                    st.divider()
                    st.markdown('<div class="section-title">🧾 決算品質分析 (Earnings Quality)</div>', unsafe_allow_html=True)
                    st.caption("四半期決算の数字の強さ・成長の質・市場反応を多角的に評価します。")

                    with st.spinner("四半期財務データを解析中..."):
                        eq_raw = fetch_earnings_quality_data(ticker)
                        eq = calculate_earnings_quality(eq_raw)

                    eq_score  = eq.get("earnings_quality_score", 0)
                    eq_status = eq.get("earnings_quality_status", "neutral")
                    eq_label  = eq.get("summary_label_ja", "—")
                    eq_comment= eq.get("comment", "")

                    status_cfg_eq = {
                        "strong":  ("💎 高品質",  "#10b981", "rgba(16,185,129,0.15)"),
                        "neutral": ("⚖️ 平均的",  "#f59e0b", "rgba(245,158,11,0.15)"),
                        "weak":    ("⚠️ 要注意",  "#ef4444", "rgba(239,68,68,0.15)"),
                    }
                    eq_icon, eq_color, eq_bg = status_cfg_eq.get(eq_status, status_cfg_eq["neutral"])

                    # ── スコアゲージ & ステータス ──────────────────────────
                    col_eq1, col_eq2 = st.columns([1, 2])

                    with col_eq1:
                        fig_eq_gauge = go.Figure(go.Pie(
                            values=[eq_score, 100 - eq_score],
                            hole=0.72,
                            marker_colors=[eq_color, "rgba(255,255,255,0.05)"],
                            textinfo="none", sort=False,
                        ))
                        fig_eq_gauge.add_annotation(
                            text=f"<b>{eq_score}</b>",
                            x=0.5, y=0.55, font=dict(size=36, color=eq_color), showarrow=False
                        )
                        fig_eq_gauge.add_annotation(
                            text="EQ Score", x=0.5, y=0.38,
                            font=dict(size=12, color="#94a3b8"), showarrow=False
                        )
                        fig_eq_gauge.update_layout(
                            **{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=10, b=0)},
                            showlegend=False, height=220,
                        )
                        st.plotly_chart(fig_eq_gauge, use_container_width=True)

                    with col_eq2:
                        st.markdown(
                            f'<div style="background:{eq_bg}; border-left:6px solid {eq_color}; '
                            f'border-radius:12px; padding:18px 20px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">総合評価</div>'
                            f'<div style="font-size:1.5rem; font-weight:900; color:{eq_color};">'
                            f'{eq_icon} {eq_label}</div></div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(f'<div class="ai-report" style="margin-top:10px;">{eq_comment}</div>',
                                    unsafe_allow_html=True)

                    # ── 主要指標メトリクス ─────────────────────────────────
                    st.divider()
                    st.markdown("#### 📊 主要財務指標（YoY 成長率）")
                    mc1, mc2, mc3, mc4 = st.columns(4)

                    def _fmt_growth(v, label):
                        if v is None: return st.metric(label, "—")
                        color = "normal" if v >= 0 else "inverse"
                        st.metric(label, f"{v:+.1f}%", delta=f"vs 前年同期", delta_color=color)

                    with mc1: _fmt_growth(eq.get("revenue_growth_pct"),      "売上成長率")
                    with mc2: _fmt_growth(eq.get("net_income_growth_pct"),   "純利益成長率")
                    with mc3: _fmt_growth(eq.get("operating_cf_growth_pct"), "営業CF成長率")
                    with mc4:
                        margin = eq.get("margin_latest_pct")
                        m_trend = eq.get("margin_trend", "unknown")
                        m_icon = "↑" if m_trend == "improving" else ("↓" if m_trend == "deteriorating" else "→")
                        st.metric("純利益率", f"{margin:.1f}%" if margin is not None else "—",
                                  delta=f"{m_icon} {eq.get('margin_trend_label_ja', '')}")

                    # ── 決算後市場反応 ─────────────────────────────────────
                    st.divider()
                    st.markdown("#### 📅 決算後の市場反応")
                    mr1, mr2, mr3 = st.columns(3)

                    ret_1d = eq.get("post_earnings_1d_return_pct")
                    ret_5d = eq.get("post_earnings_5d_return_pct")
                    vol_ra = eq.get("post_earnings_volume_ratio")

                    with mr1:
                        if ret_1d is not None:
                            st.metric("翌日騰落率", f"{ret_1d:+.1f}%",
                                      delta_color="normal" if ret_1d >= 0 else "inverse")
                        else: st.metric("翌日騰落率", "—")

                    with mr2:
                        if ret_5d is not None:
                            st.metric("5日後騰落率", f"{ret_5d:+.1f}%",
                                      delta_color="normal" if ret_5d >= 0 else "inverse")
                        else: st.metric("5日後騰落率", "—")

                    with mr3:
                        st.metric("翌日出来高倍率", f"{vol_ra:.1f}x" if vol_ra is not None else "—",
                                  help="直近20日の平均出来高との比率")

                    # ── 強み / 懸念フラグ ─────────────────────────────────
                    st.divider()
                    col_qf, col_rf = st.columns(2)

                    with col_qf:
                        st.markdown("#### ✅ 強みポイント")
                        qf = eq.get("quality_flags", [])
                        if qf:
                            for f in qf:
                                st.markdown(f"- {f}")
                        else:
                            st.caption("強みフラグなし")

                    with col_rf:
                        st.markdown("#### ⚠️ 懸念ポイント")
                        rf = eq.get("risk_flags", [])
                        if rf:
                            for f in rf:
                                st.markdown(f"- {f}")
                        else:
                            st.caption("懸念フラグなし")

                    # ── 四半期推移チャート ────────────────────────────────
                    st.divider()
                    st.markdown("#### 📈 四半期売上 / 純利益 / 営業CF 推移")

                    _rev  = eq.get("_rev")
                    _ni   = eq.get("_ni")
                    _ocf  = eq.get("_ocf")
                    _q_dates = eq.get("_q_dates", [])

                    if _rev is not None and len(_rev) >= 2:
                        x_labels = [str(d)[:7] for d in _q_dates[-len(_rev):]] if _q_dates else list(range(len(_rev)))
                        fig_eq_bar = go.Figure()
                        fig_eq_bar.add_trace(go.Bar(
                            x=x_labels, y=(_rev / 1e6).values,
                            name="売上高 (M$)", marker_color="#3b82f6", opacity=0.85
                        ))
                        if _ni is not None:
                            fig_eq_bar.add_trace(go.Bar(
                                x=x_labels[:len(_ni)], y=(_ni / 1e6).values,
                                name="純利益 (M$)", marker_color="#10b981", opacity=0.85
                            ))
                        if _ocf is not None:
                            fig_eq_bar.add_trace(go.Scatter(
                                x=x_labels[:len(_ocf)], y=(_ocf / 1e6).values,
                                name="営業CF (M$)", mode="lines+markers",
                                line=dict(color="#f59e0b", width=2),
                            ))
                        fig_eq_bar.update_layout(
                            **{**PLOTLY_LAYOUT, "height": 400, "barmode": "group",
                               "title": f"{ticker} 四半期業績推移"},
                        )
                        st.plotly_chart(fig_eq_bar, use_container_width=True)
                    else:
                        st.info("四半期チャートの生成に必要なデータが不足しています。")

            # ⚖️ 需給分析タブ
            if tab_sd:
                with tab_sd:
                    st.divider()
                    st.markdown('<div class="section-title">⚖️ 需給分析 (Supply / Demand)</div>', unsafe_allow_html=True)
                    st.caption("機関保有・空売り・インサイダー・出来高の4軸から資金の流れと需給バランスを評価します。")

                    with st.spinner("需給データを解析中..."):
                        sd_raw = fetch_supply_demand_extended(ticker)
                        sd = calculate_supply_demand_score(sd_raw)

                    sd_score  = sd.get("supply_demand_score", 0)
                    sd_status = sd.get("supply_demand_status", "neutral")
                    sd_label  = sd.get("summary_label_ja", "—")
                    sd_comment= sd.get("comment", "")

                    status_cfg_sd = {
                        "strong":  ("💪 良好",   "#10b981", "rgba(16,185,129,0.15)"),
                        "neutral": ("⚖️ 中立",   "#f59e0b", "rgba(245,158,11,0.15)"),
                        "weak":    ("📉 要注意", "#ef4444", "rgba(239,68,68,0.15)"),
                    }
                    sd_icon, sd_color, sd_bg = status_cfg_sd.get(sd_status, status_cfg_sd["neutral"])

                    # ── スコアゲージ & 総合ステータス ────────────────────
                    col_sd1, col_sd2 = st.columns([1, 2])

                    with col_sd1:
                        fig_sd_gauge = go.Figure(go.Pie(
                            values=[sd_score, 100 - sd_score],
                            hole=0.72,
                            marker_colors=[sd_color, "rgba(255,255,255,0.05)"],
                            textinfo="none", sort=False,
                        ))
                        fig_sd_gauge.add_annotation(
                            text=f"<b>{sd_score}</b>",
                            x=0.5, y=0.55, font=dict(size=36, color=sd_color), showarrow=False
                        )
                        fig_sd_gauge.add_annotation(
                            text="SD Score", x=0.5, y=0.38,
                            font=dict(size=12, color="#94a3b8"), showarrow=False
                        )
                        fig_sd_gauge.update_layout(
                            **{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=10, b=0)},
                            showlegend=False, height=220,
                        )
                        st.plotly_chart(fig_sd_gauge, use_container_width=True)

                    with col_sd2:
                        st.markdown(
                            f'<div style="background:{sd_bg}; border-left:6px solid {sd_color}; '
                            f'border-radius:12px; padding:18px 20px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">需給総合評価</div>'
                            f'<div style="font-size:1.5rem; font-weight:900; color:{sd_color};">'
                            f'{sd_icon} {sd_label}</div></div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(f'<div class="ai-report" style="margin-top:10px;">{sd_comment}</div>',
                                    unsafe_allow_html=True)

                    # ── 主要指標: 3列 ──────────────────────────────────
                    st.divider()
                    st.markdown("#### 📊 主要需給指標")
                    sdm1, sdm2, sdm3 = st.columns(3)

                    with sdm1:
                        inst_pct = sd.get("institutional_ownership_pct")
                        inst_sup = sd.get("institutional_support", "unknown")
                        sup_map  = {"strong": "💪高い", "moderate": "中程度", "low": "低め", "weak": "⚠️低い", "unknown": "—"}
                        st.metric("機関保有比率", f"{inst_pct:.1f}%" if inst_pct is not None else "—",
                                  delta=sup_map.get(inst_sup, "—"), help="機関投資家が保有している浮動株の割合")

                    with sdm2:
                        short_pct = sd.get("short_float_pct")
                        dtc       = sd.get("days_to_cover")
                        sq_label  = {"high": "🔥踏上余地大", "medium": "踏上余地あり",
                                     "low": "踏上余地小", "minimal": "ほぼなし", "unknown": "—"}
                        st.metric("空売り比率 (Float)", f"{short_pct:.1f}%" if short_pct is not None else "—",
                                  delta=sq_label.get(sd.get("short_squeeze_potential", "unknown"), "—"),
                                  help="浮動株に対する空売り割合")
                        if dtc is not None:
                            st.caption(f"Days to Cover: **{dtc:.1f}日**")

                    with sdm3:
                        insider_ja = sd.get("insider_bias_label_ja", "—")
                        insider_b  = sd.get("insider_bias", "neutral")
                        ins_color  = {"buying": "#10b981", "selling": "#ef4444",
                                      "mixed": "#f59e0b", "neutral": "#94a3b8"}.get(insider_b, "#94a3b8")
                        st.markdown(
                            f'<div style="text-align:center; padding:8px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">インサイダー動向（直近3ヶ月）</div>'
                            f'<div style="font-size:1.1rem; font-weight:700; color:{ins_color}; margin-top:6px;">'
                            f'{insider_ja}</div></div>',
                            unsafe_allow_html=True
                        )

                    # ── 出来高指標 ─────────────────────────────────────
                    st.divider()
                    st.markdown("#### 📦 出来高・資金流")
                    vm1, vm2, vm3 = st.columns(3)

                    with vm1:
                        vr20 = sd.get("volume_ratio_20d")
                        vr_col = "#10b981" if (vr20 is not None and vr20 >= 1.3) else ("#ef4444" if (vr20 is not None and vr20 < 0.7) else "#f59e0b")
                        st.metric("直近出来高倍率 (20日MA比)", f"{vr20:.1f}x" if vr20 is not None else "—",
                                  help="直近の出来高が20日平均の何倍か")

                    with vm2:
                        up_vol = sd.get("up_volume_strength", "unknown")
                        uv_label = {"strong": "💪 上昇日優勢", "moderate": "やや上昇優勢",
                                    "neutral": "拮抗", "weak": "⚠️ 下落日優勢", "unknown": "—"}
                        uv_color = {"strong": "#10b981", "moderate": "#34d399", "neutral": "#94a3b8",
                                    "weak": "#ef4444", "unknown": "#64748b"}.get(up_vol, "#94a3b8")
                        st.markdown(
                            f'<div style="text-align:center; padding:8px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">上昇日 vs 下落日 出来高</div>'
                            f'<div style="font-size:1.1rem; font-weight:700; color:{uv_color}; margin-top:6px;">'
                            f'{uv_label.get(up_vol, "—")}</div></div>',
                            unsafe_allow_html=True
                        )

                    with vm3:
                        avg_10d = sd_raw.get("avg_volume_10d")
                        avg_3m  = sd_raw.get("avg_volume_3m")
                        if avg_10d and avg_3m and avg_3m > 0:
                            short_term_vs_avg = avg_10d / avg_3m
                            trend_label = "増加傾向 📈" if short_term_vs_avg >= 1.1 else ("減少傾向 📉" if short_term_vs_avg <= 0.9 else "横ばい")
                            st.metric("出来高トレンド (10日/3ヶ月平均)", f"{short_term_vs_avg:.2f}x", delta=trend_label)
                        else:
                            st.metric("出来高トレンド", "—")

                    # ── 強み / 懸念フラグ ─────────────────────────────
                    st.divider()
                    col_sdqf, col_sdrf = st.columns(2)

                    with col_sdqf:
                        st.markdown("#### ✅ 需給好転ポイント")
                        qf = sd.get("quality_flags", [])
                        if qf:
                            for f in qf:
                                st.markdown(f"- {f}")
                        else:
                            st.caption("好転フラグなし")

                    with col_sdrf:
                        st.markdown("#### ⚠️ 需給懸念ポイント")
                        rf = sd.get("risk_flags", [])
                        if rf:
                            for f in rf:
                                st.markdown(f"- {f}")
                        else:
                            st.caption("懸念フラグなし")

                    # ── 出来高付き日足チャート ──────────────────────────
                    st.divider()
                    st.markdown("#### 📈 出来高付き日足チャート（直近1年）")
                    _sd_hist = sd.get("_hist", pd.DataFrame())
                    if not _sd_hist.empty and len(_sd_hist) >= 20:
                        vol_ma_line = _sd_hist["Volume"].rolling(20).mean()
                        fig_sd_vol = make_subplots(
                            rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.65, 0.35], vertical_spacing=0.04,
                        )
                        # 上段: ローソク足
                        fig_sd_vol.add_trace(go.Candlestick(
                            x=_sd_hist.index, open=_sd_hist["Open"], high=_sd_hist["High"],
                            low=_sd_hist["Low"], close=_sd_hist["Close"], name="株価"
                        ), row=1, col=1)
                        # 下段: 出来高バー
                        colors_vol = [
                            "#10b981" if c >= o else "#ef4444"
                            for c, o in zip(_sd_hist["Close"], _sd_hist["Open"])
                        ]
                        fig_sd_vol.add_trace(go.Bar(
                            x=_sd_hist.index, y=_sd_hist["Volume"],
                            name="出来高", marker_color=colors_vol, opacity=0.7
                        ), row=2, col=1)
                        # 20日平均出来高ライン
                        fig_sd_vol.add_trace(go.Scatter(
                            x=_sd_hist.index, y=vol_ma_line,
                            name="出来高20日MA", line=dict(color="#f59e0b", width=1.5, dash="dot")
                        ), row=2, col=1)
                        fig_sd_vol.update_layout(
                            **{**PLOTLY_LAYOUT, "height": 500, "xaxis_rangeslider_visible": False,
                               "title": f"{ticker} 株価・出来高（直近1年）"},
                        )
                        st.plotly_chart(fig_sd_vol, use_container_width=True)
                    else:
                        st.info("出来高チャートの生成に必要なデータが不足しています。")

                    # ── インサイダー売買テーブル ────────────────────────
                    _insider_df = sd.get("_insider_df", pd.DataFrame())
                    if _insider_df is not None and not _insider_df.empty:
                        st.divider()
                        st.markdown("#### 👤 インサイダー売買（直近）")
                        show_cols = [c for c in ["Date", "Insider", "Position", "Side", "Shares", "Value"] if c in _insider_df.columns]
                        disp_df = _insider_df[show_cols].head(10).copy()
                        if "Value" in disp_df.columns:
                            disp_df["Value"] = disp_df["Value"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
                        st.dataframe(disp_df, use_container_width=True)

            # 📏 バリュエーション帯分析タブ
            if tab_val:
                with tab_val:
                    st.divider()
                    st.markdown('<div class="section-title">📏 バリュエーション帯分析 (Valuation Band)</div>', unsafe_allow_html=True)
                    st.caption("自社の過去レンジ・同業比較・成長率調整の3軸でバリュエーションを評価します。")

                    with st.spinner("バリュエーションデータを取得・解析中（同業比較含む）..."):
                        vb_raw = fetch_valuation_band_data(ticker)
                        vb = calculate_valuation_band(vb_raw)

                    vb_score  = vb.get("valuation_score_v2", 50)
                    vb_status = vb.get("valuation_status", "fair")
                    vb_label  = vb.get("valuation_label_ja", "—")
                    vb_comment= vb.get("comment", "")

                    status_cfg_vb = {
                        "cheap":             ("💎 割安",     "#10b981", "rgba(16,185,129,0.15)"),
                        "fair":              ("⚖️ 適正",     "#3b82f6", "rgba(59,130,246,0.15)"),
                        "slightly_expensive":("🟡 やや割高", "#f59e0b", "rgba(245,158,11,0.15)"),
                        "expensive":         ("🔴 割高",     "#ef4444", "rgba(239,68,68,0.15)"),
                    }
                    vb_icon, vb_color, vb_bg = status_cfg_vb.get(vb_status, status_cfg_vb["fair"])

                    # ── スコアゲージ & 総合ステータス ────────────────────
                    col_vb1, col_vb2 = st.columns([1, 2])
                    with col_vb1:
                        fig_vb_gauge = go.Figure(go.Pie(
                            values=[vb_score, 100 - vb_score],
                            hole=0.72,
                            marker_colors=[vb_color, "rgba(255,255,255,0.05)"],
                            textinfo="none", sort=False,
                        ))
                        fig_vb_gauge.add_annotation(
                            text=f"<b>{vb_score}</b>",
                            x=0.5, y=0.55, font=dict(size=36, color=vb_color), showarrow=False
                        )
                        fig_vb_gauge.add_annotation(
                            text="Val Score", x=0.5, y=0.38,
                            font=dict(size=12, color="#94a3b8"), showarrow=False
                        )
                        fig_vb_gauge.update_layout(
                            **{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=10, b=0)},
                            showlegend=False, height=220,
                        )
                        st.plotly_chart(fig_vb_gauge, use_container_width=True)

                    with col_vb2:
                        st.markdown(
                            f'<div style="background:{vb_bg}; border-left:6px solid {vb_color}; '
                            f'border-radius:12px; padding:18px 20px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">バリュエーション総合判定</div>'
                            f'<div style="font-size:1.5rem; font-weight:900; color:{vb_color};">'
                            f'{vb_icon} {vb_label}</div></div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(f'<div class="ai-report" style="margin-top:10px;">{vb_comment}</div>',
                                    unsafe_allow_html=True)

                    # ── 現在の主要指標 ─────────────────────────────────
                    st.divider()
                    st.markdown("#### 📊 現在の主要バリュエーション指標")
                    vm1, vm2, vm3, vm4 = st.columns(4)
                    with vm1:
                        pe = vb.get("current_pe")
                        pe_fwd = vb.get("current_pe_fwd")
                        st.metric("PER (TTM)", f"{pe:.1f}x" if pe else "—",
                                  delta=f"予{pe_fwd:.1f}x" if pe_fwd else None)
                with vm2:
                    psr = vb.get("current_psr")
                    st.metric("PSR", f"{psr:.1f}x" if psr else "—", help="時価総額÷売上高")
                with vm3:
                    peg = vb.get("peg")
                    peg_color = "#10b981" if (peg and peg < 1.5) else ("#ef4444" if (peg and peg > 3) else "#f59e0b")
                    if peg:
                        st.markdown(
                            f'<div style="text-align:center;"><div style="font-size:0.8rem; color:#94a3b8;">PEG</div>'
                            f'<div style="font-size:1.4rem; font-weight:700; color:{peg_color};">{peg:.2f}x</div></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.metric("PEG", "—", help="PER÷EPS成長率%")
                with vm4:
                    fcfy = vb.get("fcf_yield")
                    fcfy_color = "#10b981" if (fcfy and fcfy >= 3) else ("#ef4444" if (fcfy and fcfy < 0) else "#f59e0b")
                    st.metric("FCF利回り", f"{fcfy:.1f}%" if fcfy is not None else "—",
                              help="フリーキャッシュフロー / 時価総額")

                # ── A: 自社の過去レンジ比較 ──────────────────────────
                st.divider()
                st.markdown("#### 🅐 自社の過去レンジ比較")
                hist_pe_vals  = vb.get("hist_pe_values", [])
                hist_psr_vals = vb.get("hist_psr_values", [])
                pe_band_pos   = vb.get("historical_pe_band_position")
                hist_pe_med   = vb.get("historical_pe_median")

                col_ha, col_hb = st.columns(2)
                with col_ha:
                    st.markdown("**PER 過去レンジ**")
                    if hist_pe_vals and pe:
                        fig_hist_pe = go.Figure()
                        fig_hist_pe.add_trace(go.Histogram(
                            x=hist_pe_vals, name="過去PER",
                            marker_color="#3b82f6", opacity=0.7, nbinsx=15
                        ))
                        fig_hist_pe.add_vline(
                            x=pe, line_color="#f59e0b", line_width=2,
                            annotation_text=f"現在 {pe:.1f}x", annotation_position="top right"
                        )
                        if hist_pe_med:
                            fig_hist_pe.add_vline(
                                x=hist_pe_med, line_color="#94a3b8", line_width=1, line_dash="dash",
                                annotation_text=f"中央値 {hist_pe_med:.1f}x", annotation_position="top left"
                            )
                        fig_hist_pe.update_layout(
                            **{**PLOTLY_LAYOUT, "height": 260, "showlegend": False,
                               "xaxis_title": "PER", "yaxis_title": "頻度"},
                        )
                        st.plotly_chart(fig_hist_pe, use_container_width=True)
                        if pe_band_pos is not None:
                            pct_label = f"{pe_band_pos*100:.0f}パーセンタイル"
                            band_color = "#10b981" if pe_band_pos <= 0.4 else ("#ef4444" if pe_band_pos >= 0.75 else "#f59e0b")
                            st.markdown(f'現在PERは過去レンジの <b style="color:{band_color};">{pct_label}</b>（中央値 {hist_pe_med:.1f}x）', unsafe_allow_html=True)
                    else:
                        st.caption("過去PERデータが取得できませんでした。")

                with col_hb:
                    st.markdown("**PSR 過去レンジ**")
                    hist_psr_med = vb.get("historical_psr_median")
                    psr_band_pos = vb.get("historical_psr_band_position")
                    if hist_psr_vals and psr:
                        fig_hist_psr = go.Figure()
                        fig_hist_psr.add_trace(go.Histogram(
                            x=hist_psr_vals, name="過去PSR",
                            marker_color="#a78bfa", opacity=0.7, nbinsx=15
                        ))
                        fig_hist_psr.add_vline(
                            x=psr, line_color="#f59e0b", line_width=2,
                            annotation_text=f"現在 {psr:.1f}x", annotation_position="top right"
                        )
                        if hist_psr_med:
                            fig_hist_psr.add_vline(
                                x=hist_psr_med, line_color="#94a3b8", line_width=1, line_dash="dash",
                                annotation_text=f"中央値 {hist_psr_med:.1f}x", annotation_position="top left"
                            )
                        fig_hist_psr.update_layout(
                            **{**PLOTLY_LAYOUT, "height": 260, "showlegend": False,
                               "xaxis_title": "PSR", "yaxis_title": "頻度"},
                        )
                        st.plotly_chart(fig_hist_psr, use_container_width=True)
                        if psr_band_pos is not None:
                            pct_lbl = f"{psr_band_pos*100:.0f}パーセンタイル"
                            pc = "#10b981" if psr_band_pos <= 0.4 else ("#ef4444" if psr_band_pos >= 0.75 else "#f59e0b")
                            st.markdown(f'現在PSRは過去レンジの <b style="color:{pc};">{pct_lbl}</b>（中央値 {hist_psr_med:.1f}x）', unsafe_allow_html=True)
                    else:
                        st.caption("過去PSRデータが取得できませんでした。")

                # ── B: 同業比較テーブル ──────────────────────────────
                st.divider()
                st.markdown("#### 🅑 同業他社バリュエーション比較")
                peers = vb.get("peer_data", [])
                if peers:
                    peer_rows = []
                    for p in peers:
                        peer_rows.append({
                            "銘柄":         p["ticker"],
                            "PER":          f"{p['pe']:.1f}x"  if p.get("pe")  else "—",
                            "P/B":          f"{p['pb']:.1f}x"  if p.get("pb")  else "—",
                            "PSR":          f"{p['psr']:.1f}x" if p.get("psr") else "—",
                            "売上成長率":   f"{p['rev_growth']:+.1f}%" if p.get("rev_growth") else "—",
                            "EPS成長率":    f"{p['eps_growth']:+.1f}%" if p.get("eps_growth") else "—",
                        })
                    # 自社を先頭に追加
                    self_row = {
                        "銘柄":       f"【{ticker}】",
                        "PER":        f"{pe:.1f}x"   if pe   else "—",
                        "P/B":        f"{vb.get('current_pb'):.1f}x" if vb.get("current_pb") else "—",
                        "PSR":        f"{psr:.1f}x"  if psr  else "—",
                        "売上成長率": f"{vb.get('rev_growth_pct'):+.1f}%" if vb.get("rev_growth_pct") else "—",
                        "EPS成長率":  f"{vb.get('eps_growth_pct'):+.1f}%" if vb.get("eps_growth_pct") else "—",
                    }
                    st.dataframe([self_row] + peer_rows, use_container_width=True)

                    peer_pe_med  = vb.get("peer_pe_median")
                    peer_pe_gap  = vb.get("peer_pe_gap")
                    peer_psr_gap = vb.get("peer_psr_gap")
                    if peer_pe_med:
                        gap_c = "#10b981" if (peer_pe_gap and peer_pe_gap <= -5) else ("#ef4444" if (peer_pe_gap and peer_pe_gap >= 15) else "#94a3b8")
                        st.markdown(
                            f'同業PER中央値: **{peer_pe_med:.1f}x** &nbsp; 自社との乖離: '
                            f'<b style="color:{gap_c};">{peer_pe_gap:+.0f}%</b>' if peer_pe_gap is not None else f'同業PER中央値: **{peer_pe_med:.1f}x**',
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("同業データが取得できませんでした。")

                # ── 強み / 懸念フラグ ─────────────────────────────
                st.divider()
                col_vbqf, col_vbrf = st.columns(2)
                with col_vbqf:
                    st.markdown("#### ✅ 割安・優位ポイント")
                    for f in vb.get("quality_flags", []) or ["特になし"]: st.markdown(f"- {f}")
                with col_vbrf:
                    st.markdown("#### ⚠️ 割高・懸念ポイント")
                    for f in vb.get("risk_flags", []) or ["特になし"]: st.markdown(f"- {f}")

            # 📅 イベントリスク判定タブ
            if tab_event:
                with tab_event:
                    st.divider()
                    st.markdown('<div class="section-title">📅 イベントリスク判定 (Event Risk)</div>', unsafe_allow_html=True)
                    st.caption("決算接近・マクロイベント・セクター特性の3軸から「今購入すべきタイミングか」を判定します。")

                    with st.spinner("イベントリスクデータを解析中..."):
                        er_raw  = fetch_event_risk_data(ticker)
                        er      = calculate_event_risk(er_raw)

                    er_score  = er.get("event_risk_score", 0)
                    er_status = er.get("event_risk_status", "low")
                    er_label  = er.get("summary_label_ja", "—")
                    er_comment= er.get("comment", "")
                    wait_flag = er.get("wait_for_event_passage", False)

                    status_cfg_er = {
                        "high":   ("🚨 高リスク",    "#ef4444", "rgba(239,68,68,0.15)"),
                        "medium": ("⚠️ 中リスク",  "#f59e0b", "rgba(245,158,11,0.15)"),
                        "low":    ("✅ 低リスク",    "#10b981", "rgba(16,185,129,0.15)"),
                    }
                    er_icon, er_color, er_bg = status_cfg_er.get(er_status, status_cfg_er["medium"])

                    # ── イベント通過待ちバナー ─────────────────────────────
                    if wait_flag:
                        st.markdown(
                            '<div style="background:rgba(239,68,68,0.12); border:1px solid #ef4444; '
                            'border-radius:10px; padding:14px 18px; margin-bottom:12px;">'
                            '🛑 <b>イベント通過を待つことを推奨</b> — '
                            '銀柄自体の魅力とは別に、短期的にはイベント通過待ちの方が合理的な局面です。'
                            '</div>',
                            unsafe_allow_html=True
                        )

                    # ── スコアゲージ & 総合ステータス ────────────────────
                    col_er1, col_er2 = st.columns([1, 2])
                    with col_er1:
                        fig_er_gauge = go.Figure(go.Pie(
                            values=[er_score, 100 - er_score],
                            hole=0.72,
                            marker_colors=[er_color, "rgba(255,255,255,0.05)"],
                            textinfo="none", sort=False,
                        ))
                        fig_er_gauge.add_annotation(
                            text=f"<b>{er_score}</b>",
                            x=0.5, y=0.55, font=dict(size=36, color=er_color), showarrow=False
                        )
                        fig_er_gauge.add_annotation(
                            text="Event Risk", x=0.5, y=0.38,
                            font=dict(size=11, color="#94a3b8"), showarrow=False
                        )
                        fig_er_gauge.update_layout(
                            **{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=10, b=0)},
                            showlegend=False, height=220,
                        )
                        st.plotly_chart(fig_er_gauge, use_container_width=True)

                    with col_er2:
                        st.markdown(
                            f'<div style="background:{er_bg}; border-left:6px solid {er_color}; '
                            f'border-radius:12px; padding:18px 20px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">イベントリスク総合判定</div>'
                            f'<div style="font-size:1.5rem; font-weight:900; color:{er_color};">'
                            f'{er_icon} {er_label}</div></div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(f'<div class="ai-report" style="margin-top:10px;">{er_comment}</div>',
                                    unsafe_allow_html=True)

                    # ── 3軸詳細カード ─────────────────────────────────────
                    st.divider()
                    st.markdown("#### 📌 リスク要因3軸")
                    ec1, ec2, ec3 = st.columns(3)

                    # 軸1: 決算リスク
                    with ec1:
                        d2e    = er.get("days_to_earnings")
                        el     = er.get("earnings_risk_level", "unknown")
                        el_col = {"imminent": "#ef4444", "high": "#ef4444", "medium": "#f59e0b",
                                  "low": "#f59e0b", "safe": "#10b981", "passed": "#10b981",
                                  "unknown": "#94a3b8"}.get(el, "#94a3b8")
                        st.markdown(
                            f'<div style="background:rgba(255,255,255,0.04); border-radius:10px; padding:14px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">📄 決算リスク</div>'
                            f'<div style="font-size:1.0rem; font-weight:700; color:{el_col}; margin-top:4px;">'
                            f'{er.get("earnings_risk_label_ja", "—")}</div>'
                            f'<div style="font-size:0.8rem; color:#64748b; margin-top:4px;">'
                            f'決算日: {er.get("earnings_date", "不明")} | 退け: '
                            f'{"{:.1f}%".format(er.get("avg_earnings_move_pct")) if er.get("avg_earnings_move_pct") else "—"}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

                    # 軸2: マクロリスク
                    with ec2:
                        ml     = er.get("macro_event_risk_level", "low")
                        ml_col = {"high": "#ef4444", "medium": "#f59e0b",
                                  "low_medium": "#f59e0b", "low": "#10b981"}.get(ml, "#94a3b8")
                        nm     = er.get("nearest_macro_name", "")
                        nd     = er.get("nearest_macro_days")
                        st.markdown(
                            f'<div style="background:rgba(255,255,255,0.04); border-radius:10px; padding:14px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">🌐 マクロイベント</div>'
                            f'<div style="font-size:1.0rem; font-weight:700; color:{ml_col}; margin-top:4px;">'
                            f'{er.get("macro_event_risk_label_ja", "—")}</div>'
                            f'<div style="font-size:0.8rem; color:#64748b; margin-top:4px;">'
                            f'{nm + " まで " + str(nd) + "日" if nm and nd is not None else "直近2週間に主要イベントなし"}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

                    # 軸3: セクター感応度
                    with ec3:
                        sl     = er.get("sector_event_sensitivity", "medium")
                        sl_col = {"very_high": "#ef4444", "high": "#f59e0b",
                                  "medium": "#3b82f6", "low": "#10b981"}.get(sl, "#94a3b8")
                        sl_lv  = {"very_high": "🚨 極高", "high": "🔵 高", "medium": "🟡 中", "low": "🟢 低"}.get(sl, "—")
                        st.markdown(
                            f'<div style="background:rgba(255,255,255,0.04); border-radius:10px; padding:14px;">'
                            f'<div style="font-size:0.8rem; color:#94a3b8;">🏭 セクター感応度</div>'
                            f'<div style="font-size:1.0rem; font-weight:700; color:{sl_col}; margin-top:4px;">{sl_lv}</div>'
                            f'<div style="font-size:0.75rem; color:#64748b; margin-top:4px;">'
                            f'{er.get("sector_event_sensitivity_label_ja", "—")}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

                    # ── マクロイベントカレンダービュー ────────────────────────────
                    st.divider()
                    import datetime as _dt_ui
                    today_ui = _dt_ui.date.today()
                    st.markdown("#### 🗓️ マクロイベントカレンダー（直近90日分）")
                    cal_rows = []
                    for ev in _MACRO_EVENT_CALENDAR:
                        try:
                            ev_date = _dt_ui.date.fromisoformat(ev["date"])
                            diff = (ev_date - today_ui).days
                            if -7 <= diff <= 90:
                                urgency = "🚨" if diff <= 3 else ("⚠️" if diff <= 7 else "📌")
                                cal_rows.append({
                                    "イベント": f"{urgency} {ev['name']}",
                                    "日付":   str(ev_date),
                                    "までの日数": f"{diff}日" if diff >= 0 else f"通過済({abs(diff)}日前)",
                                    "種別":   ev.get("type", "—").upper(),
                                })
                        except Exception:
                            pass
                    if cal_rows:
                        st.dataframe(cal_rows, use_container_width=True)
                    else:
                        st.caption("直近90日内に登録されたマクロイベントはありません。")

                    # ── 安心材料 / 警戛材料 ─────────────────────────────
                    st.divider()
                    col_erqf, col_errf = st.columns(2)
                    with col_erqf:
                        st.markdown("#### ✅ リスク抱減要因")
                        for f in er.get("quality_flags", []) or ["特になし"]: st.markdown(f"- {f}")
                    with col_errf:
                        st.markdown("#### ⚠️ 警戛要因")
                        for f in er.get("risk_flags", []) or ["特になし"]: st.markdown(f"- {f}")

            # 7. リスク・予想
            if tab_risk:
                with tab_risk:
                    st.divider()
                    col_r1, col_r2 = st.columns([1, 1])
                
                    with col_r1:
                        st.markdown('<div class="section-title">🛡️ リスク感応度 & ベータ</div>', unsafe_allow_html=True)
                        risk = calculate_risk_sensitivity(ticker, data.get("sector", ""))
                        if risk:
                            st.metric("1年ベータ", f"{risk.get('beta_1y', 0):.2f}", help="市場(SPY)に対する感応度。1.0より高いと変動が激しい。")
                            st.metric("金利相関係数", f"{risk.get('corr_yield', 0):+.2f}", help="10年債利回りとの相関。プラスなら金利上昇時に上昇しやすい。")
                            st.caption(f"※ 使用セクターETF: {risk.get('sector_etf_used', 'SPY')}")
                    
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown('<div class="section-title">🏢 SEC公式提出書類 (EDGAR)</div>', unsafe_allow_html=True)
                        analyst = fetch_analyst_data(ticker)
                        if analyst and analyst.get("filings"):
                            for f in analyst["filings"]:
                                st.markdown(f"📄 **{f['type']}** ({f['date']})<br>[{f['title']}]({f['url']})", unsafe_allow_html=True)
                        else:
                            st.info("直近の公式書類リンクが見つかりませんでした。")
    
                    with col_r2:
                        st.markdown('<div class="section-title">📝 アナリスト予想 & レーティング</div>', unsafe_allow_html=True)
                        if analyst:
                            # 目標株価メトリクス
                            curr_p = data.get("price")
                            def get_delta(target):
                                if target and curr_p:
                                    diff = (target - curr_p) / curr_p
                                    return f"{diff:+.1%}"
                                return None
    
                            c1, c2 = st.columns(2)
                            c1.metric("平均目標株価", fmt_number(analyst.get("target_mean"), prefix="$"), delta=get_delta(analyst.get("target_mean")))
                            c2.metric("コンセンサス", analyst.get("recommendation_key", "—").replace("_", " ").capitalize())
                        
                            # 円グラフ
                            fig_pie = create_recommendation_pie_chart(analyst.get("recs_summary"))
                            if fig_pie:
                                st.plotly_chart(fig_pie, use_container_width=True)
                    
                        st.divider()
                        st.markdown('<div class="section-title">🔑 インサイダー取引履歴</div>', unsafe_allow_html=True)
                        if analyst and analyst.get("insider") is not None and not analyst["insider"].empty:
                            st.dataframe(analyst["insider"].head(10), use_container_width=True, hide_index=True)
                        else:
                            st.info("直近のインサイダー取引データがありません。")
    

            # 8. シナリオ別期待値分析
            if tab_scenario:
                with tab_scenario:
                    st.divider()
                    st.markdown('<div class="section-title">🎲 シナリオ別期待値分析 (Expected Value / Risk-Reward)</div>', unsafe_allow_html=True)
                    st.caption("強気・中立・弱気のシナリオ別に目標価格を算出し、現在価格からの「期待値（Expected Value）」と「リスクリワード比」を評価します。")
                
                    with st.spinner("シナリオ期待値を計算中..."):
                        cio_base_inputs = build_cio_decision_inputs(ticker)
                        scenario_res = calculate_scenario_expected_value(ticker, data, cio_base_inputs)
                
                    if scenario_res.get("expected_value_status") == "error":
                        st.warning("⚠️ EPSがマイナスか、十分な財務データが得られなかったため、シナリオ分析を計算できませんでした。")
                    else:
                        curr_p = scenario_res["current_price"]
                        status = scenario_res["expected_value_status"]
                        summary_ja = scenario_res["summary_label_ja"]
                        ev_pct = scenario_res["expected_value_pct"]
                        rr = scenario_res["risk_reward_ratio"]
                        ev_score = scenario_res["expected_value_score"]
                    
                        # ステータスバナー
                        bg_color = {
                            "attractive": "rgba(16,185,129,0.15)",
                            "neutral": "rgba(245,158,11,0.15)",
                            "unattractive": "rgba(239,68,68,0.15)"
                        }.get(status, "rgba(255,255,255,0.05)")
                    
                        border_c = {
                            "attractive": "#10b981",
                            "neutral": "#f59e0b",
                            "unattractive": "#ef4444"
                        }.get(status, "#64748b")
                    
                        st.markdown(f"""
                        <div style="background:{bg_color}; border-left:6px solid {border_c}; padding:16px; border-radius:8px; margin-bottom:20px;">
                            <h3 style="margin:0; color:{border_c};">{summary_ja}</h3>
                            <div style="display:flex; gap:20px; margin-top:10px;">
                                <div style="font-size:1.1rem;">期待値 (EV) : <strong style="color:{"#10b981" if ev_pct>0 else "#ef4444"}">{ev_pct:+.1f}%</strong></div>
                                <div style="font-size:1.1rem;">リスクリワード比 : <strong>{rr:.2f}x</strong></div>
                                <div style="font-size:1.1rem;">評価スコア : <strong>{ev_score}/100</strong></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                        # 3シナリオのカード
                        col_bull, col_base, col_bear = st.columns(3)
                    
                        with col_bull:
                            st.markdown("#### 🌟 Bull Case (強気)")
                            st.caption(f"発生確率: {scenario_res['bull_probability']*100:.0f}%")
                            up_pct = scenario_res['bull_upside_pct']
                            st.metric("目標株価", f"${scenario_res['bull_target_price']:,.2f}", f"{up_pct:+.1f}%", delta_color="normal")
                            st.caption("好決算継続、成長率上振れ、高PER維持のケース")
                        
                        with col_base:
                            st.markdown("#### 🟰 Base Case (中立)")
                            st.caption(f"発生確率: {scenario_res['base_probability']*100:.0f}%")
                            bsc_pct = scenario_res['base_upside_pct']
                            col_normal = "normal" if bsc_pct >= 0 else "inverse"
                            st.metric("妥当株価", f"${scenario_res['base_target_price']:,.2f}", f"{bsc_pct:+.1f}%", delta_color=col_normal)
                            st.caption("現状の成長予想延長、妥当PERへ回帰のケース")
                        
                        with col_bear:
                            st.markdown("#### 📉 Bear Case (弱気)")
                            st.caption(f"発生確率: {scenario_res['bear_probability']*100:.0f}%")
                            dn_pct = scenario_res['bear_downside_pct']
                            st.metric("下値メド", f"${scenario_res['bear_target_price']:,.2f}", f"{dn_pct:+.1f}%", delta_color="inverse")
                            st.caption("成長鈍化、PER縮小、市場の期待低下のケース")
                        
                        st.divider()
                        col_flag_pos, col_flag_neg = st.columns(2)
                        with col_flag_pos:
                            st.markdown("##### ✅ アピールポイント")
                            if not scenario_res["quality_flags"]:
                                st.write("該当なし")
                            for f in scenario_res["quality_flags"]:
                                st.markdown(f"- {f}")
                    
                        with col_flag_neg:
                            st.markdown("##### ⚠️ 警戒ポイント")
                            if not scenario_res["risk_flags"]:
                                st.write("該当なし")
                            for f in scenario_res["risk_flags"]:
                                st.markdown(f"- {f}")
                            
                        st.caption(scenario_res["comment"])

    
            # 9. CIO 総合投資判断ダッシュボード（7軸統合）
            if tab_cio:
                with tab_cio:
                    st.divider()
                    st.markdown('<div class="section-title">🎯 CIO 総合投資判断ダッシュボード（7軸統合）</div>', unsafe_allow_html=True)
                    st.caption("トレンド・エントリー・RS・決算品質・需給・バリュエーション・イベント安全性の7軸を統合し、最終投資判断を生成します。")

                    # ─── 7軸スコア収集（キャッシュ付き統合関数） ───
                    with st.spinner("7軸統合スコアを計算中（初回は少し時間がかかります）..."):
                        cio_inputs  = build_cio_decision_inputs(ticker)
                        final_judge = derive_final_judgment(cio_inputs, ticker, data)

                    scores_7     = cio_inputs.get("scores", {})
                    total_score  = cio_inputs.get("total_score", 50)
                    verdict      = final_judge.get("verdict", "monitor")
                    verdict_ja   = final_judge.get("verdict_ja", "👁️ 監視継続")
                    verdict_desc = final_judge.get("verdict_desc", "")
                    wait_event   = final_judge.get("wait_event_flag", False)

                    # ─── 1. 最終ジャッジバナー ───────────────────────
                    verdict_cfg = {
                        "buy":          ("#10b981", "rgba(16,185,129,0.18)", "🟢 今すぐ買いの好機"),
                        "pullback_buy": ("#34d399", "rgba(52,211,153,0.13)", "🔵 押し目を待って買い"),
                        "wait_event":   ("#f59e0b", "rgba(245,158,11,0.13)", "⏳ イベント通過を待て"),
                        "monitor":      ("#3b82f6", "rgba(59,130,246,0.13)", "👁️ ウォッチリスト継続"),
                        "pass":         ("#ef4444", "rgba(239,68,68,0.13)",  "🚫 現時点では見送り"),
                    }
                    v_color, v_bg, v_top = verdict_cfg.get(verdict, verdict_cfg["monitor"])

                    st.markdown(
                        f'<div style="background:{v_bg}; border:2px solid {v_color}; border-radius:14px; '
                        f'padding:20px 24px; margin-bottom:16px;">'
                        f'<div style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.08em;">CIO 最終判断</div>'
                        f'<div style="font-size:2rem; font-weight:900; color:{v_color}; margin:4px 0;">'
                        f'{verdict_ja}</div>'
                        f'<div style="font-size:0.95rem; color:#e2e8f0;">{verdict_desc}</div>'
                        f'<div style="margin-top:10px; font-size:1.4rem; font-weight:700; color:#94a3b8;">'
                        f'総合スコア: <span style="color:{v_color};">{total_score:.0f} / 100</span></div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    if wait_event:
                        st.warning("⚠️ イベントリスクが高い状態です。「📅 イベントリスク」タブで詳細を確認してください。")

                    # ─── 2. 7軸レーダーチャート + スコアバー ───────────
                    st.divider()
                    col_radar7, col_bars7 = st.columns([1, 1])

                    # レーダー用ラベル
                    radar_labels = {
                        "trend_score":         "トレンド",
                        "entry_score":         "エントリー",
                        "rs_score":            "相対強度",
                        "earnings_score":      "決算品質",
                        "supply_demand_score": "需給",
                        "valuation_score":     "バリュエーション",
                        "event_safety_score":  "イベント安全性",
                    }
                    radar_scores = {radar_labels[k]: scores_7.get(k, 50) for k in radar_labels}

                    with col_radar7:
                        st.markdown("#### 📡 7軸統合レーダーチャート")
                        fig_radar7 = create_radar_chart(radar_scores)
                        st.plotly_chart(fig_radar7, use_container_width=True)

                    with col_bars7:
                        st.markdown("#### 📊 各軸スコア詳細")
                        weights_disp = {
                            "trend_score":         ("トレンド",         "週足Stage/SEPA",   0.20),
                            "entry_score":         ("エントリー",       "週足+日足整合",     0.20),
                            "rs_score":            ("相対強度",         "対SPY/セクター",    0.15),
                            "earnings_score":      ("決算品質",         "売上/EPS/CF反応",  0.15),
                            "supply_demand_score": ("需給",             "機関/空売/出来高", 0.12),
                            "valuation_score":     ("バリュエーション", "PER帯/同業/PEG",   0.10),
                            "event_safety_score":  ("イベント安全性",   "決算/FOMC/CPI",    0.08),
                        }
                        for key, (label, sub, wt) in weights_disp.items():
                            sc = scores_7.get(key, 50)
                            bar_color = "#10b981" if sc >= 70 else "#f59e0b" if sc >= 45 else "#ef4444"
                            st.markdown(f"""
                            <div style="margin-bottom:10px;">
                              <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
                                <span style="color:#e2e8f0; font-weight:600;">{label}
                                  <span style="color:#64748b; font-weight:400;"> ({sub})</span></span>
                                <span style="color:{bar_color}; font-weight:700;">{sc} <span style="color:#64748b; font-size:0.7rem;">wt:{wt:.0%}</span></span>
                              </div>
                              <div style="height:8px; background:rgba(255,255,255,0.07); border-radius:4px; margin-top:4px;">
                                <div style="width:{sc}%; height:100%; background:{bar_color}; border-radius:4px;"></div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)

                    # ─── 3. 強み / リスク / エントリー条件 / 無効化条件 ──
                    st.divider()
                    col_str, col_rsk = st.columns(2)

                    with col_str:
                        st.markdown("#### ✅ 主な強み（上位3軸）")
                        for s in final_judge.get("strengths", []):
                            st.markdown(f"- **{s}**")

                    with col_rsk:
                        st.markdown("#### ⚠️ 主なリスク")
                        for r in final_judge.get("risks", []):
                            st.markdown(f"- **{r}**")

                    st.divider()
                    col_ec, col_inv = st.columns(2)

                    with col_ec:
                        st.markdown("#### 🎯 ベストエントリー条件")
                        for ec in final_judge.get("entry_conditions", []):
                            st.markdown(f"- {ec}")

                    with col_inv:
                        st.markdown("#### 🚫 無効化条件（損切り基準）")
                        for inv in final_judge.get("invalidation", []):
                            st.markdown(f"- {inv}")

                    # ─── 4. 投資家タイプ & スコア一覧テーブル ──────────
                    st.divider()
                    col_type, col_table = st.columns([1, 2])
                    with col_type:
                        st.markdown("#### 🏷️ 投資スタイル分類")
                        inv_type = final_judge.get("investor_type", "—")
                        st.markdown(
                            f'<div style="background:rgba(59,130,246,0.13); border-left:4px solid #3b82f6; '
                            f'border-radius:8px; padding:12px 16px;">'
                            f'<div style="font-size:1.0rem; font-weight:700; color:#93c5fd;">{inv_type}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    with col_table:
                        st.markdown("#### 📋 7軸スコア一覧")
                        table_rows = []
                        for key, (label, sub, wt) in weights_disp.items():
                            sc = scores_7.get(key, 50)
                            emoji = "🟢" if sc >= 68 else "🟡" if sc >= 42 else "🔴"
                            table_rows.append({
                                "軸":   f"{emoji} {label}",
                                "スコア": sc,
                                "評価基準": sub,
                                "重み": f"{wt:.0%}",
                            })
                        st.dataframe(table_rows, use_container_width=True, hide_index=True)

                    # ─── 5. VCP & トレードプラン（既存機能を移植） ──────
                    st.divider()
                    st.markdown('<div class="section-title">📐 VCP分析 & トレードプラン (ミネルヴィニ式)</div>', unsafe_allow_html=True)

                    cio_hist = fetch_price_history(ticker, "1y")
                    if cio_hist is not None and not cio_hist.empty:
                        trade_plan = analyze_vcp_and_trade_plan(ticker, data, cio_hist)
                        col_vcp, col_trade = st.columns(2)

                        with col_vcp:
                            st.markdown("##### 🔬 ボラティリティ収縮 (VCP)")
                            vcp_status = trade_plan.get("vcp_status", "不明")
                            if "収縮" in vcp_status:
                                st.success(f"✅ {vcp_status}")
                            else:
                                st.warning(f"⚠️ {vcp_status}")
                            st.caption(f"週間レンジ推移: {trade_plan.get('vcp_desc', '—')}")
                            st.info("💡 VCP はボラティリティが段階的に縮小するパターンです。ブレイクアウト前のベース形成の兆候として注目されます。")

                        with col_trade:
                            st.markdown("##### 📊 トレードプラン")
                            buy_point  = trade_plan.get("buy_point")
                            stop_loss  = trade_plan.get("stop_loss_price")
                            pos_size   = trade_plan.get("position_size_pct")
                            curr_price = data.get("price", 0)
                            if buy_point:
                                gap_to_bp = ((buy_point - curr_price) / curr_price * 100) if curr_price else 0
                                st.metric("⬆️ ブレイクアウト・ポイント", f"${buy_point:,.2f}", delta=f"現在値から {gap_to_bp:+.1f}%")
                            if stop_loss:
                                loss_pct = ((stop_loss - buy_point) / buy_point * 100) if buy_point else -7
                                st.metric("🛑 損切りライン (-7%)", f"${stop_loss:,.2f}", delta=f"{loss_pct:.1f}%", delta_color="inverse")
                            if pos_size:
                                st.metric("📏 推奨ポジションサイズ", f"{pos_size*100:.1f}%",
                                          help="総資産の1.25%をリスク上限とし、損切り幅から逆算した推奨比率。最大25%。")
                    else:
                        st.info("価格データが取得できなかったため、VCP分析を実行できませんでした。")

                    st.caption("⚠️ 本ダッシュボードは情報提供を目的としたものであり、特定の投資行動を推奨するものではありません。投資判断はご自身の責任でお願いいたします。")

            # 10. 銘柄タイプ分類 (Stock Playbook)
            if tab_playbook:
                with tab_playbook:
                    st.divider()
                    st.markdown('<div class="section-title">🗂️ 銘柄タイプ・戦略分類 (Stock Playbook)</div>', unsafe_allow_html=True)
                    st.caption("対象銘柄が現在どのタイプの戦術に適しているかを分類し、具体的な行動指針を提示します。")
                
                    with st.spinner("戦術の分類判定中..."):
                        cio_base_inputs = build_cio_decision_inputs(ticker)
                        playbook_res = determine_stock_playbook(ticker, cio_base_inputs)
                
                    pb_ja = playbook_res["stock_playbook_type_label_ja"]
                    conf_ja = playbook_res["playbook_confidence_label_ja"]
                    bg_col = playbook_res.get("color_bg", "rgba(255,255,255,0.05)")
                    bd_col = playbook_res.get("color_border", "#64748b")
                
                    st.markdown(f"""
                    <div style="background:{bg_col}; border-left:6px solid {bd_col}; padding:20px; border-radius:8px; margin-bottom:20px;">
                        <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:4px;">推奨プレイブック - 確信度: {conf_ja}</div>
                        <div style="color:{bd_col}; font-size:2rem; font-weight:800; margin-bottom:8px;">{pb_ja}</div>
                        <div style="font-size:1.05rem; color:#e2e8f0;">{playbook_res['comment']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                    if playbook_res["secondary_type"]:
                        st.info(f"💡 **補足:** 本来のトレンドは「{playbook_res['secondary_type_label_ja']}」ですが、リスク要因により現在の分類が優先されています。")
                
                    col_pb1, col_pb2 = st.columns(2)
                    with col_pb1:
                        st.markdown("#### ✅ 判定理由")
                        for rsn in playbook_res["playbook_reason"]:
                            st.markdown(f"- {rsn}")
                    with col_pb2:
                        st.markdown("#### 🎯 特徴フラグ")
                        for flg in playbook_res["playbook_flags"]:
                            st.markdown(f"- `{flg}`")
                        
                    st.divider()
                    st.markdown("#### 🧭 行動指針 (Action Plan)")
                    st.success(f"**👍 最善の行動:**\n\n{playbook_res['best_action']}")
                    st.error(f"**🚫 避けるべき行動:**\n\n{playbook_res['avoid_action']}")
                
                    st.markdown("#### ⚡ 発動・撤退条件")
                    st.info(f"**🟢 発動(トリガー)条件:** {playbook_res['trigger_condition']}")
                    st.warning(f"**⚠️ 無効化(警告)条件:** {playbook_res['warning_condition']}")

            # 11. AI最終ジャッジ
            if tab_ai_final:
                with tab_ai_final:
                    st.divider()
                    st.markdown('<div class="section-title">✅ AI 最終ジャッジ (Gemini 定型プロンプト出力)</div>', unsafe_allow_html=True)
                    st.caption("CIOダッシュボードの7軸の定量・定性結果をAIへ渡し、ぶれのない定型レイアウトで最終判断を生成します。")

                    if not GENAI_AVAILABLE:
                        st.warning("⚠️ Gemini APIが無効または未設定です。設定を確認してください。")
                    else:
                        api_key = get_gemini_api_key()
                        if not api_key:
                            st.info("Gemini API Key が未設定の場合は「🤖 AI分析」タブで設定してください。")
                        else:
                            if st.button("🚀 AI 最終ジャッジを生成", type="primary"):
                                with st.spinner("AI が 全データとCIO評価を解析中..."):
                                    # CIOの入力と判定を取得 (すでにtab_cioでキャッシュされていれば早い)
                                    cio_inputs = build_cio_decision_inputs(ticker)
                                    final_judge_info = derive_final_judgment(cio_inputs, ticker, data)
                                
                                    ai_verdict = generate_ai_final_verdict(ticker, data, cio_inputs, final_judge_info)
                                
                                    if ai_verdict:
                                        st.success("解析完了！")
                                        # --- UI 描画 ---
                                        # バナー表現
                                        vd = ai_verdict.get("final_verdict", "monitor")
                                        vd_ja = ai_verdict.get("final_verdict_label_ja", "監視")
                                        sum_line = ai_verdict.get("one_line_summary", "")
                                        conf_ja = ai_verdict.get("confidence_label_ja", "中確信")
                                    
                                        v_colors = {
                                            "buy": ("#10b981", "rgba(16,185,129,0.1)"),
                                            "buy_on_pullback": ("#34d399", "rgba(52,211,153,0.1)"),
                                            "monitor": ("#3b82f6", "rgba(59,130,246,0.1)"),
                                            "pass": ("#ef4444", "rgba(239,68,68,0.1)")
                                        }
                                        c_main, c_bg = v_colors.get(vd, v_colors["monitor"])
                                    
                                        st.markdown(f"""
                                        <div style="background:{c_bg}; border-left:6px solid {c_main}; border-radius:8px; padding:20px; margin-bottom:20px;">
                                            <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:4px;">AI 統合ジャッジ - {conf_ja}</div>
                                            <div style="color:{c_main}; font-size:2.2rem; font-weight:800; margin-bottom:10px;">{vd_ja}</div>
                                            <div style="font-size:1.1rem; color:#e2e8f0; font-weight:500;">{sum_line}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("#### ✅ 判断理由")
                                            for rsn in ai_verdict.get("top_reasons", []):
                                                st.markdown(f" - {rsn}")
                                        with col2:
                                            st.markdown("#### ⚠️ 最大のリスク")
                                            for rsk in ai_verdict.get("top_risks", []):
                                                st.markdown(f" - {rsk}")
                                            
                                        st.divider()
                                        col3, col4 = st.columns(2)
                                        with col3:
                                            st.markdown("#### 🎯 ベストエントリー条件")
                                            st.info(f"💡 {ai_verdict.get('best_entry_condition', '—')}")
                                        with col4:
                                            st.markdown("#### 🚫 無効化・損切り条件")
                                            st.error(f"⚠️ {ai_verdict.get('invalidation_condition', '—')}")
                                        
                                        st.divider()
                                        st.markdown("#### 📋 アクションプラン")
                                        action_html = "".join([f"<li style='margin-bottom:8px;'>{act}</li>" for act in ai_verdict.get("action_plan", [])])
                                        st.markdown(f"<ul style='color:#e2e8f0; font-size:1rem;'>{action_html}</ul>", unsafe_allow_html=True)
                                    
                                        st.divider()
                                        st.markdown("#### 💬 フル・コメンタリー")
                                        st.caption(f"推奨投資家タイプ: **{ai_verdict.get('investor_type_fit', '—')}**")
                                        st.markdown(f"""
                                        <div style="background:rgba(255,255,255,0.05); padding:16px; border-radius:8px; line-height:1.7;">
                                            {ai_verdict.get("full_commentary", "—")}
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.error("AIからのJSONレスポンスのパースに失敗しました。時間をおいて再実行してください。")

    else:
        st.info("👆 ティッカーシンボルを入力して分析を開始してください。")

# ─────────────────────────────────────────────
# 最終的なルーティング
# ─────────────────────────────────────────────
if st.session_state.app_mode == "テーマ・エクスプローラー":
    render_theme_explorer()
elif st.session_state.app_mode == "セクター・アナライザー":
    render_sector_analyzer()
else:
    render_stock_analyzer()
