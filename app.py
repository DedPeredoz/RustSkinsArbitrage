import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Rust Skin Arbitrage", layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    conn = sqlite3.connect('skins.db')
    df = pd.read_sql("""
        SELECT name, source, deposit_price, withdraw_price, have, max, 
               datetime(last_updated, 'localtime') as last_updated 
        FROM skins
        UNION ALL
        SELECT name, 'rustypot' as source, price as deposit_price, price as withdraw_price, 
               1 as have, 100 as max, datetime(last_updated, 'localtime') as last_updated
        FROM rustypot_items
    """, conn)
    conn.close()
    return df

def prepare_data(df):
    df_deposit = df[['name', 'source', 'deposit_price', 'have', 'max', 'last_updated']].copy()
    df_deposit['price_type'] = 'Deposit'
    df_deposit.rename(columns={'deposit_price': 'price'}, inplace=True)
    
    df_withdraw = df[['name', 'source', 'withdraw_price', 'have', 'max', 'last_updated']].copy()
    df_withdraw['price_type'] = 'Withdraw'
    df_withdraw.rename(columns={'withdraw_price': 'price'}, inplace=True)
    
    return pd.concat([df_deposit, df_withdraw])

def calculate_stock_status(row, source):
    if source == 'rustypot':
        return 'OK'  # RustyPot всегда в наличии
    
    have = row[f'have_{source}']
    max_qty = row[f'max_{source}']
    if have > max_qty: return 'OVRS'
    elif have == 0: return 'ZERO'
    return 'OK'

def main():
    st.title("🛒 Табличка для арбитража")
    df = load_data()
    
    if df.empty:
        st.warning("No data available. Please run the updater first.")
        return
    
    df_long = prepare_data(df)
    sources = sorted(df_long['source'].unique())
    price_types = ['Deposit', 'Withdraw']
    
    with st.sidebar:
        st.header("⚙️ Настройки")
        col1, col2 = st.columns(2)
        with col1:
            source1 = st.selectbox("Откуда", sources, index=0)
            price_type1 = st.selectbox("Dep/With", price_types, index=1)
        with col2:
            source2 = st.selectbox("Куда", sources, index=1 if len(sources) > 1 else 0)
            price_type2 = st.selectbox("Dep/With", price_types, index=0)
        
        min_price, max_price = st.slider(
            "Разброс ($)",
            float(df_long['price'].min()),
            float(df_long['price'].max()),
            (0.0, min(100.0, float(df_long['price'].max()))))
        
        st.subheader("Stock Filters")
        show_ovrs = st.checkbox("Show OVRS (overstock)", value=True)
        show_zero = st.checkbox("Show ZERO (out of stock)", value=True)
    
    df1 = df_long[(df_long['source'] == source1) & (df_long['price_type'] == price_type1)]
    df2 = df_long[(df_long['source'] == source2) & (df_long['price_type'] == price_type2)]
    
    if df1.empty or df2.empty:
        st.warning("No data for selected sources/price types.")
        return
    
    merged_df = pd.merge(df1, df2, on='name', suffixes=(f'_{source1}', f'_{source2}'))
    
    merged_df[f'{source1}_status'] = merged_df.apply(lambda x: calculate_stock_status(x, source1), axis=1)
    merged_df[f'{source2}_status'] = merged_df.apply(lambda x: calculate_stock_status(x, source2), axis=1)
    
    filtered_df = merged_df.copy()
    if not show_ovrs:
        filtered_df = filtered_df[(filtered_df[f'{source1}_status'] != 'OVRS') & (filtered_df[f'{source2}_status'] != 'OVRS')]
    if not show_zero:
        filtered_df = filtered_df[(filtered_df[f'{source1}_status'] != 'ZERO') & (filtered_df[f'{source2}_status'] != 'ZERO')]
    
    filtered_df = filtered_df[
        (filtered_df[f'price_{source1}'] >= min_price) & 
        (filtered_df[f'price_{source1}'] <= max_price)
    ]
    
    filtered_df['Diff ($)'] = filtered_df[f'price_{source1}'] - filtered_df[f'price_{source2}']
    filtered_df['Diff (%)'] = (filtered_df['Diff ($)'] / filtered_df[f'price_{source2}']) * 100
    
    filtered_df[f'{source1} Stock'] = (
        filtered_df[f'have_{source1}'].astype(str) + '/' + 
        filtered_df[f'max_{source1}'].astype(str) + ' ' +
        filtered_df[f'{source1}_status']
    )
    filtered_df[f'{source2} Stock'] = (
        filtered_df[f'have_{source2}'].astype(str) + '/' + 
        filtered_df[f'max_{source2}'].astype(str) + ' ' +
        filtered_df[f'{source2}_status']
    )
    
    result_df = filtered_df[[
        'name',
        f'price_{source1}',
        f'price_{source2}',
        f'{source1} Stock',
        f'{source2} Stock',
        'Diff ($)',
        'Diff (%)',
        f'last_updated_{source1}',
        f'last_updated_{source2}'
    ]].rename(columns={
        f'price_{source1}': f'{source1} Price',
        f'price_{source2}': f'{source2} Price',
        f'last_updated_{source1}': f'{source1} Updated',
        f'last_updated_{source2}': f'{source2} Updated'
    }).sort_values('Diff (%)', ascending=False)
    
    st.header(f"🔍 Comparison: {source1} ({price_type1}) vs {source2} ({price_type2})")
    st.dataframe(
        result_df.style.format({
            f'{source1} Price': '{:.2f}',
            f'{source2} Price': '{:.2f}',
            'Diff ($)': '{:.2f}',
            'Diff (%)': '{:.1f}%'
        }).applymap(lambda x: 'color: green' if x > 0 else 'color: red', 
                  subset=['Diff ($)', 'Diff (%)']),
        height=700,
        use_container_width=True
    )

if __name__ == "__main__":
    main()