import geoacumen
import maxminddb
from flask import current_app

IP_ADDR_LOOKUP = maxminddb.open_database(
    current_app.config.get("GEOIP_DATABASE_PATH", geoacumen.db_path)
)


def lookup_ip_address(addr):
    # strip port from IP address if set by proxy, i.e. via X-Forwarded-For
    response = IP_ADDR_LOOKUP.get(addr.split(':')[0])
    try:
        return response["country"]["iso_code"]
    except KeyError:
        return None
