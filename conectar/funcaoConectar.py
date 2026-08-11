import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="localhost",          # endereço do servidor MySQL
        user="seu_usuario",        # usuário do banco
        password="sua_senha",      # senha do banco
        database="CampeonatoBrasileiro2026DB"  # nome do banco de dados
    )
