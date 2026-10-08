from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from conectar.funcaoConectar import conectar

from endpoints.aluno import aluno
from endpoints.emprestimos import emprestimos
from endpoints.funcionario import funcionario
from endpoints.livros import livros

app = Flask(__name__)

CORS (app)

app.register_blueprint(aluno)
app.register_blueprint(emprestimos)
app.register_blueprint(funcionario)
app.register_blueprint(livros)

@app.errorhandler(HTTPException)
def erro_json(e):
    return jsonify({"erro": e.description}), e.code

if __name__ == "__main__":
    app.run(debug=True)
