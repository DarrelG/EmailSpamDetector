import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

db = SQLAlchemy()

class Email(db.Model):
    __tablename__ = "MsEmail"

    IdEmail = db.Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4) 
    Title = db.Column(db.String(255), nullable=False)
    Content = db.Column(db.Text, nullable=False)
    IsSpam = db.Column(db.Boolean, default=False) 
    Time = db.Column(db.DateTime, default=datetime)
    ToEmail = db.Column(db.String(255))
    FromEmail = db.Column(db.String(255))
    IsProcessed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Email {self.Title}>'
