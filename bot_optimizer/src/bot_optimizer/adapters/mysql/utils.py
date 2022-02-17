import logging
from datetime import datetime


def create_performance(db, start_at: datetime, end_at: datetime, breakdown: str, result: str, channel: str, hyper_id: int):
    from bot_optimizer.adapters.mysql.model import Performance
    performance = Performance(
        start_at=start_at,
        end_at=end_at,
        breakdown=breakdown,
        result=result,
        channel=channel,
        hyper_id=hyper_id
    )
    db.session.add(performance)
    db.session.commit()
    logging.info(f"create performance {performance}")


def create_hyperopt(db, params: str, channel: str, days: int, loss: str, start_at: datetime, end_at: datetime):
    from bot_optimizer.adapters.mysql.model import Hyperopt
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
        raise Exception(f"{channel} has no {loss} optimized config.")

    logging.info(f"Get hyperopt {hyperopt}")
    return hyperopt
