from flask import Blueprint, jsonify, request
from conectar.funcaoConectar import conectar

login = Blueprint("login", __name__)


@login.route("/login", methods=["POST"])
def autenticar_usuario():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados de login inválidos."
        }), 400

    tipo = dados.get("tipoUsuario")
    identificacao = str(
        dados.get("identificacao") or ""
    ).strip()
    senha = dados.get("senha")

    if not tipo or not identificacao or not senha:
        return jsonify({
            "erro": "Preencha a identificação e a senha."
        }), 400

    if tipo not in ("funcionario", "aluno"):
        return jsonify({
            "erro": "Tipo de usuário inválido."
        }), 400

    if tipo == "aluno" and not identificacao.isdigit():
        return jsonify({
            "erro": "A matrícula deve conter somente números."
        }), 400

    conn = None
    cursor = None

    try:
        conn = conectar()
        cursor = conn.cursor()

        if tipo == "funcionario":
            cursor.execute(
                """
                SELECT idfuncionario, NomeFuncionario
                FROM funcionario
                WHERE RegistroFuncionario = %s
                  AND SenhaFuncionario = %s
                """,
                (identificacao, senha)
            )
        else:
            cursor.execute(
                """
                SELECT idAluno, NomeAluno
                FROM aluno
                WHERE MatriculaAluno = %s
                  AND SenhaAluno = %s
                """,
                (int(identificacao), senha)
            )

        usuario = cursor.fetchone()

        if usuario is None:
            return jsonify({
                "erro": "Identificação ou senha incorreta."
            }), 401

        return jsonify({
            "mensagem": "Login realizado com sucesso!",
            "tipoUsuario": tipo,
            "id": usuario[0],
            "nome": usuario[1]
        }), 200

    except Exception:
        # Registre o erro detalhado no terminal do servidor
        # durante o desenvolvimento, sem expô-lo ao usuário.
        import logging
        logging.exception("Erro ao autenticar usuário")

        return jsonify({
            "erro": "Erro interno ao consultar o banco de dados."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()