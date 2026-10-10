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
    cursor.execute("SELECT idEmprestimo, DataEmprestimo, PrevisaoDevolucao, DataDevolucaoReal FROM emprestimos")
    dados = [
        {"idEmprestimo": row[0], "DataEmprestimo": row[1], "PrevisaoDevolucao": row[2], "DataDevolucaoReal": row[3]}
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
    campos_obrigatorios = {"DataEmprestimo", "PrevisaoDevolucao", "DataDevolucaoReal"}
    if not campos_obrigatorios.issubset(dados.keys()):
        abort(400, description=f"Campos obrigatórios: {', '.join(campos_obrigatorios)}")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emprestimos (DataEmprestimo, PrevisaoDevolucao, DataDevolucaoReal)"
        "VALUES (%s, %s, %s)",
        (dados["DataEmprestimo"], dados["PrevisaoDevolucao"], dados["DataDevolucaoReal"])
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    # 201 Created + Location do recurso recém‑criado
    resposta = jsonify({"idEmprestimo": novo_id, **dados})
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
        campos_esperados = {"DataEmprestimo", "PrevisaoDevolucao", "DataDevolucaoReal"}
        if not campos_esperados.issubset(dados.keys()):
            abort(400, description=f"PUT requer todos os campos: {', '.join(campos_esperados)}")

    # Monta dinamicamente o SQL somente com os campos enviados
    campos_validos = {"DataEmprestimo", "PrevisaoDevolucao", "DataDevolucaoReal"}
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


@emprestimos.route("/emprestimos/novo", methods=["POST"])
def criar_emprestimo_novo():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "JSON inválido ou ausente."}), 400

    campos = [
        "tipoUsuario",
        "idUsuario",
        "idLivro",
        "DataEmprestimo",
        "PrevisaoDevolucao"
    ]

    if any(dados.get(campo) in (None, "") for campo in campos):
        return jsonify({
            "erro": "Preencha todos os campos obrigatórios."
        }), 400

    tipo = dados["tipoUsuario"]

    if tipo not in ("aluno", "funcionario"):
        return jsonify({"erro": "Tipo de usuário inválido."}), 400

    try:
        id_usuario = int(dados["idUsuario"])
        id_livro = int(dados["idLivro"])
    except (ValueError, TypeError):
        return jsonify({"erro": "Usuário ou livro inválido."}), 400

    data_emprestimo = dados["DataEmprestimo"]
    previsao = dados["PrevisaoDevolucao"]

    if previsao < data_emprestimo:
        return jsonify({
            "erro": "A previsão de devolução não pode ser anterior ao empréstimo."
        }), 400

    conn = conectar()

    try:
        cursor = conn.cursor()

        # Confirma que o livro existe
        cursor.execute(
            "SELECT idLivro FROM livros WHERE idLivro = %s",
            (id_livro,)
        )

        if cursor.fetchone() is None:
            return jsonify({"erro": "Livro não encontrado."}), 404

        if tipo == "aluno":
            cursor.execute(
                "SELECT idAluno FROM aluno WHERE idAluno = %s",
                (id_usuario,)
            )

            if cursor.fetchone() is None:
                return jsonify({"erro": "Aluno não encontrado."}), 404

            cursor.execute("""
                INSERT INTO emprestimos (
                    DataEmprestimo,
                    PrevisaoDevolucao,
                    DataDevolucaoReal,
                    idLivro,
                    idAluno,
                    idfuncionario
                )
                VALUES (%s, %s, NULL, %s, %s, NULL)
            """, (
                data_emprestimo,
                previsao,
                id_livro,
                id_usuario
            ))

        else:
            cursor.execute(
                "SELECT idfuncionario FROM funcionario WHERE idfuncionario = %s",
                (id_usuario,)
            )

            if cursor.fetchone() is None:
                return jsonify({"erro": "Funcionário não encontrado."}), 404

            cursor.execute("""
                INSERT INTO emprestimos (
                    DataEmprestimo,
                    PrevisaoDevolucao,
                    DataDevolucaoReal,
                    idLivro,
                    idAluno,
                    idfuncionario
                )
                VALUES (%s, %s, NULL, %s, NULL, %s)
            """, (
                data_emprestimo,
                previsao,
                id_livro,
                id_usuario
            ))

        conn.commit()

        return jsonify({
            "mensagem": "Empréstimo registrado com sucesso!",
            "idEmprestimo": cursor.lastrowid
        }), 201

    except Exception:
        conn.rollback()
        return jsonify({
            "erro": "Erro interno ao registrar o empréstimo."
        }), 500

    finally:
        conn.close()