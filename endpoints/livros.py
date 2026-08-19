from flask import Blueprint, jsonify, request, abort

from conectar.funcaoConectar import conectar

livros = Blueprint('livros', __name__)

#ROTAS PARA A TABELA SERIE D
##ROTA GET
##############################################
@livros.route("/livros", methods=["GET"])
def listar_CadastrosD():
    conn = conectar()
    #conn.execute("PRAGMA foreign_keys = ON") #ativa as chaves estrangeiras das tabelas (pois, não é ativado por padrão)
    cursor = conn.cursor()
    cursor.execute("SELECT idLivro, NomeLivro, AutorLivro, EditoraLivro, Ano_Edicao_livro, Categoria_Livro, QuantidadeLivro, StatusLivros FROM livros")
    dados = [
        {"idLivro": row[0], "NomeLivro": row[1], "AutorLivro": row[2], "EditoraLivro": row[3], "Ano_Edicao_livro": row [4], "Categoria_Livro": row [5], "QuantidadeLivro": row [6], "StatusLivros": row [7]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(dados)

##ROTA INSERT
#############################################
@livros.route("/livros", methods=["POST"])
def criar_usuarioD():
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Validação de campos obrigatórios
    campos_obrigatorios = {"NomeLivro", "AutorLivro", "EditoraLivro", "Ano_Edicao_livro", "Categoria_Livro","QuantidadeLivro", "StatusLivros"}
    if not campos_obrigatorios.issubset(dados.keys()):
        abort(400, description=f"Campos obrigatórios: {', '.join(campos_obrigatorios)}")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO livros (NomeLivro, AutorLivro, EditoraLivro, Ano_Edicao_livro, Categoria_Livro, QuantidadeLivro, StatusLivros)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (dados["NomeLivro"], dados["AutorLivro"], dados["EditoraLivro"], dados["Ano_Edicao_livro"], dados["Categoria_Livro"], dados["QuantidadeLivro"], dados["StatusLivros"])
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    # 201 Created + Location do recurso recém‑criado
    resposta = jsonify({"idLivro": novo_id, **dados})
    resposta.status_code = 201
    resposta.headers["Location"] = f"/livros/{novo_id}"
    return resposta

##ROTA UPDATE
#############################################
@livros.route("/livros/<int:idLivro>", methods=["PUT", "PATCH"])
def atualizar_usuarioD(idLivro):
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, description="JSON inválido ou ausente")

    # Para PUT, garanta que todos os campos estejam presentes
    if request.method == "PUT":
        campos_esperados = {"NomeLivro", "AutorLivro", "EditoraLivro", "Ano_Edicao_Livro", "Categoria_Livro", "QuantidadeLivro", "StatusLivros"}
        if not campos_esperados.issubset(dados.keys()):
            abort(400, description=f"PUT requer todos os campos: {', '.join(campos_esperados)}")

    # Monta dinamicamente o SQL somente com os campos enviados
    campos_validos = {"NomeLivro", "AutorLivro", "EditoraLivro", "Ano_Edicao_livro", "Categoria_Livro", "QuantidadeLivro", "StatusLivros"}
    set_clauses = []
    valores = []
    for campo in campos_validos & dados.keys():
        set_clauses.append(f"{campo} = %s")
        valores.append(dados[campo])

    if not set_clauses:
        abort(400, description="Nenhum campo válido para atualizar")

    valores.append(idLivro)  # último parâmetro é o WHERE

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE livros SET {', '.join(set_clauses)} WHERE idLivro = %s",
        tuple(valores)
    )
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        abort(404, description="livro não encontrado")

    conn.close()
    # 204 = No Content, mas você pode devolver 200 com o JSON atualizado se preferir
    return ("", 204)


##ROTA DELETE
#############################################
@livros.route("/livros/<int:idLivro>", methods=["DELETE"])
def deletarlivros(idLivro):
    conn = conectar()
    cursor = conn.cursor()

    # tenta apagar o registro informado
    cursor.execute("DELETE FROM TabelaSerieD WHERE idLivro = %s", (idLivro,))
    conn.commit()

    # cursor.rowcount informa quantas linhas foram afetadas
    if cursor.rowcount == 0:
        conn.close()
        # nenhum registro com esse ID → devolve 404
        abort(404, description="livro não encontrado")

    conn.close()
    # 204 = No Content (padrão para deleções bem‑sucedidas)
    return ("", 204)