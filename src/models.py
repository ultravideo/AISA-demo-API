from src import db


class Encoding(db.Model):
    id = db.Column(db.CHAR(36), primary_key=True)
    out_path = db.Column(db.VARCHAR(2048))
