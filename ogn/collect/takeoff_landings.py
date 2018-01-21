from datetime import timedelta

from celery.utils.log import get_task_logger

from sqlalchemy import and_, or_, insert, between, exists
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import case

from ogn.collect.celery import app
from ogn.model import AircraftBeacon, TakeoffLanding, Airport

logger = get_task_logger(__name__)


@app.task
def update_takeoff_landings(session=None):
    """Compute takeoffs and landings."""

    logger.info("Compute takeoffs and landings.")

    if session is None:
        session = app.session

    # check if we have any airport
    airports_query = session.query(Airport)
    if not airports_query.all():
        logger.warn("Cannot calculate takeoff and landings without any airport! Please import airports first.")
        return

    # takeoff / landing detection is based on 3 consecutive points
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 5000       # the points must not exceed this radius around the 2nd point

    # takeoff / landing has to be near an airport
    airport_radius = 2500   # takeoff / landing must not exceed this radius around the airport
    airport_delta = 100     # takeoff / landing must not exceed this altitude offset above/below the airport

    # 'wo' is the window order for the sql window function
    wo = and_(AircraftBeacon.device_id,
              AircraftBeacon.timestamp,
              AircraftBeacon.receiver_id)

    # make a query with current, previous and next position
    beacon_selection = session.query(AircraftBeacon.id) \
        .order_by(AircraftBeacon.timestamp) \
        .limit(1000000) \
        .subquery()

    sq = session.query(
        AircraftBeacon.id,
        func.lag(AircraftBeacon.id).over(order_by=wo).label('id_prev'),
        func.lead(AircraftBeacon.id).over(order_by=wo).label('id_next'),
        AircraftBeacon.device_id,
        func.lag(AircraftBeacon.device_id).over(order_by=wo).label('device_id_prev'),
        func.lead(AircraftBeacon.device_id).over(order_by=wo).label('device_id_next'),
        AircraftBeacon.timestamp,
        func.lag(AircraftBeacon.timestamp).over(order_by=wo).label('timestamp_prev'),
        func.lead(AircraftBeacon.timestamp).over(order_by=wo).label('timestamp_next'),
        AircraftBeacon.location_wkt,
        func.lag(AircraftBeacon.location_wkt).over(order_by=wo).label('location_wkt_prev'),
        func.lead(AircraftBeacon.location_wkt).over(order_by=wo).label('location_wkt_next'),
        AircraftBeacon.track,
        func.lag(AircraftBeacon.track).over(order_by=wo).label('track_prev'),
        func.lead(AircraftBeacon.track).over(order_by=wo).label('track_next'),
        AircraftBeacon.ground_speed,
        func.lag(AircraftBeacon.ground_speed).over(order_by=wo).label('ground_speed_prev'),
        func.lead(AircraftBeacon.ground_speed).over(order_by=wo).label('ground_speed_next'),
        AircraftBeacon.altitude,
        func.lag(AircraftBeacon.altitude).over(order_by=wo).label('altitude_prev'),
        func.lead(AircraftBeacon.altitude).over(order_by=wo).label('altitude_next')) \
        .filter(AircraftBeacon.id == beacon_selection.c.id) \
        .subquery()

    # consider only positions with the same device id
    sq2 = session.query(sq) \
       .filter(sq.c.device_id_prev == sq.c.device_id == sq.c.device_id_next) \
       .subquery()

    # find possible takeoffs and landings
    sq3 = session.query(
        sq2.c.id,
        sq2.c.timestamp,
        case([(sq2.c.ground_speed > takeoff_speed, sq2.c.location_wkt_prev),  # on takeoff we take the location from the previous fix because it is nearer to the airport
              (sq2.c.ground_speed < landing_speed, sq2.c.location)]).label('location'),
        case([(sq2.c.ground_speed > takeoff_speed, sq2.c.track),
              (sq2.c.ground_speed < landing_speed, sq2.c.track_prev)]).label('track'),    # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
        sq2.c.ground_speed,
        sq2.c.altitude,
        case([(sq2.c.ground_speed > takeoff_speed, True),
              (sq2.c.ground_speed < landing_speed, False)]).label('is_takeoff'),
        sq2.c.device_id) \
        .filter(sq2.c.timestamp_next - sq2.c.timestamp_prev < timedelta(seconds=duration)) \
        .filter(and_(func.ST_Distance_Sphere(sq2.c.location, sq2.c.location_wkt_prev) < radius,
                     func.ST_Distance_Sphere(sq2.c.location, sq2.c.location_wkt_next) < radius)) \
        .filter(or_(and_(sq2.c.ground_speed_prev < takeoff_speed,    # takeoff
                         sq2.c.ground_speed > takeoff_speed,
                         sq2.c.ground_speed_next > takeoff_speed),
                    and_(sq2.c.ground_speed_prev > landing_speed,    # landing
                         sq2.c.ground_speed < landing_speed,
                         sq2.c.ground_speed_next < landing_speed))) \
        .subquery()

    # consider them if they are near a airport
    sq4 = session.query(
        sq3.c.timestamp,
        sq3.c.track,
        sq3.c.is_takeoff,
        sq3.c.device_id,
        Airport.id.label('airport_id')) \
        .filter(and_(func.ST_Distance_Sphere(sq3.c.location, Airport.location_wkt) < airport_radius,
                     between(sq3.c.altitude, Airport.altitude - airport_delta, Airport.altitude + airport_delta))) \
        .filter(between(Airport.style, 2, 5)) \
        .subquery()

    # consider them only if they are not already existing in db
    takeoff_landing_query = session.query(sq4) \
        .filter(~exists().where(
            and_(TakeoffLanding.timestamp == sq4.c.timestamp,
                 TakeoffLanding.device_id == sq4.c.device_id,
                 TakeoffLanding.airport_id == sq4.c.airport_id)))

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp,
                                              TakeoffLanding.track,
                                              TakeoffLanding.is_takeoff,
                                              TakeoffLanding.device_id,
                                              TakeoffLanding.airport_id),
                                             takeoff_landing_query)
    result = session.execute(ins)
    counter = result.rowcount

    session.commit()
    logger.debug("Inserted {} TakeoffLandings".format(counter))

    return "Inserted {} TakeoffLandings".format(counter)