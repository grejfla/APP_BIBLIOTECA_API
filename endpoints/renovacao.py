from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from conectar.funcaoConectar import conectar

renovacao = Blueprint("renovacao", __name__)

DIAS_RENOVACAO = 7      # dias somados a cada renovação
MAX_RENOVACOES = 2      # limite por empréstimo


def _para_date(valor):
    """Aceita date, datetime ou texto 'AAAA-MM-DD'."""
    if hasattr(valor, "date") and callable(valor.date):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


@renovacao.route("/emprestimos/<int:id_emprestimo>/renovar", methods=["PUT"])
def renovar_emprestimo(id_emprestimo):
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "JSON inválido ou ausente."}), 400

    tipo = dados.get("tipoUsuario")
    if tipo not in ("aluno", "funcionario"):
        return jsonify({"erro": "Tipo de usuário inválido."}), 400

    try:
        id_usuario = int(dados.get("idUsuario"))
    except (ValueError, TypeError):
        return jsonify({"erro": "Usuário inválido."}), 400

    conn = conectar()

    try:
        cursor = conn.cursor()

        # FOR UPDATE trava a linha: evita duas renovações simultâneas.
        cursor.execute(
            """
            SELECT idEmprestimo, PrevisaoDevolucao, DataDevolucaoReal,
                   idAluno, idfuncionario
            FROM emprestimos
            WHERE idEmprestimo = %s
            FOR UPDATE
            """,
            (id_emprestimo,)
        )
        emp = cursor.fetchone()

        if emp is None:
            return jsonify({"erro": "Empréstimo não encontrado."}), 404

        _, previsao_atual, devolucao_real, id_aluno, id_func = emp

        # O empréstimo precisa ser do usuário que está renovando.
        dono = id_aluno if tipo == "aluno" else id_func
        if dono != id_usuario:
            return jsonify({
                "erro": "Este empréstimo não pertence ao usuário informado."
            }), 403

        if devolucao_real is not None:
            return jsonify({
                "erro": "Este empréstimo já foi devolvido."
            }), 409

        try:
            previsao = _para_date(previsao_atual)
        except (ValueError, TypeError):
            return jsonify({
                "erro": "Previsão de devolução inválida no cadastro."
            }), 500

        if previsao < date.today():
            return jsonify({
                "erro": "Empréstimo em atraso não pode ser renovado. "
                        "Procure o balcão para regularizar."
            }), 409

        cursor.execute(
            "SELECT COUNT(*) FROM renovacoes WHERE idEmprestimo = %s",
            (id_emprestimo,)
        )
        feitas = cursor.fetchone()[0]

        if feitas >= MAX_RENOVACOES:
            return jsonify({
                "erro": f"Limite de {MAX_RENOVACOES} renovações atingido."
            }), 409

        nova = previsao + timedelta(days=DIAS_RENOVACAO)

        cursor.execute(
            "UPDATE emprestimos SET PrevisaoDevolucao = %s "
            "WHERE idEmprestimo = %s",
            (nova.isoformat(), id_emprestimo)
        )

        cursor.execute(
            """
            INSERT INTO renovacoes (
                idEmprestimo, PrevisaoAnterior, NovaPrevisao,
                idAluno, idfuncionario
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                id_emprestimo,
                previsao.isoformat(),
                nova.isoformat(),
                id_usuario if tipo == "aluno" else None,
                id_usuario if tipo == "funcionario" else None
            )
        )

        conn.commit()

        return jsonify({
            "mensagem": "Empréstimo renovado com sucesso!",
            "idEmprestimo": id_emprestimo,
            "PrevisaoDevolucao": nova.isoformat(),
            "renovacoes": feitas + 1,
            "restantes": MAX_RENOVACOES - (feitas + 1)
        }), 200

    except Exception:
        conn.rollback()
        import logging
        logging.exception("Erro ao renovar empréstimo")
        return jsonify({"erro": "Erro interno ao renovar o empréstimo."}), 500

    finally:
        conn.close()