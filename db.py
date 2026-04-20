from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        "mssql+pyodbc://sa:123456@DESKTOP-4952DA1/MissingChildrenDB"
        "?driver=ODBC Driver 17 for SQL Server"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)