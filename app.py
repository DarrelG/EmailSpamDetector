import os
import uuid
import pickle
import logging
from flask_cors import CORS
from urllib.parse import quote
from AppModel import db, Email
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
secret_key = os.urandom(24)

# Muat model dan vectorizer
with open("model/MNB.pkl", "rb") as model_file:
    model = pickle.load(model_file)

with open("model/vectorizer.pkl", "rb") as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://[Isi data untuk database]'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key

# Inisialisasi SQLAlchemy
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

#Route utama
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            from_email = request.form.get('from_email')
            to_email = request.form.get('to_email')

            # Buat email baru dan simpan ke database
            new_email = Email(
                IdEmail=str(uuid.uuid4()), 
                Title=title,
                Content=content,
                IsSpam=False, 
                Time=datetime.now(),
                ToEmail=to_email,
                FromEmail=from_email,
                IsProcessed=False
            )

            db.session.add(new_email); 
            db.session.commit()
            flash("Email added successfully!", "success")
            return redirect(url_for('index'))

        inbox_emails = Email.query.filter_by(IsSpam=False).all()
        spam_emails = Email.query.filter_by(IsSpam=True).all()
        
        return render_template('index.html', inbox_emails=inbox_emails, spam_emails=spam_emails)
    
    except Exception:
        db.session.rollback()
        inbox_emails = Email.query.filter_by(IsSpam=False).all()
        spam_emails = Email.query.filter_by(IsSpam=True).all()
        return render_template('index.html', inbox_emails=inbox_emails, spam_emails=spam_emails)


@app.route("/predict", methods=["POST"])
def predict():
        
        AllData = Email.query.filter_by(IsSpam=False, IsProcessed=False).all()
        for email in AllData:
            title = email.Title
            content = email.Content
            timestamp = email.Time
            from_email = email.FromEmail
            to_email = email.ToEmail

            email_text = f"Subject: {title}\nBody: {content}\nFrom: {from_email}\nTo: {to_email}\nTimestamp: {timestamp}"

            # Vektorisasi teks gabungan dan prediksi spam
            text_vector = vectorizer.transform([email_text])
            prediction = model.predict(text_vector)[0]
            is_spam = True if prediction else False
            
            if(is_spam):
                email.IsSpam = is_spam
            
            email.IsProcessed = True
            db.session.commit()

        return 'Email Scanned'

@app.route("/delete", methods=['DELETE'])
def delete():
    try:
        data = request.get_json()
        email_id = data.get('id')
        
        if not email_id:
            return jsonify({"error": "No ID provided"}), 400

        email = Email.query.filter_by(IdEmail=email_id).first()
        if not email:
            return jsonify({"error": "Email not found"}), 404

        db.session.delete(email)
        db.session.commit()
        return jsonify({"message": "Email deleted successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Menjalankan aplikasi Flask
if __name__ == '__main__':
    app.run(debug=True)

