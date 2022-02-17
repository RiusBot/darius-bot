from bot_optimizer.flask_app import db


class serialize():
    def to_dict(self):
        obj = vars(self)
        obj.pop('_sa_instance_state')
        # if "created_at" in obj:
        #     obj.pop("created_at")
        # if "update_at" in obj:
        #     obj.pop("update_at")
        return obj


class Performance(db.Model, serialize):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    breakdown = db.Column(db.String(8), nullable=False)
    result = db.Column(db.String(4096), nullable=False)
    channel = db.Column(db.String(32), nullable=False)
    hyper_id = db.Column(db.Integer, db.ForeignKey('hyperopt.id'), nullable=False)

    def __repr__(self):
        return f'<Performance {self.id}>'


class Hyperopt(db.Model, serialize):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    # updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    params = db.Column(db.String(4096), nullable=False)
    channel = db.Column(db.String(32), nullable=False)
    loss = db.Column(db.String(32), nullable=False)
    days = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Hyperopt {self.id}>'