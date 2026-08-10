from flask import Flask, jsonify

from conectar.funcaoConectar import conectar

from endpoints.serieA import TabelaSerie_A_bp
from endpoints.serieB import TabelaSerie_B_bp
from endpoints.serieC import TabelaSerie_C_bp
from endpoints.serieD import TabelaSerie_D_bp

app = Flask(__name__)

app.register_blueprint(TabelaSerie_A_bp)
app.register_blueprint(TabelaSerie_B_bp)
app.register_blueprint(TabelaSerie_C_bp)
app.register_blueprint(TabelaSerie_D_bp)

if __name__ == "__main__":
    app.run(debug=True)
