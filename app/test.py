
from flask import Blueprint
from flask_cors import CORS
from app.models import db, Map

test = Blueprint('TEST', __name__)
CORS(test)

@test.route('/test/reset_db')
def reset_db():
    for m in db.session.query(Map).all():
        db.session.delete(m)
    db.session.commit()
    return ('', 200)
