import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="127.0.0.1",          # endereço do servidor MySQL
        user="root",        # usuário do banco
        password="",      # senha do banco
        database="app_biblioteca_banco"  # nome do banco de dados
    )
