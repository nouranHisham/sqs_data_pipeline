from datetime import datetime, timedelta, timezone
import json
import time

def transform_to_trip(message: str):

    msg = json.loads(message)

    # Combine name + surname
    full_name = f"{msg.get('name', '')} {msg.get('surname', '')}".strip()

    # Build trip in correct order
    if "route" in msg:
        route = msg["route"]
        last = route[-1]

        start = datetime.strptime(last["started_at"], "%d/%m/%Y %H:%M:%S")
        
        end_date = start + timedelta(minutes=last["duration"])
        start_date = datetime.strptime(route[0]["started_at"], "%d/%m/%Y %H:%M:%S")

        trip = {
            "departure": route[0]["from"],
            "destination": last["to"],
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S")
        }

    elif "locations" in msg:
        locs = msg["locations"]

        trip = {
            "departure": locs[0]["location"],
            "destination": locs[-1]["location"],
            "start_date": datetime.fromtimestamp(locs[0]["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": datetime.fromtimestamp(locs[-1]["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }

    else:
        raise ValueError("Unknown message type")

    return {
        "id": msg["id"],
        "mail": msg["mail"],
        "name": full_name,
        "trip": trip
    }

