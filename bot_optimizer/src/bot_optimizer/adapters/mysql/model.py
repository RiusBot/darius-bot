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
    result = db.Column(db.Text, nullable=False)
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


class Message(db.Model, serialize):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    symbol = db.Column(db.String(32), nullable=False)
    action = db.Column(db.String(32), nullable=False)
    channel = db.Column(db.String(32), nullable=False)
    message_timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Message {self.id}>'