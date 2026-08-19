from flask import Blueprint, jsonify,request,abort

from conectar.funcaoConectar import conectar

emprestimos = Blueprint('emprestimos', __name__)


#ROTAS PARA A TABELA SERIE B
##ROTA GET
##############################################
@emprestimos.route("/emprestimos", methods=["GET"])
def listar_CadastrosB():
    conn = conectar()
    #conn.execute("PRAGMA foreign_keys = ON") #ativa as chaves estrangeiras das tabelas (pois, não é ativado por padrão)
    cursor = conn.cursor()
    cursor.execute("SELECT idEmprestimo, DataEmprestimo, PrevisaoDevolucao FROM emprestimos")
    dados = [
        {"idEmprestimo": row[0], "DataEmprestimo": row[1], "PrevisaoDevolucao": row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(dados)

##ROTA INSERT
#############################################

@emprestimos.route("/emprestimos", methods=["POST"])
def criar_usuarioB():
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Validação de campos obrigatórios
    campos_obrigatorios = {"DataEmprestimo", "PrevisaoDevolucao"}
    if not campos_obrigatorios.issubset(dados.keys()):
        abort(400, description=f"Campos obrigatórios: {', '.join(campos_obrigatorios)}")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emprestimos (DataEmprestimo, PrevisaoDevolucao)"
        "VALUES (%s, %s)",
        (dados["DataEmprestimo"], dados["PrevisaoDevolucao"])
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    # 201 Created + Location do recurso recém‑criado
    resposta = jsonify({"emprestimos": novo_id, **dados})
    resposta.status_code = 201
    resposta.headers["Location"] = f"/emprestimos/{novo_id}"
    return resposta

##ROTA UPDATE
#############################################
@emprestimos.route("/emprestimos/<int:idEmprestimo>", methods=["PUT", "PATCH"])
def atualizar_usuarioB(idEmprestimo):
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Para PUT, garanta que todos os campos estejam presentes
    if request.method == "PUT":
        campos_esperados = {"DataEmprestimo", "PrevisaoDevolucao"}
        if not campos_esperados.issubset(dados.keys()):
            abort(400, description=f"PUT requer todos os campos: {', '.join(campos_esperados)}")

    # Monta dinamicamente o SQL somente com os campos enviados
    campos_validos = {"DataEmprestimo", "PrevisaoDevolucao"}
    set_clauses = []
    valores = []
    for campo in campos_validos & dados.keys():
        set_clauses.append(f"{campo} = %s")
        valores.append(dados[campo])

    if not set_clauses:
        abort(400, description="Nenhum campo válido para atualizar")

    valores.append(idEmprestimo)  # último parâmetro é o WHERE

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE emprestimos SET {', '.join(set_clauses)} WHERE idEmprestimo = %s",
        tuple(valores)
    )
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        abort(404, description="usuário não encontrado")

    conn.close()
    # 204 = No Content, mas você pode devolver 200 com o JSON atualizado se preferir
    return ("", 204)


##ROTA DELETE
#############################################
@emprestimos.route("/emprestimos/<int:idEmprestimo>", methods=["DELETE"])
def deletaremprestimos(idEmprestimo):
    conn = conectar()
    cursor = conn.cursor()

    # tenta apagar o registro informado
    cursor.execute("DELETE FROM emprestimos WHERE idEmprestimo = %s", (idEmprestimo,))
    conn.commit()

    # cursor.rowcount informa quantas linhas foram afetadas
    if cursor.rowcount == 0:
        conn.close()
        # nenhum registro com esse ID → devolve 404
        abort(404, description="usuário não encontrado")

    conn.close()
    # 204 = No Content (padrão para deleções bem‑sucedidas)
    return ("", 204)