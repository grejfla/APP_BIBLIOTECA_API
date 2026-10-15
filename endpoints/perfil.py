from flask import Blueprint, jsonify
from conectar.funcaoConectar import conectar
from endpoints.renovacao import MAX_RENOVACOES

perfil = Blueprint("perfil", __name__)


def _data(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


@perfil.route("/usuario/<tipo>/<int:id_usuario>/perfil", methods=["GET"])
def perfil_usuario(tipo, id_usuario):
    if tipo not in ("aluno", "funcionario"):
        return jsonify({"erro": "Tipo de usuário inválido."}), 400

    conn = conectar()
    try:
        cursor = conn.cursor()

        if tipo == "aluno":
            cursor.execute(
                """
                SELECT idAluno, NomeAluno, MatriculaAluno,
                       TurmaAluno, ContatoAluno, EnderecoAluno
                FROM aluno WHERE idAluno = %s
                """,
                (id_usuario,)
            )
            row = cursor.fetchone()
            if row is None:
                return jsonify({"erro": "Usuário não encontrado."}), 404
            dados = {
                "id": row[0], "nome": row[1], "identificacao": row[2],
                "turma": row[3], "contato": row[4], "endereco": row[5],
                "tipo": "Aluno"
            }
        else:
            cursor.execute(
                """
                SELECT idfuncionario, NomeFuncionario, RegistroFuncionario
                FROM funcionario WHERE idfuncionario = %s
                """,
                (id_usuario,)
            )
            row = cursor.fetchone()
            if row is None:
                return jsonify({"erro": "Usuário não encontrado."}), 404
            dados = {
                "id": row[0], "nome": row[1], "identificacao": row[2],
                "tipo": "Funcionário"
            }

        return jsonify(dados), 200

    except Exception:
        return jsonify({"erro": "Erro ao consultar o perfil."}), 500
    finally:
        conn.close()


@perfil.route("/usuario/<tipo>/<int:id_usuario>/emprestimos", methods=["GET"])
def emprestimos_usuario(tipo, id_usuario):
    if tipo not in ("aluno", "funcionario"):
        return jsonify({"erro": "Tipo de usuário inválido."}), 400

    # O nome da coluna vem de uma lista fixa, nunca do usuário.
    coluna = "e.idAluno" if tipo == "aluno" else "e.idfuncionario"

    conn = conectar()
    try:
        cursor = conn.cursor()

        # ===== INÍCIO DA TROCA =====
        cursor.execute(
            f"""
            SELECT e.idEmprestimo, l.NomeLivro, l.AutorLivro,
                   e.DataEmprestimo, e.PrevisaoDevolucao, e.DataDevolucaoReal,
                   (SELECT COUNT(*) FROM renovacoes r
                     WHERE r.idEmprestimo = e.idEmprestimo) AS Renovacoes
            FROM emprestimos e
            LEFT JOIN livros l ON e.idLivro = l.idLivro
            WHERE {coluna} = %s
            ORDER BY e.idEmprestimo DESC
            """,
            (id_usuario,)
        )
        dados = [
            {
                "idEmprestimo": r[0],
                "NomeLivro": r[1],
                "AutorLivro": r[2],
                "DataEmprestimo": _data(r[3]),
                "PrevisaoDevolucao": _data(r[4]),
                "DataDevolucaoReal": _data(r[5]),
                "Renovacoes": r[6],
                "LimiteRenovacoes": MAX_RENOVACOES
            }
            for r in cursor.fetchall()
        ]
        # ===== FIM DA TROCA =====

        return jsonify(dados), 200

    except Exception:
        return jsonify({"erro": "Erro ao consultar os empréstimos."}), 500
    finally:
        conn.close()