from flask import Blueprint, jsonify,request,abort

from conectar.funcaoConectar import conectar

emprestimos = Blueprint('emprestimos', __name__)


#ROTAS PARA A TABELA SERIE B

## ROTA GET — LISTAR EMPRÉSTIMOS COM USUÁRIO E LIVRO

@emprestimos.route("/emprestimos", methods=["GET"])
def listar_CadastrosB():
    conn = conectar()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.idEmprestimo,
                e.DataEmprestimo,
                e.PrevisaoDevolucao,
                e.DataDevolucaoReal,
                e.idLivro,
                l.NomeLivro,
                e.idAluno,
                a.NomeAluno,
                e.idfuncionario,
                f.NomeFuncionario,
                CASE
                    WHEN e.idAluno IS NOT NULL THEN 'Aluno'
                    WHEN e.idfuncionario IS NOT NULL THEN 'Funcionário'
                    ELSE 'Não identificado'
                END AS TipoUsuario,
                COALESCE(
                    a.NomeAluno,
                    f.NomeFuncionario,
                    'Usuário não identificado'
                ) AS NomeUsuario
            FROM emprestimos e
            LEFT JOIN livros l
                ON e.idLivro = l.idLivro
            LEFT JOIN aluno a
                ON e.idAluno = a.idAluno
            LEFT JOIN funcionario f
                ON e.idfuncionario = f.idfuncionario
            ORDER BY e.idEmprestimo DESC
        """)

        dados = [
            {
                "idEmprestimo": row[0],
                "DataEmprestimo": row[1],
                "PrevisaoDevolucao": row[2],
                "DataDevolucaoReal": row[3],
                "idLivro": row[4],
                "NomeLivro": row[5],
                "idAluno": row[6],
                "NomeAluno": row[7],
                "idfuncionario": row[8],
                "NomeFuncionario": row[9],
                "TipoUsuario": row[10],
                "NomeUsuario": row[11]
            }
            for row in cursor.fetchall()
        ]

        return jsonify(dados), 200

    except Exception:
        return jsonify({
            "erro": "Não foi possível consultar os empréstimos."
        }), 500

    finally:
        conn.close()


##ROTA INSERT
#############################################

@emprestimos.route("/emprestimos", methods=["POST"])
def criar_usuarioB():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "JSON inválido ou ausente."}), 400

    obrigatorios = [
        "DataEmprestimo",
        "PrevisaoDevolucao",
        "idLivro"
    ]

    if any(dados.get(campo) in (None, "") for campo in obrigatorios):
        return jsonify({
            "erro": "Informe as datas e o livro."
        }), 400

    id_aluno = dados.get("idAluno")
    id_funcionario = dados.get("idfuncionario")

    if (id_aluno in (None, "")) == (id_funcionario in (None, "")):
        return jsonify({
            "erro": "Informe exatamente um aluno ou um funcionário."
        }), 400

    try:
        id_livro = int(dados["idLivro"])
        id_aluno = int(id_aluno) if id_aluno not in (None, "") else None
        id_funcionario = (
            int(id_funcionario)
            if id_funcionario not in (None, "")
            else None
        )
    except (ValueError, TypeError):
        return jsonify({"erro": "Identificadores inválidos."}), 400

    data = dados["DataEmprestimo"]
    previsao = dados["PrevisaoDevolucao"]

    if previsao < data:
        return jsonify({
            "erro": "A previsão não pode ser anterior ao empréstimo."
        }), 400

    conn = conectar()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT idLivro FROM livros WHERE idLivro = %s",
            (id_livro,)
        )
        if cursor.fetchone() is None:
            return jsonify({"erro": "Livro não encontrado."}), 404

        if id_aluno is not None:
            cursor.execute(
                "SELECT idAluno FROM aluno WHERE idAluno = %s",
                (id_aluno,)
            )
            if cursor.fetchone() is None:
                return jsonify({"erro": "Aluno não encontrado."}), 404

        if id_funcionario is not None:
            cursor.execute(
                "SELECT idfuncionario FROM funcionario WHERE idfuncionario = %s",
                (id_funcionario,)
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
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data,
            previsao,
            dados.get("DataDevolucaoReal") or None,
            id_livro,
            id_aluno,
            id_funcionario
        ))

        novo_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "mensagem": "Empréstimo registrado com sucesso!",
            "idEmprestimo": novo_id
        }), 201

    except Exception:
        conn.rollback()
        return jsonify({
            "erro": "Erro interno ao registrar o empréstimo."
        }), 500

    finally:
        conn.close()

##ROTA UPDATE
#############################################

@emprestimos.route("/emprestimos/<int:idEmprestimo>", methods=["PUT"])
def atualizar_usuarioB(idEmprestimo):
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "JSON inválido ou ausente."}), 400

    campos_obrigatorios = {
        "DataEmprestimo",
        "PrevisaoDevolucao",
        "DataDevolucaoReal",
        "idLivro",
        "idAluno",
        "idfuncionario"
    }

    if not campos_obrigatorios.issubset(dados.keys()):
        return jsonify({
            "erro": "Informe todas as datas, o livro e os campos de usuário."
        }), 400

    data_emprestimo = dados["DataEmprestimo"]
    previsao = dados["PrevisaoDevolucao"]
    data_devolucao = dados["DataDevolucaoReal"]

    try:
        id_livro = int(dados["idLivro"])
        id_aluno = (
            int(dados["idAluno"])
            if dados["idAluno"] not in (None, "") else None
        )
        id_funcionario = (
            int(dados["idfuncionario"])
            if dados["idfuncionario"] not in (None, "") else None
        )
    except (ValueError, TypeError):
        return jsonify({"erro": "Identificadores inválidos."}), 400

    if (id_aluno is None) == (id_funcionario is None):
        return jsonify({
            "erro": "Informe exatamente um aluno ou um funcionário."
        }), 400

    if previsao < data_emprestimo:
        return jsonify({
            "erro": "A previsão de devolução não pode ser anterior ao empréstimo."
        }), 400

    conn = conectar()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT idEmprestimo FROM emprestimos WHERE idEmprestimo = %s",
            (idEmprestimo,)
        )
        if cursor.fetchone() is None:
            return jsonify({"erro": "Empréstimo não encontrado."}), 404

        cursor.execute(
            "SELECT idLivro FROM livros WHERE idLivro = %s",
            (id_livro,)
        )
        if cursor.fetchone() is None:
            return jsonify({"erro": "Livro não encontrado."}), 404

        if id_aluno is not None:
            cursor.execute(
                "SELECT idAluno FROM aluno WHERE idAluno = %s",
                (id_aluno,)
            )
            if cursor.fetchone() is None:
                return jsonify({"erro": "Aluno não encontrado."}), 404

        if id_funcionario is not None:
            cursor.execute(
                "SELECT idfuncionario FROM funcionario WHERE idfuncionario = %s",
                (id_funcionario,)
            )
            if cursor.fetchone() is None:
                return jsonify({"erro": "Funcionário não encontrado."}), 404

        cursor.execute("""
            UPDATE emprestimos
            SET DataEmprestimo = %s,
                PrevisaoDevolucao = %s,
                DataDevolucaoReal = %s,
                idLivro = %s,
                idAluno = %s,
                idfuncionario = %s
            WHERE idEmprestimo = %s
        """, (
            data_emprestimo,
            previsao,
            data_devolucao or None,
            id_livro,
            id_aluno,
            id_funcionario,
            idEmprestimo
        ))

        conn.commit()

        return jsonify({
            "mensagem": "Empréstimo atualizado com sucesso.",
            "idEmprestimo": idEmprestimo
        }), 200

    except Exception:
        conn.rollback()
        return jsonify({
            "erro": "Erro interno ao atualizar o empréstimo."
        }), 500

    finally:
        conn.close()

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