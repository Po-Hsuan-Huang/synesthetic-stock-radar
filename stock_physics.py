"""
Stock Physics Engine
Maps financial metrics to physical properties for synesthetic visualization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import math


def normalize(value: float, min_val: float, max_val: float, target_min: float = 0, target_max: float = 1) -> float:
    """Normalize value from one range to another"""
    if max_val == min_val:
        return target_min
    normalized = (value - min_val) / (max_val - min_val)
    return target_min + normalized * (target_max - target_min)


def get_stock_color(change_pct: float, rule_of_40: float = 0) -> str:
    """
    Map stock performance to intuitive color
    
    Blue (falling) → White (neutral) → Yellow → Orange → Red (rising)
    Saturation increases with Rule of 40 score
    """
    # Base hue from price change
    if change_pct >= 3:
        hue = 0  # Red for strong gains
    elif change_pct >= 1:
        hue = 30  # Orange for moderate gains
    elif change_pct >= 0:
        hue = 50  # Yellow for small gains
    elif change_pct >= -1:
        hue = 180  # Cyan for small losses
    elif change_pct >= -3:
        hue = 200  # Light blue for moderate losses
    else:
        hue = 220  # Deep blue for strong losses
    
    # Saturation from Rule of 40 (higher score = more vivid)
    saturation = min(100, max(40, 50 + abs(rule_of_40) / 2))
    
    # Lightness - make it visible on dark background
    lightness = 60
    
    return f"hsl({hue}, {saturation}%, {lightness}%)"


def get_glow_intensity(rule_of_40: float) -> float:
    """
    Calculate glow intensity based on Rule of 40 score
    Higher score = brighter glow (better value)
    """
    # Normalize to 0-1 range, where 40+ is considered good
    if rule_of_40 >= 80:
        return 1.0  # Maximum glow
    elif rule_of_40 >= 40:
        return 0.5 + (rule_of_40 - 40) / 80  # 0.5 to 1.0
    elif rule_of_40 >= 0:
        return 0.2 + (rule_of_40 / 40) * 0.3  # 0.2 to 0.5
    else:
        return 0.1  # Minimal glow for negative scores


def get_bubble_size(market_cap: float, all_market_caps: List[float]) -> float:
    """
    Calculate bubble size from market cap
    Uses logarithmic scale to handle wide range of market caps
    """
    if market_cap <= 0:
        return 5
    
    # Use log scale for better visualization
    log_cap = math.log10(market_cap + 1)
    min_log = math.log10(min(all_market_caps) + 1) if all_market_caps else log_cap
    max_log = math.log10(max(all_market_caps) + 1) if all_market_caps else log_cap
    
    # Map to size range: 10 to 60 pixels
    size = normalize(log_cap, min_log, max_log, 10, 60)
    return size


def get_pulse_speed(volume: float, all_volumes: List[float]) -> float:
    """
    Calculate pulse animation speed based on trading volume
    Higher volume = faster pulse
    """
    if not all_volumes or volume <= 0:
        return 1.0
    
    # Normalize volume to 0.5 - 3.0 range (animation speed multiplier)
    normalized = normalize(volume, min(all_volumes), max(all_volumes), 0.5, 3.0)
    return normalized


def get_opacity(debt_to_equity: float) -> float:
    """
    Calculate opacity based on debt levels
    Higher debt = more transparent (ghostly)
    """
    if debt_to_equity <= 0:
        return 1.0  # Fully opaque
    elif debt_to_equity <= 50:
        return 1.0  # Healthy debt
    elif debt_to_equity <= 150:
        return 0.9 - (debt_to_equity - 50) / 100 * 0.3  # 0.9 to 0.6
    else:
        return max(0.4, 0.6 - (debt_to_equity - 150) / 200 * 0.2)  # 0.6 to 0.4


def get_velocity_vector(revenue_growth: float, momentum: float) -> Tuple[float, float]:
    """
    Calculate velocity vector based on growth and momentum
    Returns (vx, vy) for animation
    """
    # Revenue growth determines speed
    speed = abs(revenue_growth) / 20  # Scale down for reasonable movement
    
    # Positive growth = upward/rightward, negative = downward/leftward
    angle = 45 if revenue_growth >= 0 else -135  # degrees
    angle_rad = math.radians(angle)
    
    vx = speed * math.cos(angle_rad)
    vy = speed * math.sin(angle_rad)
    
    # Add momentum component
    vy += momentum / 100
    
    return (vx, vy)


def get_elasticity(volatility: float) -> float:
    """
    Calculate bounce/elasticity from volatility
    Higher volatility = more bouncy
    """
    # Normalize to 0.3 - 1.0 range
    if volatility <= 0:
        return 0.5
    
    elasticity = min(1.0, 0.3 + volatility / 100)
    return elasticity


def calculate_bubble_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all visual properties for stock bubbles
    
    Adds columns:
    - color: HSL color string
    - size: Bubble size in pixels
    - glow: Glow intensity (0-1)
    - opacity: Transparency (0-1)
    - pulse_speed: Animation speed multiplier
    - vx, vy: Velocity vector
    - elasticity: Bounce factor
    """
    df = df.copy()
    
    # Extract lists for normalization
    all_caps = df['market_cap'].tolist()
    all_volumes = df['volume'].tolist()
    
    # Calculate properties for each stock
    df['color'] = df.apply(lambda row: get_stock_color(row['change_pct'], row['rule_of_40']), axis=1)
    df['size'] = df['market_cap'].apply(lambda x: get_bubble_size(x, all_caps))
    df['glow'] = df['rule_of_40'].apply(get_glow_intensity)
    df['opacity'] = df['debt_to_equity'].apply(get_opacity)
    df['pulse_speed'] = df['volume'].apply(lambda x: get_pulse_speed(x, all_volumes))
    df['elasticity'] = df['volatility'].apply(get_elasticity)
    
    # Calculate velocity vectors
    velocities = df.apply(lambda row: get_velocity_vector(row['revenue_growth'], row['month_change']), axis=1)
    df['vx'] = velocities.apply(lambda v: v[0])
    df['vy'] = velocities.apply(lambda v: v[1])
    
    return df


def initialize_positions(df: pd.DataFrame, width: float = 100, height: float = 100) -> pd.DataFrame:
    """
    Initialize random positions for stocks within bounds
    Adds columns: x, y
    """
    df = df.copy()
    
    # Random positions with margin
    margin = 10
    df['x'] = np.random.uniform(margin, width - margin, len(df))
    df['y'] = np.random.uniform(margin, height - margin, len(df))
    
    return df


def apply_attraction(df: pd.DataFrame, mode: str = 'value', strength: float = 0.1) -> pd.DataFrame:
    """
    Apply attraction forces to cluster stocks
    
    Modes:
    - 'value': High Rule of 40 stocks attract others
    - 'growth': High revenue growth stocks attract
    - 'profit': High margin stocks attract
    - 'size': Large market cap stocks attract
    """
    df = df.copy()
    
    if mode == 'value':
        weights = df['rule_of_40']
    elif mode == 'growth':
        weights = df['revenue_growth']
    elif mode == 'profit':
        weights = df['operating_margin']
    elif mode == 'size':
        weights = df['market_cap']
    else:
        return df
    
    # Normalize weights
    weights = (weights - weights.min()) / (weights.max() - weights.min() + 0.001)
    
    # Calculate center of mass for high-value stocks
    high_value_mask = weights > 0.7
    if high_value_mask.sum() > 0:
        center_x = (df.loc[high_value_mask, 'x'] * weights[high_value_mask]).sum() / weights[high_value_mask].sum()
        center_y = (df.loc[high_value_mask, 'y'] * weights[high_value_mask]).sum() / weights[high_value_mask].sum()
        
        # Pull stocks toward center
        df['vx'] += (center_x - df['x']) * strength * (1 - weights)
        df['vy'] += (center_y - df['y']) * strength * (1 - weights)
    
    return df


def update_positions(df: pd.DataFrame, time_delta: float = 0.1, bounds: Tuple[float, float, float, float] = (0, 100, 0, 100)) -> pd.DataFrame:
    """
    Update positions based on velocity
    Apply boundary conditions
    
    Args:
        df: DataFrame with x, y, vx, vy columns
        time_delta: Time step for physics simulation
        bounds: (x_min, x_max, y_min, y_max)
    """
    df = df.copy()
    
    # Update positions
    df['x'] += df['vx'] * time_delta
    df['y'] += df['vy'] * time_delta
    
    # Bounce off boundaries
    x_min, x_max, y_min, y_max = bounds
    
    # X bounds
    df.loc[df['x'] < x_min, 'vx'] *= -df.loc[df['x'] < x_min, 'elasticity']
    df.loc[df['x'] < x_min, 'x'] = x_min
    df.loc[df['x'] > x_max, 'vx'] *= -df.loc[df['x'] > x_max, 'elasticity']
    df.loc[df['x'] > x_max, 'x'] = x_max
    
    # Y bounds
    df.loc[df['y'] < y_min, 'vy'] *= -df.loc[df['y'] < y_min, 'elasticity']
    df.loc[df['y'] < y_min, 'y'] = y_min
    df.loc[df['y'] > y_max, 'vy'] *= -df.loc[df['y'] > y_max, 'elasticity']
    df.loc[df['y'] > y_max, 'y'] = y_max
    
    # Apply slight damping to prevent infinite bouncing
    df['vx'] *= 0.98
    df['vy'] *= 0.98
    
    return df


if __name__ == "__main__":
    # Test the physics engine
    print("Testing Physics Engine...")
    
    # Create sample data
    test_data = pd.DataFrame({
        'ticker': ['AAPL', 'TSLA', 'NVDA'],
        'change_pct': [2.5, -3.2, 5.1],
        'rule_of_40': [65, 25, 90],
        'market_cap': [3e12, 8e11, 2.5e12],
        'volume': [50000000, 120000000, 30000000],
        'debt_to_equity': [20, 150, 30],
        'volatility': [25, 65, 40],
        'revenue_growth': [8, 45, 60],
        'month_change': [5, -10, 15],
        'operating_margin': [30, -5, 55]
    })
    
    # Calculate properties
    result = calculate_bubble_properties(test_data)
    print("\n📊 Bubble Properties:")
    print(result[['ticker', 'color', 'size', 'glow', 'opacity', 'pulse_speed']])
    
    # Initialize positions
    result = initialize_positions(result)
    print("\n📍 Initial Positions:")
    print(result[['ticker', 'x', 'y', 'vx', 'vy']])
