import logging
from datetime import datetime


def create_performance(db, start_at: datetime, breakdown: str, reuslt: str, channel: str, hyper_id: int):
    from bot_optimizer.adapters.mysql.model import Performance
    performance = Performance(
        start_at=start_at,
        breakdown=breakdown,
        reuslt=result,
        channel=channel,
        hyper_id=hyper_id
    )
    db.session.add(performance)
    db.session.commit()
    logging.info(f"create performance {performance}")


def create_hyperopt(db, params: str, channel: str, days: int, loss: str):
    from bot_optimizer.adapters.mysql.model import Hyperopt
    hyperopt = Hyperopt(
        params=params,
        channel=channel,
        days=days,
        loss=loss
    )
    db.session.add(hyperopt)
    db.session.commit()
    logging.info(f"create hyperopt {hyperopt}")


def get_hyperopt(db, channel: str, loss: str):
    from bot_optimizer.adapters.mysql.model import Hyperopt
    hyperopt = Hyperopt.query.filter_by(
        channel=channel,
        loss=loss
    ).order_by(Hyperopt.created_at.desc()).first()

    if hyperopt is None:
        raise Exception(f"{channel} has no {loss} optimized config.")
    return hyperopt.to_dict()['params']
