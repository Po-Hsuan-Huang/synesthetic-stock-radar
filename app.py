import dash
from dash import html, dcc, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from io import StringIO

# Import our custom modules
from stock_api import fetch_market_snapshot
from stock_physics import (
    calculate_bubble_properties,
    initialize_positions,
    apply_attraction,
    update_positions
)

# Create Dash app
app = dash.Dash(__name__)
server = app.server

# Educational content (preserved from original)
def chapter1_content():
    return [
        html.H4("📖 第1章:後稀缺時代的黎明"),
        html.P("導論:經濟新曙光"),
        html.P(
            "數百年來,經濟學的核心問題一直圍繞著「稀缺性」——如何在有限資源與無限需求之間做出選擇。"
        ),
    ]

def chapter2_content():
    return [
        html.H4("📖 第2章:能源・材料・計算——新的三大稀缺"),
        html.P("在後稀缺框架下,限制經濟增長的不再是人力,而是能源、材料與計算三者的耦合瓶頸。"),
    ]

def chapter3_content():
    return [
        html.H4("📖 第3章:分配、所有權與激勵"),
        html.P("當可複製的智能使勞動不再稀缺,經濟的瓶頸轉向能源、材料與計算。"),
    ]

# Visualization functions
def create_physics_radar(df: pd.DataFrame, attraction_mode: str = 'none') -> go.Figure:
    """Create physics-based radar visualization"""
    
    # Build hover text with comprehensive metrics
    hover_texts = []
    for _, row in df.iterrows():
        text = (
            f"<b>{row['ticker']}</b><br>"
            f"Price: ${row['price']:.2f} ({row['change_pct']:+.2f}%)<br>"
            f"<br>"
            f"<b>Rule of 40: {row['rule_of_40']:.1f}</b><br>"
            f"  Op. Margin: {row['operating_margin']:.1f}%<br>"
            f"  Rev. Growth: {row['revenue_growth']:.1f}%<br>"
            f"<br>"
            f"Market Cap: ${row['market_cap']/1e9:.1f}B<br>"
            f"Volume: {row['volume']/1e6:.1f}M<br>"
            f"Volatility: {row['volatility']:.1f}%"
        )
        hover_texts.append(text)
    
    # Create scatter plot with bubble properties
    trace = go.Scatter(
        x=df['x'],
        y=df['y'],
        mode='markers+text',
        text=df['ticker'],
        hovertext=hover_texts,
        hoverinfo='text',
        textposition='top center',
        textfont=dict(size=8, color='rgba(255,255,255,0.8)'),
        marker=dict(
            size=df['size'],
            color=df['color'],
            opacity=df['opacity'],
            line=dict(
                width=df['glow'] * 4,  # Glow effect via border
                color=df['color']
            ),
            sizemode='diameter'
        ),
        showlegend=False
    )
    
    # Space-themed dark layout
    layout = go.Layout(
        paper_bgcolor='#0a0e27',
        plot_bgcolor='#0a0e27',
        xaxis=dict(
            range=[0, 100],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            range=[0, 100],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode='closest',
        height=700,
        # Add concentric zone circles
        shapes=[
            dict(type='circle', xref='x', yref='y',
                 x0=15, y0=15, x1=85, y1=85,
                 line=dict(color='rgba(102,126,234,0.1)', width=1)),
            dict(type='circle', xref='x', yref='y',
                 x0=30, y0=30, x1=70, y1=70,
                 line=dict(color='rgba(102,126,234,0.15)', width=1)),
        ],
        annotations=[
            dict(
                text="🌌 VALUE CORE",
                x=50, y=50,
                showarrow=False,
                font=dict(size=11, color='rgba(102,126,234,0.3)'),
            )
        ]
    )
    
    return go.Figure(data=[trace], layout=layout)


def create_rule40_classic(df: pd.DataFrame) -> go.Figure:
    """Traditional Rule of 40 scatter plot"""
    slope = -41 / 39
    intercept_line = 40
    
    margins = df['operating_margin'].tolist()
    growths = df['revenue_growth'].tolist()
    caps = df['market_cap'].tolist()
    labels = df['ticker'].tolist()
    
    x_line = list(range(-20, int(max(margins)) + 10))
    y_line = [slope * x + intercept_line for x in x_line]
    
    intercepts = [y - slope * x for x, y in zip(margins, growths)]
    hover_texts = [
        f"{label}<br>Margin: {x:.2f}%<br>Growth: {y:.2f}%<br>Market Cap: ${c/1e9:.2f}B<br>Intercept: {b:.2f}"
        for label, x, y, c, b in zip(labels, margins, growths, caps, intercepts)
    ]
    
    scatter = go.Scatter(
        x=margins,
        y=growths,
        mode='markers+text',
        text=labels,
        hovertext=hover_texts,
        hoverinfo='text',
        textposition='top center',
        textfont=dict(size=9, color='white'),
        marker=dict(
            size=[min(60, max(10, c/5e10)) for c in caps],
            color='cyan',
            line=dict(width=1, color='white')
        ),
        name='Companies'
    )
    
    line = go.Scatter(
        x=x_line,
        y=y_line,
        mode='lines',
        name='Rule of 40 Frontier',
        line=dict(color='red', dash='dash', width=2)
    )
    
    layout = go.Layout(
        xaxis=dict(
            title='Adjusted Operating Margin (%)',
            range=[-20, 75],
            gridcolor='#444444',
            tickfont=dict(color='#f0f0f0'),
        ),
        yaxis=dict(
            title='YoY Revenue Growth (%)',
            range=[-20, 145],
            gridcolor='#444444',
            tickfont=dict(color='#f0f0f0'),
        ),
        showlegend=True,
        height=700,
        plot_bgcolor='#1a1a2e',
        paper_bgcolor='#0a0e27',
        font=dict(color='#f0f0f0')
    )
    
    return go.Figure(data=[scatter, line], layout=layout)


# App Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🌌 Synesthetic Stock Radar", 
                style={'margin': '0', 'background': 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                       '-webkit-background-clip': 'text', '-webkit-text-fill-color': 'transparent',
                       'fontSize': '2.5rem', 'fontWeight': '700'}),
        html.P("Experience stocks through AI's sixth sense - where financial data becomes intuitive physics",
               style={'color': '#a0aec0', 'margin': '0.5rem 0'}),
    ], style={'textAlign': 'center', 'padding': '2rem 1rem 1rem'}),
    
    # Simple tab navigation
    dcc.Tabs(id='main-tabs', value='radar', children=[
        dcc.Tab(label='🌌 Radar View', value='radar'),
        dcc.Tab(label='📊 Rule of 40 Classic', value='rule40'),
        dcc.Tab(label='📖 Learn', value='learn'),
    ]),
    
    # Data stores
    dcc.Store(id='stock-data-store'),
    dcc.Store(id='chapter-index', data=0),
    
    # Auto-refresh interval
    dcc.Interval(id='data-refresh', interval=300000, n_intervals=0),
    
    # Tab content
    html.Div(id='tab-content', style={'padding': '1rem'})
    
], style={'backgroundColor': '#0a0e27', 'minHeight': '100vh', 'color': '#f0f0f0'})


# Callbacks
@app.callback(
    Output('stock-data-store', 'data'),
    Input('data-refresh', 'n_intervals')
)
def fetch_data(n):
    """Fetch stock data"""
    df = fetch_market_snapshot(max_stocks=50)
    df = calculate_bubble_properties(df)
    df = initialize_positions(df, width=100, height=100)
    return df.to_json()


@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('stock-data-store', 'data')]
)
def render_content(tab, data_json):
    """Render tab content"""
    
    if tab == 'radar':
        if not data_json:
            return html.Div("Loading...", style={'textAlign': 'center', 'padding': '3rem'})
        
        df = pd.read_json(StringIO(data_json))
        df = apply_attraction(df, mode='value', strength=0.03)
        df = update_positions(df, time_delta=0.3, bounds=(5, 95, 5, 95))
        
        fig = create_physics_radar(df)
        
        return html.Div([
            dcc.Graph(figure=fig, config={'displayModeBar': False}),
            
            # Legend
            html.Div([
                html.H4("🎨 Visual Properties", style={'marginBottom': '1rem'}),
                html.Div([
                    html.Div("🔵 Size = Market Cap | 🎨 Color = Price Change (Blue→Red)", 
                            style={'margin': '0.5rem 0'}),
                    html.Div("✨ Glow = Rule of 40 Score | 🌫️ Opacity = Debt Level",
                            style={'margin': '0.5rem 0'}),
                    html.Div("📍 Position = Attracted to high-value stocks (bright glowing bubbles)",
                            style={'margin': '0.5rem 0', 'fontStyle': 'italic', 'color': '#a0aec0'}),
                ])
            ], style={'backgroundColor': '#1a1a2e', 'padding': '1.5rem', 
                     'borderRadius': '12px', 'marginTop': '1rem'})
        ])
    
    elif tab == 'rule40':
        if not data_json:
            return html.Div("Loading...", style={'textAlign': 'center', 'padding': '3rem'})
        
        df = pd.read_json(StringIO(data_json))
        fig = create_rule40_classic(df)
        
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    elif tab == 'learn':
        return html.Div([
            html.Button("Next Chapter →", id='next-btn', n_clicks=0,
                      style={'padding': '0.75rem 1.5rem', 'marginBottom': '1rem',
                             'borderRadius': '8px', 'border': '1px solid #667eea',
                             'backgroundColor': '#2d3561', 'color': '#f0f0f0',
                             'cursor': 'pointer'}),
            html.Div(id='chapter-content', children=chapter1_content(),
                    style={'backgroundColor': '#1a1a2e', 'padding': '2rem',
                           'borderRadius': '12px', 'maxHeight': '600px', 'overflowY': 'auto'})
        ])


@app.callback(
    [Output('chapter-content', 'children'),
     Output('chapter-index', 'data')],
    Input('next-btn', 'n_clicks'),
    State('chapter-index', 'data'),
    prevent_initial_call=True
)
def next_chapter(n, idx):
    """Cycle chapters"""
    new_idx = (idx + 1) % 3
    if new_idx == 0:
        return chapter1_content(), 0
    elif new_idx == 1:
        return chapter2_content(), 1
    else:
        return chapter3_content(), 2


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
