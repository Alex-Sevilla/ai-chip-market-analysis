"""
Corre este script UNA VEZ para crear stocks.db desde el CSV.
Requisito: Python 3 (no necesita instalar nada extra)

Uso:
    python create_db.py
"""

import sqlite3
import csv
import os

CSV_FILE = "stock_data_2022_2026.csv"
DB_FILE  = "stocks.db"

# Verificar que el CSV existe
if not os.path.exists(CSV_FILE):
    print(f"No encontré '{CSV_FILE}'. Asegúrate de que esté en la misma carpeta.")
    exit(1)

# Crear base de datos
conn = sqlite3.connect(DB_FILE)
cur  = conn.cursor()

# Crear tabla
cur.execute("DROP TABLE IF EXISTS stock_prices")
cur.execute("""
    CREATE TABLE stock_prices (
        date    TEXT,
        ticker  TEXT,
        open    REAL,
        close   REAL,
        average REAL
    )
""")

# Cargar datos del CSV
with open(CSV_FILE, newline="") as f:
    reader = csv.DictReader(f)
    rows = [
        (r["Date"], r["Ticker"], float(r["Open"]), float(r["Close"]), float(r["Average"]))
        for r in reader
    ]

cur.executemany("INSERT INTO stock_prices VALUES (?, ?, ?, ?, ?)", rows)
conn.commit()
conn.close()

print(f" Base de datos creada: {DB_FILE}")
print(f"   Filas cargadas: {len(rows)}")
print(f"   Tickers: NVDA, AMD, INTC, TSM")
print(f"   Período: 2022-01-03 → 2025-12-31")
print()
print("Próximo paso en VS Code:")
print("  1. Instala la extensión 'SQLTools' + 'SQLTools SQLite Driver'")
print("  2. Conecta a este archivo stocks.db")
print("  3. Abre stock_analysis.sql y corre las queries")