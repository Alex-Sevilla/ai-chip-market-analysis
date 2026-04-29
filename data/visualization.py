"""
Stock Analysis — Visualizations
Genera 4 gráficas y las guarda como imágenes PNG.

Requisitos:
    pip install matplotlib seaborn

Uso:
    python visualizations.py

Output:
    chart1_annual_returns.png
    chart2_investment_sim.png
    chart3_nvda_moving_avg.png
    chart4_correlation.png
"""

import csv
import sqlite3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from collections import defaultdict

matplotlib.use('Agg')

# ── Configuración visual ─────────────────────────────────────────────────────
COLORS = {'NVDA': '#76b900', 'AMD': '#ED1C24', 'INTC': '#0071C5', 'TSM': '#00BFFF'}
BG, CARD, TEXT, GRID = '#0f0f0f', '#1a1a1a', '#e8e8e8', '#2a2a2a'

plt.rcParams.update({
    'figure.facecolor': BG, 'axes.facecolor': CARD,
    'axes.edgecolor': GRID, 'axes.labelcolor': TEXT,
    'xtick.color': TEXT, 'ytick.color': TEXT,
    'text.color': TEXT, 'grid.color': GRID,
    'font.family': 'monospace', 'axes.grid': True,
    'grid.linewidth': 0.5, 'axes.spines.top': False,
    'axes.spines.right': False,
})

# ── Carga de datos ────────────────────────────────────────────────────────────
rows = []
with open('stock_data_2022_2026.csv') as f:
    for r in csv.DictReader(f):
        rows.append(r)

def annual_return(rows, ticker):
    filtered = [r for r in rows if r['Ticker'] == ticker]
    by_year = defaultdict(list)
    for r in filtered:
        by_year[r['Date'][:4]].append(r)
    result = {}
    for yr, rs in sorted(by_year.items()):
        rs = sorted(rs, key=lambda x: x['Date'])
        open_p  = float(rs[0]['Close'])
        close_p = float(rs[-1]['Close'])
        result[yr] = round((close_p - open_p) / open_p * 100, 2)
    return result

def moving_avg(data, window):
    result = [None] * (window - 1)
    for i in range(window - 1, len(data)):
        result.append(sum(data[i - window + 1:i + 1]) / window)
    return result

# ── Chart 1: Retorno anual por ticker ────────────────────────────────────────
tickers = ['NVDA', 'AMD', 'INTC', 'TSM']
years   = ['2022', '2023', '2024', '2025']
returns = {t: annual_return(rows, t) for t in tickers}

fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG)
ax.set_facecolor(CARD)
x, width = np.arange(len(years)), 0.2

for i, ticker in enumerate(tickers):
    vals = [returns[ticker].get(yr, 0) for yr in years]
    bars = ax.bar(x + i * width, vals, width, label=ticker,
                  color=COLORS[ticker], alpha=0.9, zorder=3)
    for bar, val in zip(bars, vals):
        ypos = bar.get_height() + 3 if val >= 0 else bar.get_height() - 12
        ax.text(bar.get_x() + bar.get_width() / 2, ypos, f'{val:+.0f}%',
                ha='center', va='bottom', fontsize=7.5,
                color=COLORS[ticker], fontweight='bold')

ax.axhline(0, color=TEXT, linewidth=0.8, linestyle='--', alpha=0.4)
ax.set_xticks(x + width * 1.5)
ax.set_xticklabels(years, fontsize=11)
ax.set_ylabel('Annual Return (%)', fontsize=10)
ax.set_title('Annual Return by Ticker (2022–2025)', fontsize=14, fontweight='bold', pad=15)
ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:+.0f}%'))
plt.tight_layout()
plt.savefig('../images/chart1_annual_returns.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
# print(" chart1_annual_returns.png")

# ── Chart 2: Simulación $1,000 invertidos ────────────────────────────────────
sim = {'NVDA': 6191.9, 'TSM': 2359.39, 'AMD': 1425.45, 'INTC': 693.48}
sorted_sim  = sorted(sim.items(), key=lambda x: x[1], reverse=True)
labels      = [s[0] for s in sorted_sim]
values      = [s[1] for s in sorted_sim]

fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
ax.set_facecolor(CARD)
bars = ax.barh(labels, values, color=[COLORS[t] for t in labels],
               alpha=0.9, height=0.5, zorder=3)
ax.axvline(1000, color='white', linewidth=1.2, linestyle='--', alpha=0.5, label='Initial $1,000')

for bar, val in zip(bars, values):
    ret  = (val - 1000) / 1000 * 100
    sign = '+' if ret >= 0 else ''
    ax.text(val + 80, bar.get_y() + bar.get_height() / 2,
            f'${val:,.0f}  ({sign}{ret:.0f}%)',
            va='center', fontsize=10, fontweight='bold',
            color=bar.get_facecolor())

ax.set_xlim(0, 7500)
ax.set_xlabel('Final Value (USD)', fontsize=10)
ax.set_title('$1,000 Invested per Ticker — Jan 2022 → Dec 2025', fontsize=13, fontweight='bold', pad=15)
ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'${v:,.0f}'))
plt.tight_layout()
plt.savefig('../images/chart2_investment_sim.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
# print(" chart2_investment_sim.png")

# ── Chart 3: NVDA precio + MA30 + MA90 ───────────────────────────────────────
nvda   = sorted([r for r in rows if r['Ticker'] == 'NVDA'], key=lambda x: x['Date'])
dates  = [r['Date'] for r in nvda]
closes = [float(r['Close']) for r in nvda]
ma30   = moving_avg(closes, 30)
ma90   = moving_avg(closes, 90)

start        = 90
dates_plot   = dates[start:]
closes_plot  = closes[start:]
ma30_plot    = ma30[start:]
ma90_plot    = ma90[start:]
x_idx        = list(range(len(dates_plot)))

tick_positions, tick_labels = [], []
for year in ['2022', '2023', '2024', '2025']:
    for i, d in enumerate(dates_plot):
        if year + '-01' <= d < year + '-02':
            tick_positions.append(i)
            tick_labels.append(year)
            break

fig, ax = plt.subplots(figsize=(14, 6), facecolor=BG)
ax.set_facecolor(CARD)
ax.plot(x_idx, closes_plot, color=COLORS['NVDA'], linewidth=1.2, alpha=0.9, label='NVDA Close', zorder=3)
ax.plot(x_idx, ma30_plot,   color='#FFD700',      linewidth=1.5, linestyle='--', label='MA 30d', zorder=4)
ax.plot(x_idx, ma90_plot,   color='#FF6B6B',      linewidth=1.5, linestyle='--', label='MA 90d', zorder=4)

# Anotar golden cross
for i in range(1, len(dates_plot)):
    if (ma30_plot[i] and ma90_plot[i] and ma30_plot[i-1] and ma90_plot[i-1]
            and ma30_plot[i] > ma90_plot[i] and ma30_plot[i-1] <= ma90_plot[i-1]
            and dates_plot[i] >= '2023-01-01'):
        ax.annotate('Golden Cross\n(Feb 2023)', xy=(i, closes_plot[i]),
                    xytext=(i + 30, closes_plot[i] + 20),
                    arrowprops=dict(arrowstyle='->', color='white', lw=1.2),
                    fontsize=8.5, color='white',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#333',
                              edgecolor='white', alpha=0.8))
        break

ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, fontsize=10)
ax.set_ylabel('Price (USD)', fontsize=10)
ax.set_title('NVDA — Price vs Moving Averages (MA30 & MA90)', fontsize=13, fontweight='bold', pad=15)
ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'${v:.0f}'))
plt.tight_layout()
plt.savefig('../images/chart3_nvda_moving_avg.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
# print(" chart3_nvda_moving_avg.png")

# ── Chart 4: Correlación NVDA vs AMD por año ─────────────────────────────────
corr_data = {'2022': 0.8873, '2023': 0.6694, '2024': 0.5786, '2025': 0.5948}
yrs  = list(corr_data.keys())
vals = list(corr_data.values())

fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG)
ax.set_facecolor(CARD)
bar_cols = ['#e05c5c' if v > 0.8 else '#f0a500' if v > 0.65 else '#76b900' for v in vals]
bars = ax.bar(yrs, vals, color=bar_cols, alpha=0.9, width=0.5, zorder=3)

for bar, val in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.01,
            f'{val:.4f}', ha='center', va='bottom',
            fontsize=11, fontweight='bold', color=bar.get_facecolor())

ax.set_ylim(0, 1.1)
ax.axhline(0.8, color='#e05c5c', linewidth=1, linestyle=':', alpha=0.6, label='High correlation (0.8)')
ax.axhline(0.6, color='#f0a500', linewidth=1, linestyle=':', alpha=0.6, label='Moderate (0.6)')
ax.set_ylabel('Pearson Correlation', fontsize=10)
ax.set_title('NVDA vs AMD — Daily Return Correlation by Year', fontsize=13, fontweight='bold', pad=15)
ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)
plt.tight_layout()
plt.savefig('../images/chart4_correlation.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
# print(" chart4_correlation.png")

# print("\n🎉 Todas las imágenes generadas correctamente.")