import os
import asyncio
import numpy as np
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime, timedelta
import pandas as pd
from trading.wallet import WalletManager
from trading.trader import YeMemeTrader
from functools import partial
import nest_asyncio

# Abilita il nesting di event loops
nest_asyncio.apply()

# Crea un nuovo event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("🎵 Ye Meme Trader Dashboard 🚀", className="text-center mb-4"), width=12)
    ]),
    
    dbc.Row([
        # Wallet Status Card
        dbc.Col(dbc.Card([
            dbc.CardHeader("💰 Wallet Status"),
            dbc.CardBody([
                html.H4(id="wallet-balance", className="card-title"),
                html.P(id="wallet-address", className="card-text")
            ])
        ]), width=4),
        
        # Active Trades Card
        dbc.Col(dbc.Card([
            dbc.CardHeader("🔄 Active Trades"),
            dbc.CardBody([
                html.H4(id="active-trades-count", className="card-title"),
                html.Div(id="active-trades-list")
            ])
        ]), width=4),
        
        # Performance Card
        dbc.Col(dbc.Card([
            dbc.CardHeader("📈 Performance"),
            dbc.CardBody([
                html.H4(id="total-profit", className="card-title"),
                html.P(id="win-rate", className="card-text")
            ])
        ]), width=4)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Trading Chart"),
                dbc.CardBody([
                    dcc.Graph(id='trading-chart'),
                    dcc.Interval(
                        id='chart-update',
                        interval=30000,  # 30 seconds
                        n_intervals=0
                    )
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎯 Recent Opportunities"),
                dbc.CardBody(id="opportunities-list")
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📝 Trading Log"),
                dbc.CardBody([
                    html.Div(id="trading-log", style={'maxHeight': '300px', 'overflow': 'auto'})
                ])
            ])
        ], width=6)
    ])
], fluid=True, className="p-4")

# Cache per i dati del wallet
wallet_cache = {
    'balance': 0.0,
    'address': os.getenv('WALLET_ADDRESS', '')[:8] + '...',
    'last_update': None
}

async def fetch_wallet_data():
    """Fetch wallet data asynchronously"""
    try:
        wallet_manager = WalletManager()
        balance = await wallet_manager.get_balance()
        address = os.getenv('WALLET_ADDRESS')
        wallet_cache.update({
            'balance': balance,
            'address': f"{address[:8]}...{address[-6:]}",
            'last_update': datetime.now()
        })
    except Exception as e:
        print(f"Error fetching wallet data: {e}")

# Callbacks
@app.callback(
    [Output("wallet-balance", "children"),
     Output("wallet-address", "children")],
    Input("chart-update", "n_intervals")
)
def update_wallet_info(n):
    """Update wallet information using cached data"""
    # Aggiorna i dati in background
    asyncio.run_coroutine_threadsafe(fetch_wallet_data(), loop)
    
    # Usa i dati dalla cache
    return f"${wallet_cache['balance']:.2f}", f"Wallet: {wallet_cache['address']}"

@app.callback(
    Output("trading-chart", "figure"),
    Input("chart-update", "n_intervals")
)
def update_chart(n):
    # Sample data - replace with real trading data
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
    values = pd.Series(range(len(dates))) + np.random.randn(len(dates)) * 5
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#00ff00', width=2)
    ))
    
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=None,
        yaxis_title='Value (USD)',
        showlegend=False
    )
    
    return fig

def start_dashboard():
    """Start the dashboard server"""
    app.run_server(debug=True, port=8050)
