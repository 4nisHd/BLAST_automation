from flask import Flask
from src.gRNA import gRNA_blueprint

app=Flask(__name__)
app.register_blueprint(gRNA_blueprint)
if __name__=='__main__':
    app.run(debug=True)