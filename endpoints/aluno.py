from flask import  Blueprint, jsonify, request, abort

from conectar.funcaoConectar import conectar


aluno = Blueprint('aluno', __name__)


#ROTAS PARA A TABELA SERIE A
##ROTA GET
##############################################
aluno.route("/aluno", methods=["GET"])
def listar_Cadastros():
    conn = conectar()
    #conn.execute("PRAGMA foreign_keys = ON") #ativa as chaves estrangeiras das tabelas (pois, não é ativado por padrão)
    cursor = conn.cursor()
    cursor.execute("SELECT idAluno, NomeAluno, SenhaAluno, MatriculaAluno,EnderecoAluno FROM aluno")
    dados = [
        {idAluno": row[0], "NomeAluno": row[1], "SenhaAluno": row[2], "MatriculaAluno": row[3], "EnderecoAluno": row [4]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(dados)

##ROTA INSERT
#############################################
@aluno.route("/aluno", methods=["POST"])
def criar_usuario():
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Validação de campos obrigatórios
    campos_obrigatorios = {"NomeAluno", "SenhaAluno", "MatriculaAluno", "EnderecoAluno"}
    if not campos_obrigatorios.issubset(dados.keys()):
        abort(400, description=f"Campos obrigatórios: {', '.join(campos_obrigatorios)}")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO aluno (NomeAluno, SenhaAluno , MatriculaAluno , EnderecoAluno)"
        "VALUES (?, ?, ?, ?,)",
        (dados["NomeAluno"], dados["SenhaAluno"], dados["MatriculaAluno"], dados["EnderecoAluno"])
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    # 201 Created + Location do recurso recém‑criado
    resposta = jsonify({"idAluno": novo_id, **dados})
    resposta.status_code = 201
    resposta.headers["Location"] = f"/aluno/{novo_id}"
    return resposta

##ROTA UPDATE
#############################################
@aluno.route("/aluno/<int:idAluno>", methods=["PUT", "PATCH"])
def atualizar_usuario(idAluno):
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Para PUT, garanta que todos os campos estejam presentes
    if request.method == "PUT":
        campos_esperados = {"NomeAluno", "SenhaAluno", "MatriculaAluno", "EnderecoAluno"}
        if not campos_esperados.issubset(dados.keys()):
            abort(400, description=f"PUT requer todos os campos: {', '.join(campos_esperados)}")

    # Monta dinamicamente o SQL somente com os campos enviados
    campos_validos = {"NomeAluno", "SenhaAluno", "MatriculaAluno", "EnderecoAluno"}
    set_clauses = []
    valores = []
    for campo in campos_validos & dados.keys():
        set_clauses.append(f"{campo} = ?")
        valores.append(dados[campo])

    if not set_clauses:
        abort(400, description="Nenhum campo válido para atualizar")

    valores.append(idAluno)  # último parâmetro é o WHERE

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE aluno SET {', '.join(set_clauses)} WHERE idAluno = ?",
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
@aluno.route("/aluno/<int:idAluno>", methods=["DELETE"])
def deletaraluno(idAluno):
    conn = conectar()
    cursor = conn.cursor()

    # tenta apagar o registro informado
    cursor.execute("DELETE FROM aluno WHERE idAluno = ?", (idAluno,))
    conn.commit()

    # cursor.rowcount informa quantas linhas foram afetadas
    if cursor.rowcount == 0:
        conn.close()
        # nenhum registro com esse ID → devolve 404
        abort(404, description="usuário não encontrado")

    conn.close()
    # 204 = No Content (padrão para deleções bem‑sucedidas)
    return ("", 204)