from __future__ import absolute_import

from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from ogn.model import Flarm
from ogn.utils import get_ddb

logger = get_task_logger(__name__)


@app.task
def update_ddb_data():
    logger.info("Update ddb data.")

    app.session.query(Flarm).delete()

    devices = get_ddb()
    logger.info("Devices: %s"%str(devices))
    app.session.bulk_save_objects(devices)

    app.session.commit()
    return len(devices)

# TODO: Reimplement.
def import_ddb_data(filename='custom.txt'):
    flarms = get_ddb(filename)
    db.session.bulk_save_objects(flarms)
    session.commit()
