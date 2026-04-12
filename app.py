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
def get_translated_summary(summary_text: str) -> str:
    """事業概要をAIなしで安定して日本語に翻訳する。"""
    if not summary_text:
        return "事業概要のデータがありません。"

    translated = translate_to_japanese(summary_text)
    return translated



# ─────────────────────────────────────────────
# データ取得
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_stock_data(ticker: str) -> dict | None:
    """yfinance を使って株価指標を取得する。"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # 有効なデータかチェック（空辞書 or 名前なし → 無効）
        if not info or "shortName" not in info:
            return None

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
            # 理論株価・分析用
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            "eps_growth": info.get("earningsGrowth"),
            "revenue_growth": info.get("revenueGrowth"),
            "beta": info.get("beta"),
            "profit_margins": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "operating_margins": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            # マーケット・データ用に追加
            "avg_vol_3m": info.get("averageVolume"),
            "avg_vol_10d": info.get("averageVolume10days"),
            "short_ratio": info.get("shortPercentOfFloat"),
            "ex_dividend_date": info.get("exDividendDate"),
        }

        # セクター等の欠損補完 (fast_info / basic_info へのフォールバック)
        try:
            if not res.get("sector") or res.get("sector") == "—":
                if hasattr(stock, "fast_info") and "sector" in stock.fast_info:
                    res["sector"] = stock.fast_info["sector"]
            if not res.get("industry") or res.get("industry") == "—":
                if hasattr(stock, "fast_info") and "industry" in stock.fast_info:
                    res["industry"] = stock.fast_info["industry"]
            if not res.get("exchange") or res.get("exchange") == "—":
                if hasattr(stock, "fast_info") and "exchange" in stock.fast_info:
                    res["exchange"] = stock.fast_info["exchange"]
        except Exception:
            pass

        # 最終的なデフォルト値の適用
        for k in ["sector", "industry", "exchange"]:
            if not res.get(k):
                res[k] = "—"

        # 決算日の取得 (calendar属性から)
        try:
            cal = ticker.calendar
            if isinstance(cal, dict) and "Earnings Date" in cal:
                res["earnings_date"] = cal["Earnings Date"][0]
            elif hasattr(cal, "iloc") and not cal.empty:
                # 稀にDataFrameで返るケースへの対応
                res["earnings_date"] = cal.iloc[0, 0]
            else:
                res["earnings_date"] = None
        except:
            res["earnings_date"] = None

        # 日本語化処理（固定マップのみ、AIは使用しない）
        res["sector_display"] = SECTOR_JA_MAP.get(res["sector"], res["sector"])
        res["industry_display"] = INDUSTRY_JA_MAP.get(res["industry"], res["industry"])

        return res
    except Exception as e:
        print(f"Fetch Error for {ticker}: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_financials(ticker: str) -> dict | None:
    """yfinance を使って過去の財務データ（損益計算書 & キャッシュフロー）を取得する。"""
    try:
        stock = yf.Ticker(ticker)

        # 年次損益計算書
        income_stmt = stock.financials  # columns = 日付, rows = 項目
        cashflow = stock.cashflow

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

        return result
    except Exception:
        return None


@st.cache_data(ttl=300)
def fetch_quarterly_financials(ticker: str) -> dict | None:
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

        return result
    except Exception as e:
        print(f"Quarterly Financials Error: {e}")
        return None


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
# メイン UI 実行
# ─────────────────────────────────────────────
st.title("Momentum Master US")
st.markdown('<div class="subtitle">AI-Powered Institutional Grade Stock Analysis Dashboard</div>', unsafe_allow_html=True)

ticker = st.text_input("📈 分析したいティッカーシンボルを入力 (例: NVDA, TSMC, AAPL)", value="", help="米国株のティッカー（大文字）を入力してください。").upper()

if ticker:
    with st.spinner(f"{ticker} のデータを取得中..."):
        data = fetch_stock_data(ticker)
        
    if not data:
        st.error(f"❌ '{ticker}' のデータが見つかりませんでした。")
    else:
        # ヘッダー情報
        st.markdown(f'<div class="company-name">{data["name"]} ({ticker})</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="company-sector">{data["sector_display"]} | {data["industry_display"]} | {data["exchange"]}</div>', unsafe_allow_html=True)
        
        # ─── タブ切り替え ───
        tab_basic, tab_fund, tab_chart, tab_peers, tab_canslim, tab_sepa, tab_risk, tab_ai, tab_cio = st.tabs(
            ["📊 基本情報", "📈 財務/バリュ", "🔍 チャート", "🏢 競合比較", "💰 CAN SLIM", "🏆 SEPA分析", "🛡️ リスク/予想", "🤖 AI分析", "🎯 CIO判断"]
        )

        # 1. 基本情報
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
                fin = fetch_financials(ticker)
            else:
                fin = fetch_quarterly_financials(ticker)
            
            if fin:
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.plotly_chart(create_revenue_chart(fin["dates"], fin.get("revenue"), fin.get("net_income")), use_container_width=True)
                with col_c2:
                    st.plotly_chart(create_cashflow_chart(fin.get("cf_dates", fin["dates"]), fin.get("operating_cf", [])), use_container_width=True)
            else:
                st.info("財務データが取得できませんでした。")

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
        with tab_chart:
            st.divider()
            period = st.selectbox("期間", ["1ヶ月", "6ヶ月", "1年", "5年"], index=2)
            hist = fetch_price_history(ticker, PERIOD_MAP[period])
            if hist is not None:
                st.plotly_chart(create_technical_chart(hist, ticker), use_container_width=True)

        # 4. 競合比較
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

        # 7. リスク・予想
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

        # 8. AI分析
        with tab_ai:
            st.divider()
            st.markdown('<div class="section-title">🤖 Gemini AI 統合分析レポート</div>', unsafe_allow_html=True)
            
            st.info("""
            **分析の根拠となるデータ項目:**
            1. **財務の質** (ROE/ROIC, キャッシュフローの健全性)
            2. **長期成長トレンド** (売上高・純利益の推移)
            3. **理論株価** (DCF分析による妥当価格との乖離)
            4. **競合比較ランキング** (セクター内での相対的な位置付け)
            5. **プロの視点** (アナリストの目標株価・推奨度)
            6. **内部関係者の動き** (インサイダー取引の履歴)
            7. **テクニカル** (RSI・SMAトレンドの裏付け)
            
            これらの多角的なデータを最新の **Gemini 2.0 Flash** モデルが統合し、分析レポートを生成します。
            """)
            
            # --- 成長ドライバ・カード (AVGO例) ---
            if ticker == "AVGO":
                st.markdown("### 📈 主要成長ドライバ分析 (Summary)")
                avgo_drivers = [
                    {"id": 1, "theme": "Custom AI Accelerator (XPU) の独占的拡大", "impact": "Google TPU v6/Meta MTIA等のカスタムASIC出荷が加速し、AI半導体売上は84.4億ドル（+106% YoY）を記録。主要CSPとの共同開発でMRVLに対し規模の経済で圧倒。", "status": "positive"},
                    {"id": 2, "theme": "AIデータセンターのEthernet移行と帯域幅の飛躍", "impact": "1M GPU クラスター向けに 102.4T 帯域の Tomahawk 6 出荷開始。InfiniBandからEthernetへの主導権転換によりネットワーク事業が高成長。", "status": "positive"},
                    {"id": 3, "theme": "接続コスト最適化としての DAC (銅線) 推進", "impact": "スケールアップ領域で光学部品コストを回避するDAC（直接接続銅線）戦略を強化。電力的・コスト的に競合に対し強力なマージン優位を確保。", "status": "positive"},
                    {"id": 4, "theme": "ASIC市場の Broadcom/Marvell 二強体制の固定化", "impact": "最先端プロセス(3nm)での開発能力を持つ唯一の二社として寡占化が進展。特にAVGOは最高難度のハイパースケーラ案件を独占、シェア70%超を維持。", "status": "positive"},
                    {"id": 5, "theme": "次世代光技術 CPO (Bailly) の先行商用化", "impact": "業界初の1.6T/3.2T対応CPO『Bailly』を投入。従来型比で消費電力を50%削減し、次世代AIインフラにおける電力密度の限界を打破。", "status": "positive"},
                    {"id": 6, "theme": "VMware (VCF) サブスクリプション移行の成否", "impact": "VCF全社導入が進み利益率向上に寄与（EBITDAマージン68%）。一方、ライセンス体系変更による一部解約リスクは残るもののLTV向上は確実視。", "status": "neutral"},
                    {"id": 7, "theme": "CoWoS および HBM 供給キャパシティの制約", "impact": "売上の約半数が先端パッケージング(CoWoS)とHBM供給に依存。バックログは増大しているが、サプライヤー側の生産能力が通期アップサイドの制限要因。", "status": "critical"}
                ]
                render_growth_driver_cards(avgo_drivers)
                st.write("<br>", unsafe_allow_html=True)
            # ------------------------------------

            api_key = get_gemini_api_key()
            if not api_key:
                api_key = st.text_input("Gemini API Key を入力してください", type="password")
            
            if api_key:
                prompt = build_analysis_prompt(ticker, data, fin=fetch_financials(ticker), adv_fin=fetch_advanced_financials(ticker), analyst=fetch_analyst_data(ticker))
                if st.button("AI分析を実行", type="primary"):
                    with st.spinner("AIがデータを解析中..."):
                        report = call_gemini(api_key, SYSTEM_PROMPT, prompt)
                        st.markdown(report)
            else:
                st.warning("API Key が未設定です。")

        # 9. CIO 総合投資判断ダッシュボード
        with tab_cio:
            st.divider()
            st.markdown('<div class="section-title">🎯 CIO 総合投資判断ダッシュボード</div>', unsafe_allow_html=True)
            st.caption("バリュエーション・モメンタム・財務の質を統合し、最終的な投資判断を支援します。")

            # ─── 必要データの取得 ───
            with st.spinner("統合診断データを生成中…"):
                cio_fin = fetch_financials(ticker)
                cio_adv = fetch_advanced_financials(ticker)
                cio_sepa = evaluate_sepa(ticker)
                cio_canslim = evaluate_canslim(ticker)
                cio_fscore = calculate_f_score(ticker)
                cio_hist = fetch_price_history(ticker, "1y")

            # ─── 1. 統合スコア算出 ───
            scores = {}

            # 成長性 (CAN SLIM ベース, 0-100)
            if cio_canslim:
                cs_passes = sum(1 for v in cio_canslim.values() if v.get('pass'))
                scores["成長性"] = min(100, int((cs_passes / max(1, len(cio_canslim))) * 100))
            else:
                scores["成長性"] = 0

            # トレンド (SEPA ベース, 0-100)
            if cio_sepa:
                sepa_passes = sum(1 for v in cio_sepa.values() if v.get('pass'))
                scores["トレンド"] = min(100, int((sepa_passes / max(1, len(cio_sepa))) * 100))
            else:
                scores["トレンド"] = 0

            # 安全性 (F-Score ベース, 0-100)
            if cio_fscore:
                f_passes = sum(1 for v in cio_fscore.values() if v.get('pass'))
                scores["安全性"] = min(100, int((f_passes / 9) * 100))
            else:
                scores["安全性"] = 0

            # 割安性 (DCF + PER ベース, 0-100)
            val_score = 50  # デフォルト
            pe = data.get("pe_ratio")
            if pe and pe > 0:
                if pe < 15:
                    val_score = 90
                elif pe < 25:
                    val_score = 70
                elif pe < 40:
                    val_score = 50
                else:
                    val_score = 25
            # 新モデルによる補正
            base_eps = data.get("eps_trailing")
            if base_eps and base_eps > 0:
                try:
                    # デフォルト設定 (10年、売上成長率、現在のPER) で算出
                    def_g = data.get("revenue_growth", 0.1) if data.get("revenue_growth") is not None else 0.1
                    def_pe = data.get("pe_ratio", 20) if data.get("pe_ratio") is not None else 20
                    
                    # ダイナミック目標年利の適用 (CIOダッシュボード用)
                    beta_cio = data.get("beta", 1.0) if data.get("beta") is not None else 1.0
                    eps_g_cio = data.get("eps_growth", def_g) if data.get("eps_growth") is not None else 0.1
                    def_r = 0.05 + (beta_cio * 0.05) + (max(0, eps_g_cio) * 0.2)
                    
                    val_res = calculate_earnings_valuation(base_eps, def_g, 10, def_pe, def_r)
                    
                    if val_res and data.get("price"):
                        val_gap = (val_res["total_value"] - data["price"]) / data["price"]
                        if val_gap > 0.5:
                            val_score = min(100, val_score + 25)
                        elif val_gap > 0:
                            val_score = min(100, val_score + 10)
                        elif val_gap < -0.3:
                            val_score = max(0, val_score - 20)
                except Exception:
                    pass
            scores["割安性"] = val_score

            # モメンタム (52週高値からの距離 + RSI)
            mom_score = 50
            if data.get("price") and data.get("fifty_two_week_high") and data.get("fifty_two_week_low"):
                h52 = data["fifty_two_week_high"]
                l52 = data["fifty_two_week_low"]
                p = data["price"]
                pos = (p - l52) / (h52 - l52) if (h52 - l52) > 0 else 0.5
                mom_score = int(pos * 100)
            if cio_hist is not None and not cio_hist.empty:
                rsi_val = cio_hist["RSI"].iloc[-1] if pd.notna(cio_hist["RSI"].iloc[-1]) else 50
                # RSI 50付近が最も健全
                rsi_factor = max(0, 100 - abs(rsi_val - 55) * 2)
                mom_score = int(mom_score * 0.6 + rsi_factor * 0.4)
            scores["モメンタム"] = min(100, max(0, mom_score))

            # ─── 2. レーダーチャート & 総合スコア表示 ───
            col_radar, col_summary = st.columns([1, 1])

            with col_radar:
                st.markdown("#### 📡 5軸統合レーダーチャート")
                fig_radar = create_radar_chart(scores)
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_summary:
                st.markdown("#### 📋 各軸スコア")
                total_avg = sum(scores.values()) / len(scores)

                # 総合判定
                if total_avg >= 75:
                    st.success(f"🟢 総合スコア: **{total_avg:.0f}点** — 強気シグナル")
                elif total_avg >= 50:
                    st.warning(f"🟡 総合スコア: **{total_avg:.0f}点** — 中立")
                else:
                    st.error(f"🔴 総合スコア: **{total_avg:.0f}点** — 弱気シグナル")

                st.progress(total_avg / 100)
                st.markdown("<br>", unsafe_allow_html=True)

                for axis_name, axis_score in scores.items():
                    bar_color = "#34d399" if axis_score >= 70 else "#fbbf24" if axis_score >= 40 else "#f87171"
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="width: 90px; font-size: 0.85rem; color: #cbd5e1;">{axis_name}</span>
                        <div style="flex: 1; height: 10px; background: rgba(255,255,255,0.08); border-radius: 5px; margin: 0 10px;">
                            <div style="width: {axis_score}%; height: 100%; background: {bar_color}; border-radius: 5px;"></div>
                        </div>
                        <span style="font-size: 0.85rem; font-weight: 700; color: {bar_color};">{axis_score}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # ─── 3. VCP & トレードプラン ───
            st.divider()
            st.markdown('<div class="section-title">📐 VCP分析 & トレードプラン (ミネルヴィニ式)</div>', unsafe_allow_html=True)

            if cio_hist is not None and not cio_hist.empty:
                trade_plan = analyze_vcp_and_trade_plan(ticker, data, cio_hist)

                col_vcp, col_trade = st.columns(2)

                with col_vcp:
                    st.markdown("##### 🔬 ボラティリティ収縮 (VCP)")
                    vcp_status = trade_plan.get("vcp_status", "不明")
                    is_contracting = "収縮" in vcp_status

                    if is_contracting:
                        st.success(f"✅ {vcp_status}")
                    else:
                        st.warning(f"⚠️ {vcp_status}")

                    st.caption(f"週間レンジ推移: {trade_plan.get('vcp_desc', '—')}")
                    st.info("💡 VCP（Volatility Contraction Pattern）はボラティリティが段階的に縮小していくパターンです。ブレイクアウト前のベース形成の兆候として注目されます。")

                with col_trade:
                    st.markdown("##### 📊 トレードプラン")

                    buy_point = trade_plan.get("buy_point")
                    stop_loss = trade_plan.get("stop_loss_price")
                    pos_size = trade_plan.get("position_size_pct")
                    curr_price = data.get("price", 0)

                    if buy_point:
                        gap_to_bp = ((buy_point - curr_price) / curr_price * 100) if curr_price else 0
                        st.metric("⬆️ ブレイクアウト・ポイント (52週高値)", f"${buy_point:,.2f}",
                                  delta=f"現在値から {gap_to_bp:+.1f}%", delta_color="normal")

                    if stop_loss:
                        loss_pct = ((stop_loss - buy_point) / buy_point * 100) if buy_point else -7
                        st.metric("🛑 損切りライン (-7%)", f"${stop_loss:,.2f}",
                                  delta=f"{loss_pct:.1f}%", delta_color="inverse")

                    if pos_size:
                        st.metric("📏 推奨ポジションサイズ", f"{pos_size*100:.1f}%",
                                  help="総資産の1.25%をリスク上限とし、損切り幅から逆算した推奨比率です。最大25%。")

            else:
                st.info("価格データが取得できなかったため、VCP分析を実行できませんでした。")

            # ─── 4. CIO コメント自動生成 ───
            st.divider()
            st.markdown('<div class="section-title">📝 CIO 投資判断コメント</div>', unsafe_allow_html=True)

            # ルールベースの自動コメント生成
            comments = []

            # 成長性
            if scores["成長性"] >= 70:
                comments.append("📈 **成長性が高い**: CAN SLIM基準の大半を満たしており、業績モメンタムは力強い。")
            elif scores["成長性"] <= 30:
                comments.append("📉 **成長性に懸念**: EPS成長率や売上モメンタムが基準を下回っている。")

            # トレンド
            if scores["トレンド"] >= 70:
                comments.append("🏆 **強い上昇トレンド**: ミネルヴィニの Stage 2 条件を大半満たしており、テクニカル的に有利なポジション。")
            elif scores["トレンド"] <= 30:
                comments.append("⚠️ **トレンドが弱い**: 中長期移動平均線を下回る局面にあり、新規エントリーは慎重に。")

            # 安全性
            if scores["安全性"] >= 70:
                comments.append("🛡️ **財務健全性良好**: F-Scoreが高く、収益性・流動性・効率性が揃っている。")
            elif scores["安全性"] <= 30:
                comments.append("🔴 **財務リスクあり**: F-Scoreが低く、レバレッジやキャッシュフローに課題がある可能性。")

            # 割安性
            if scores["割安性"] >= 70:
                comments.append("💎 **割安な水準**: PERやDCF分析から、現在の株価は本質的価値に対してディスカウントされている可能性が高い。")
            elif scores["割安性"] <= 30:
                comments.append("💸 **割高な水準**: バリュエーション指標が割高圏にあり、高い成長期待が既に織り込まれている。")

            # モメンタム
            if scores["モメンタム"] >= 70:
                comments.append("🚀 **モメンタムが強い**: 52週高値圏で推移しており、RSIも良好な水準にある。")
            elif scores["モメンタム"] <= 30:
                comments.append("⏸️ **モメンタムが弱い**: 52週安値圏にあり、底打ちのサインが出るまで待つべき局面。")

            # VCP
            if cio_hist is not None and not cio_hist.empty:
                trade_plan_for_comment = analyze_vcp_and_trade_plan(ticker, data, cio_hist)
                if "収縮" in trade_plan_for_comment.get("vcp_status", ""):
                    comments.append("🔍 **VCPパターンを形成中**: ボラティリティが段階的に縮小しており、ブレイクアウトの準備段階にある可能性。")

            # 総合判定
            if total_avg >= 75:
                comments.append(f"\n🟢 **総合判定: 強気** — 5軸平均 {total_avg:.0f}点。モメンタム型の買いに適した条件が整いつつある。")
            elif total_avg >= 50:
                comments.append(f"\n🟡 **総合判定: 中立** — 5軸平均 {total_avg:.0f}点。一部の指標に改善の余地がある。個別の強み/弱みを慎重に評価すべき。")
            else:
                comments.append(f"\n🔴 **総合判定: 弱気** — 5軸平均 {total_avg:.0f}点。複数の軸でリスクが顕在化しており、新規投資は推奨しにくい局面。")

            comment_text = "\n\n".join(comments)
            st.markdown(f'<div class="ai-report">{comment_text}</div>', unsafe_allow_html=True)

            st.caption("⚠️ 本ダッシュボードは情報提供を目的としたものであり、特定の投資行動を推奨するものではありません。投資判断はご自身の責任でお願いいたします。")

else:
    st.info("👆 ティッカーシンボルを入力して分析を開始してください。")
