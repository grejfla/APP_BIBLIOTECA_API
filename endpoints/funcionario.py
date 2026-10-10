from flask import Blueprint, jsonify, request, abort

from conectar.funcaoConectar import conectar

funcionario= Blueprint('funcionario', __name__)

#ROTAS PARA A TABELA SERIE C
##ROTA GET
##############################################
@funcionario.route("/funcionario", methods=["GET"])
def listar_CadastrosC():
    conn = conectar()
    #conn.execute("PRAGMA foreign_keys = ON") #ativa as chaves estrangeiras das tabelas (pois, não é ativado por padrão)
    cursor = conn.cursor()
    cursor.execute("SELECT idfuncionario, NomeFuncionario, SenhaFuncionario, RegistroFuncionario, CPF_Funcionario FROM funcionario")
    dados = [
        {"idfuncionario": row[0], "NomeFuncionario": row[1], "SenhaFuncionario": row[2], "RegistroFuncionario": row[3], "CPF_Funcionario": row [4]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(dados)

##ROTA INSERT
#############################################

@funcionario.route("/funcionario", methods=["POST"])
def criar_usuarioC():
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Validação de campos obrigatórios
    campos_obrigatorios = {"NomeFuncionario", "SenhaFuncionario", "RegistroFuncionario", "CPF_Funcionario"}
    if not campos_obrigatorios.issubset(dados.keys()):
        abort(400, description=f"Campos obrigatórios: {', '.join(campos_obrigatorios)}")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO funcionario (NomeFuncionario, SenhaFuncionario , RegistroFuncionario , CPF_Funcionario)"
        "VALUES (%s, %s, %s, %s)",
        (dados["NomeFuncionario"], dados["SenhaFuncionario"], dados["RegistroFuncionario"], dados["CPF_Funcionario"])
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    # 201 Created + Location do recurso recém‑criado
    resposta = jsonify({"idfuncionario": novo_id, **dados})
    resposta.status_code = 201
    resposta.headers["Location"] = f"/funcionario/{novo_id}"
    return resposta

##ROTA UPDATE
#############################################
@funcionario.route("/funcionario/<int:idfuncionario>", methods=["PUT", "PATCH"])
def atualizar_usuarioC(idfuncionario):
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Para PUT, garanta que todos os campos estejam presentes
    if request.method == "PUT":
        campos_esperados = {"NomeFuncionario", "SenhaFuncionario", "RegistroFuncionario", "CPF_Funcionario"}
        if not campos_esperados.issubset(dados.keys()):
            abort(400, description=f"PUT requer todos os campos: {', '.join(campos_esperados)}")

    # Monta dinamicamente o SQL somente com os campos enviados
    campos_validos = {"NomeFuncionario", "SenhaFuncionario", "RegistroFuncionario", "CPF_Funcionario"}
    set_clauses = []
    valores = []
    for campo in campos_validos & dados.keys():
        set_clauses.append(f"{campo} = %s")
        valores.append(dados[campo])

    if not set_clauses:
        abort(400, description="Nenhum campo válido para atualizar")

    valores.append(idfuncionario)  # último parâmetro é o WHERE

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE funcionario SET {', '.join(set_clauses)} WHERE idfuncionario = %s",
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
@funcionario.route("/funcionario/<int:idfuncionario>", methods=["DELETE"])
def deletarfuncionario(idfuncionario):
    conn = conectar()
    cursor = conn.cursor()

    # tenta apagar o registro informado
    cursor.execute("DELETE FROM funcionario WHERE idfuncionario = %s", (idfuncionario,))
    conn.commit()

    # cursor.rowcount informa quantas linhas foram afetadas
    if cursor.rowcount == 0:
        conn.close()
        # nenhum registro com esse ID → devolve 404
        abort(404, description="usuário não encontrado")

    conn.close()
    # 204 = No Content (padrão para deleções bem‑sucedidas)
    return ("", 204)

@funcionario.route("/funcionarios/selecionar", methods=["GET"])
def listar_funcionarios_para_selecao():
    conn = conectar()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT idfuncionario,
                   NomeFuncionario,
                   RegistroFuncionario
            FROM funcionario
        """)

        dados = [
            {
                "idfuncionario": row[0],
                "NomeFuncionario": row[1],
                "RegistroFuncionario": row[2]
            }
            for row in cursor.fetchall()
        ]

        return jsonify(dados), 200

    except Exception as erro:
        return jsonify({"erro": str(erro)}), 500

    finally:
        conn.close()