from flask import  Blueprint, jsonify, request, abort

from conectar.funcaoConectar import conectar


TabelaSerie_A_bp = Blueprint('TabelaSerieA', __name__)


#ROTAS PARA A TABELA SERIE A
##ROTA GET
##############################################
@TabelaSerie_A_bp.route("/TabelaSerieA", methods=["GET"])
def listar_Cadastros():
    conn = conectar()
    #conn.execute("PRAGMA foreign_keys = ON") #ativa as chaves estrangeiras das tabelas (pois, não é ativado por padrão)
    cursor = conn.cursor()
    cursor.execute("SELECT idSerieA, NomeClube, PontosClube, JogosClube, SaldoGols, VitoriaClube, DerrotasClube, EmpatesClube, PosicaoTabela FROM TabelaSerieA")
    dados = [
        {"idSerieA": row[0], "NomeClube": row[1], "PontosClube": row[2], "JogosClube": row[3], "SaldoGols": row [4], "VitoriaClube": row [5], "DerrotasClube": row [6], "EmpatesClube": row [7], "PosicaoTabela": row [8] }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(dados)

##ROTA INSERT
#############################################
@TabelaSerie_A_bp.route("/TabelaSerieA", methods=["POST"])
def criar_usuario():
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Validação de campos obrigatórios
    campos_obrigatorios = {"NomeClube", "PontosClube", "JogosClube", "SaldoGols", "VitoriaClube","DerrotasClube", "EmpatesClube", "PosicaoTabela"}
    if not campos_obrigatorios.issubset(dados.keys()):
        abort(400, description=f"Campos obrigatórios: {', '.join(campos_obrigatorios)}")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO TabelaSerieA (NomeClube, PontosClube, JogosClube, SaldoGols, VitoriaClube, DerrotasClube, EmpatesClube, PosicaoTabela)"
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (dados["NomeClube"], dados["PontosClube"], dados["JogosClube"], dados["SaldoGols"], dados["VitoriaClube"], dados["DerrotasClube"], dados["EmpatesClube"], dados["PosicaoTabela"])
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    # 201 Created + Location do recurso recém‑criado
    resposta = jsonify({"idSerieA": novo_id, **dados})
    resposta.status_code = 201
    resposta.headers["Location"] = f"/TabelaSerieA/{novo_id}"
    return resposta

##ROTA UPDATE
#############################################
@TabelaSerie_A_bp.route("/TabelaSerieA/<int:idSerieA>", methods=["PUT", "PATCH"])
def atualizar_usuario(idSerieA):
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Para PUT, garanta que todos os campos estejam presentes
    if request.method == "PUT":
        campos_esperados = {"NomeClube", "PontosClube", "JogosClube", "SaldoGols", "VitoriaClube", "DerrotasClube", "EmpatesClube","PosicaoTabela"}
        if not campos_esperados.issubset(dados.keys()):
            abort(400, description=f"PUT requer todos os campos: {', '.join(campos_esperados)}")

    # Monta dinamicamente o SQL somente com os campos enviados
    campos_validos = {"NomeClube", "PontosClube", "JogosClube", "SaldoGols", "VitoriaClube", "DerrotasClube", "EmpatesClube", "PosicaoTabela"}
    set_clauses = []
    valores = []
    for campo in campos_validos & dados.keys():
        set_clauses.append(f"{campo} = ?")
        valores.append(dados[campo])

    if not set_clauses:
        abort(400, description="Nenhum campo válido para atualizar")

    valores.append(idSerieA)  # último parâmetro é o WHERE

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE TabelaSerieA SET {', '.join(set_clauses)} WHERE idSerieA = ?",
        tuple(valores)
    )
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        abort(404, description="Clube não encontrado")

    conn.close()
    # 204 = No Content, mas você pode devolver 200 com o JSON atualizado se preferir
    return ("", 204)


##ROTA DELETE
#############################################
@TabelaSerie_A_bp.route("/TabelaSerieA/<int:idSerieA>", methods=["DELETE"])
def deletarTabelaSerieA(idSerieA):
    conn = conectar()
    cursor = conn.cursor()

    # tenta apagar o registro informado
    cursor.execute("DELETE FROM TabelaSerieA WHERE idSerieA = ?", (idSerieA,))
    conn.commit()

    # cursor.rowcount informa quantas linhas foram afetadas
    if cursor.rowcount == 0:
        conn.close()
        # nenhum registro com esse ID → devolve 404
        abort(404, description="Clube não encontrado")

    conn.close()
    # 204 = No Content (padrão para deleções bem‑sucedidas)
    return ("", 204)