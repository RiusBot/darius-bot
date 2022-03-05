import json
import logging
from datetime import datetime


def create_performance(db, start_at: datetime, end_at: datetime, result: str, channel: str, hyperopt):
    from bot_optimizer.adapters.mysql.model import Performance
    performance = Performance.query.filter_by(
        start_at=start_at,
        end_at=end_at,
        channel=channel,
    ).first()

    if performance is None:
        performance = Performance(
            start_at=start_at,
            end_at=end_at,
            result=result,
            channel=channel,
            hyperopt=hyperopt
        )
        db.session.add(performance)
        db.session.commit()
        logging.info(f"update performance {performance}")
    else:
        performance.hyperopt = hyperopt
        performance.result = result
        db.session.add(performance)
        db.session.commit()
        logging.info(f"create performance {performance}")


def create_hyperopt(db, params: str, channel: str, days: int, loss: str, start_at: datetime, end_at: datetime):
    from bot_optimizer.adapters.mysql.model import Hyperopt
    hyperopt = Hyperopt.query.filter_by(
        start_at=start_at,
        end_at=end_at,
        channel=channel,
        loss=loss,
    ).first()

    if hyperopt is None:
        hyperopt = Hyperopt(
            params=params,
            channel=channel,
            days=days,
            loss=loss,
            start_at=start_at,
            end_at=end_at
        )
        db.session.add(hyperopt)
        db.session.commit()
        logging.info(f"create hyperopt {hyperopt}")
    else:
        hyperopt.params = params
        hyperopt.days = days
        db.session.add(hyperopt)
        db.session.commit()
        logging.info(f"update instead of create")
    


def get_hyperopt(db, channel: str, loss: str, start_at: datetime):
    logging.info(f"Get hyperopt {channel} {loss} {start_at}")
    from bot_optimizer.adapters.mysql.model import Hyperopt
    hyperopt = Hyperopt.query.filter(
        Hyperopt.end_at < start_at,
        Hyperopt.channel == channel,
        Hyperopt.loss == loss
    ).order_by(
        Hyperopt.created_at.desc()
    ).first()

    if hyperopt is None:
        # hyperopt = Hyperopt.query.get(155)  # default
        hyperopt = Hyperopt.query.filter(Hyperopt.loss == 'default').first()

    logging.info(f"Get hyperopt {hyperopt}")
    return hyperopt


def get_channel(db):
    from bot_optimizer.adapters.mysql.model import Message
    channel_list = Message.query.with_entities(Message.channel).distinct().all()
    channel_list = [i[0] for i in channel_list if i[0] != "WEBHOOK"]
    return channel_list


def get_message(db, channel: str, start_at: datetime, end_at: datetime):
    logging.info(f"Get message {start_at} - {end_at}")
    from bot_optimizer.adapters.mysql.model import Message

    message_list = []
    for message in Message.query.filter(
        Message.message_timestamp <= end_at,
        Message.message_timestamp >= start_at,
        Message.channel == channel,
        Message.action.is_not(None),
        Message.symbol.is_not(None),
    ).all():
        message = message.to_dict()
        message.pop("created_at")
        message["message_timestamp"] = message["message_timestamp"].timestamp()
        message_list.append(message)

    logging.info(f"Get {len(message_list)} message from channel {channel}")
    return message_list
