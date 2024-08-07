from flask import Flask
from src.gRNA_bp import gRNA_blueprint
from src.report_bp import report_blueprint

app=Flask(__name__)
app.register_blueprint(gRNA_blueprint)
app.register_blueprint(report_blueprint)


if __name__=='__main__':
    app.run(debug=True)