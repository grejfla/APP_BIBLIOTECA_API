import sqlite3

def conectar():
    return sqlite3.connect("./BancoDados/CampeonatoBrasileiro2026DB.db")  # banco no mesmo diretório