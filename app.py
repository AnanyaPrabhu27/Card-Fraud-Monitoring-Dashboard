import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Fraud Monitoring Dashboard", layout="wide")

BLUE = "#3987e5"     # normal / single-series (dark-mode step)
ORANGE = "#d95926"   # fraud (dark-mode step)
GRID = "rgba(255,255,255,0.08)"
TEXT = "#c3c2b7"

# ---------------- Dark theme + background ----------------
st.markdown(
    """
    <style>
    /* Page background: deep navy with soft glows */
    .stApp {
        background:
            radial-gradient(1200px 600px at 10% -10%, rgba(57,135,229,0.18), transparent 60%),
            radial-gradient(900px 500px at 100% 0%, rgba(217,89,38,0.10), transparent 55%),
            linear-gradient(180deg, #0b1220 0%, #0a0f1a 100%);
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background: transparent; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 22, 36, 0.85);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 18px 20px;
    }
    [data-testid="stMetricLabel"] p {
        color: #8b93a7; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] { font-weight: 600; }

    /* Chart cards */
    [data-testid="stPlotlyChart"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 8px 6px 4px;
        overflow: hidden;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.04);
        border-radius: 10px 10px 0 0;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] { background: rgba(57,135,229,0.18); }

    h1 { letter-spacing: -0.02em; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path):
    df = pd.read_csv(path, parse_dates=["transaction_datetime"])
    df["date"] = df["transaction_datetime"].dt.date
    df["month"] = df["transaction_datetime"].dt.to_period("M").dt.to_timestamp()
    df["status"] = df["is_fraud"].map({0: "Legitimate", 1: "Fraud"})
    return df


def style(fig, height=360):
    """Shared look for every chart: clean background, light grid, no clutter."""
    fig.update_layout(
        height=height,
        margin=dict(l=60, r=20, t=50, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        title_font=dict(color="#f0efec", size=15),
        hoverlabel=dict(font_size=13, bgcolor="#1a2233", bordercolor="#2b3548", font_color="#f0efec"),
        bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, title=None, automargin=True)
    fig.update_yaxes(gridcolor=GRID, title=None, zeroline=False, automargin=True)
    return fig


def fraud_rate_by(data, col):
    out = (
        data.groupby(col)
        .agg(transactions=("is_fraud", "size"), fraud_rate=("is_fraud", "mean"))
        .reset_index()
    )
    return out


df = load_data("fraud.csv.gz")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

min_d, max_d = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input("Date range", (min_d, max_d), min_value=min_d, max_value=max_d)

channels = st.sidebar.multiselect(
    "Channel", sorted(df["transaction_channel"].unique()), default=sorted(df["transaction_channel"].unique())
)
categories = st.sidebar.multiselect(
    "Merchant category", sorted(df["merchant_category"].unique()), placeholder="All categories"
)
max_amt = float(df["transaction_amount"].max())
amount = st.sidebar.slider("Transaction amount ($)", 0.0, max_amt, (0.0, max_amt), step=10.0)

# Apply filters
f = df[df["transaction_channel"].isin(channels)]
if categories:
    f = f[f["merchant_category"].isin(categories)]
if len(date_range) == 2:
    f = f[(f["date"] >= date_range[0]) & (f["date"] <= date_range[1])]
f = f[f["transaction_amount"].between(*amount)]

st.sidebar.caption(f"Showing **{len(f):,}** of {len(df):,} transactions")

if f.empty:
    st.warning("No transactions match these filters. Try widening them.")
    st.stop()

# ---------------- Header + KPIs ----------------
st.title("Card Fraud Monitoring — 2026")
st.caption("Where fraud happens, what it costs, and the patterns behind it.")

fraud = f[f["is_fraud"] == 1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{len(f):,}")
c2.metric("Total volume", f"${f['transaction_amount'].sum():,.0f}")
c3.metric(
    "Fraud rate",
    f"{f['is_fraud'].mean():.2%}",
    delta=(f"{(f['is_fraud'].mean() - df['is_fraud'].mean()) * 100:+.2f} pp vs all data"
           if len(f) < len(df) else None),
    delta_color="inverse",
)
c4.metric("Fraud losses", f"${f['fraud_amount_lost'].sum():,.0f}", f"{len(fraud):,} fraud cases", delta_color="off")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Trends", "Where it happens", "Fraud types", "Patterns", "Flagged transactions"]
)

# ---------------- Tab 1: Trends ----------------
with tab1:
    monthly = (
        f.groupby("month")
        .agg(fraud_rate=("is_fraud", "mean"), losses=("fraud_amount_lost", "sum"))
        .reset_index()
    )
    left, right = st.columns(2)

    fig = px.line(monthly, x="month", y="fraud_rate", markers=True, title="Fraud rate by month")
    fig.update_traces(line=dict(color=BLUE, width=2), marker=dict(size=8),
                      hovertemplate="%{x|%B %Y}<br>Fraud rate: %{y:.2%}<extra></extra>")
    fig.update_yaxes(tickformat=".1%", rangemode="tozero")
    fig.update_layout(hovermode="x unified")
    left.plotly_chart(style(fig), width="stretch", theme=None)

    fig = px.bar(monthly, x="month", y="losses", title="Fraud losses by month")
    fig.update_traces(marker_color=ORANGE, marker_cornerradius=4,
                      hovertemplate="%{x|%B %Y}<br>Lost: $%{y:,.0f}<extra></extra>")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    right.plotly_chart(style(fig), width="stretch", theme=None)

# ---------------- Tab 2: Where it happens ----------------
with tab2:
    left, right = st.columns(2)

    by_channel = fraud_rate_by(f, "transaction_channel").sort_values("fraud_rate")
    fig = px.bar(by_channel, x="fraud_rate", y="transaction_channel", orientation="h",
                 title="Fraud rate by channel", custom_data=["transactions"])
    fig.update_traces(marker_color=BLUE, marker_cornerradius=4,
                      hovertemplate="%{y}<br>Fraud rate: %{x:.2%}<br>Transactions: %{customdata[0]:,}<extra></extra>")
    fig.update_xaxes(tickformat=".1%")
    left.plotly_chart(style(fig), width="stretch", theme=None)

    by_country = fraud_rate_by(f, "merchant_country")
    by_country = by_country[by_country["transactions"] >= 200].nlargest(10, "fraud_rate").sort_values("fraud_rate")
    fig = px.bar(by_country, x="fraud_rate", y="merchant_country", orientation="h",
                 title="Top 10 merchant countries by fraud rate", custom_data=["transactions"])
    fig.update_traces(marker_color=BLUE, marker_cornerradius=4,
                      hovertemplate="%{y}<br>Fraud rate: %{x:.2%}<br>Transactions: %{customdata[0]:,}<extra></extra>")
    fig.update_xaxes(tickformat=".1%")
    right.plotly_chart(style(fig), width="stretch", theme=None)
    right.caption("Countries with fewer than 200 transactions in the current filter are left out.")

    by_cat = fraud_rate_by(f, "merchant_category").sort_values("fraud_rate")
    fig = px.bar(by_cat, x="fraud_rate", y="merchant_category", orientation="h",
                 title="Fraud rate by merchant category", custom_data=["transactions"])
    fig.update_traces(marker_color=BLUE, marker_cornerradius=4,
                      hovertemplate="%{y}<br>Fraud rate: %{x:.2%}<br>Transactions: %{customdata[0]:,}<extra></extra>")
    fig.update_xaxes(tickformat=".1%")
    st.plotly_chart(style(fig, height=480), width="stretch", theme=None)

# ---------------- Tab 3: Fraud types ----------------
with tab3:
    if fraud.empty:
        st.info("No fraud cases in the current filter.")
    else:
        types = (
            fraud.groupby("fraud_type")
            .agg(cases=("is_fraud", "size"), losses=("fraud_amount_lost", "sum"))
            .reset_index()
        )
        types["avg_loss"] = types["losses"] / types["cases"]
        left, right = st.columns(2)

        t = types.sort_values("cases")
        fig = px.bar(t, x="cases", y="fraud_type", orientation="h", title="Fraud cases by type")
        fig.update_traces(marker_color=ORANGE, marker_cornerradius=4,
                          hovertemplate="%{y}<br>Cases: %{x:,}<extra></extra>")
        left.plotly_chart(style(fig), width="stretch", theme=None)

        t = types.sort_values("losses")
        fig = px.bar(t, x="losses", y="fraud_type", orientation="h", title="Total losses by type",
                     custom_data=["avg_loss"])
        fig.update_traces(marker_color=ORANGE, marker_cornerradius=4,
                          hovertemplate="%{y}<br>Lost: $%{x:,.0f}<br>Avg per case: $%{customdata[0]:,.0f}<extra></extra>")
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        right.plotly_chart(style(fig), width="stretch", theme=None)

# ---------------- Tab 4: Patterns ----------------
with tab4:
    left, right = st.columns(2)

    by_hour = fraud_rate_by(f, "transaction_hour")
    fig = px.line(by_hour, x="transaction_hour", y="fraud_rate", markers=True, title="Fraud rate by hour of day")
    fig.update_traces(line=dict(color=BLUE, width=2), marker=dict(size=8),
                      hovertemplate="%{x}:00<br>Fraud rate: %{y:.2%}<extra></extra>")
    fig.update_xaxes(dtick=2, ticksuffix=":00")
    fig.update_yaxes(tickformat=".1%", rangemode="tozero")
    left.plotly_chart(style(fig), width="stretch", theme=None)

    fig = px.box(f, x="status", y="transaction_amount", color="status", points=False,
                 title="Transaction amount: fraud vs legitimate", log_y=True,
                 category_orders={"status": ["Legitimate", "Fraud"]},
                 color_discrete_map={"Legitimate": BLUE, "Fraud": ORANGE})
    fig.update_layout(showlegend=False)
    fig.update_yaxes(tickprefix="$")
    right.plotly_chart(style(fig), width="stretch", theme=None)
    right.caption("Log scale, so small and very large amounts fit on one chart.")

    st.markdown("**Risk signals: how often fraud shows up when each flag is on vs off**")
    flags = {
        "International transaction": "international_transaction",
        "High-risk country": "high_risk_country",
        "Card present": "card_present",
        "Chip used": "used_chip",
        "Weekend": "is_weekend",
    }
    rows = []
    for label, col in flags.items():
        for val, name in [(1, "Yes"), (0, "No")]:
            sub = f[f[col] == val]
            if len(sub):
                rows.append({"Signal": label, "Flag": name, "fraud_rate": sub["is_fraud"].mean(), "n": len(sub)})
    sig = pd.DataFrame(rows)
    fig = px.bar(sig, x="fraud_rate", y="Signal", color="Flag", orientation="h", barmode="group",
                 custom_data=["n"], color_discrete_map={"Yes": ORANGE, "No": BLUE},
                 category_orders={"Flag": ["Yes", "No"]})
    fig.update_traces(marker_cornerradius=4,
                      hovertemplate="%{y}: %{fullData.name}<br>Fraud rate: %{x:.2%}<br>Transactions: %{customdata[0]:,}<extra></extra>")
    fig.update_xaxes(tickformat=".1%")
    fig.update_layout(legend=dict(orientation="h", y=1.08, x=0, title=None))
    st.plotly_chart(style(fig, height=380), width="stretch", theme=None)

# ---------------- Tab 5: Flagged transactions ----------------
with tab5:
    cols = ["transaction_id", "transaction_datetime", "transaction_amount", "merchant_category",
            "merchant_country", "transaction_channel", "fraud_type", "fraud_amount_lost"]
    table = fraud[cols].sort_values("fraud_amount_lost", ascending=False)
    st.write(f"**{len(table):,}** fraud transactions in the current filter, largest losses first.")
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "transaction_datetime": st.column_config.DatetimeColumn("Time", format="YYYY-MM-DD HH:mm"),
            "transaction_amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "fraud_amount_lost": st.column_config.NumberColumn("Lost", format="$%.2f"),
        },
    )
    st.download_button("Download as CSV", table.to_csv(index=False), "flagged_transactions.csv", "text/csv")