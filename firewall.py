from datetime import datetime, timezone, timedelta
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from database import (
    request_windows,
    blocked_ips
)


REQUEST_LIMIT = 2      
WINDOW_SECONDS = 60      
AUTO_BLOCK_MINUTES = 10  


def utc_now():
    return datetime.now(timezone.utc)



def is_blocked(ip):
    now = utc_now()

    block = blocked_ips.find_one({
        "ip": ip,
        "$or": [
            {"manual": True},
            {"expire_at": {"$gt": now}},
            {"expire_at": {"$exists": False}}
        ]
    })

    return block is not None



def auto_block(ip, reason):
    now = utc_now()

    blocked_ips.update_one(
        {"ip": ip, "manual": {"$ne": True}},
        {
            "$set": {
                "reason": reason,
                "blocked_at": now,
                "expire_at": now + timedelta(
                    minutes=AUTO_BLOCK_MINUTES
                ),
                "manual": False
            }
        },
        upsert=True
    )


def count_request(ip):
    now = utc_now()

    window_number = int(now.timestamp() // WINDOW_SECONDS)
    window_start = datetime.fromtimestamp(
        window_number * WINDOW_SECONDS,
        tz=timezone.utc
    )

    expire_at = window_start + timedelta(
        seconds=WINDOW_SECONDS * 2
    )

    try:
        result = request_windows.find_one_and_update(
            {
                "ip": ip,
                "window_start": window_start
            },
            {
                "$inc": {"count": 1},
                "$setOnInsert": {
                    "ip": ip,
                    "window_start": window_start,
                    "expire_at": expire_at
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    except DuplicateKeyError:
        result = request_windows.find_one_and_update(
            {
                "ip": ip,
                "window_start": window_start
            },
            {"$inc": {"count": 1}},
            return_document=ReturnDocument.AFTER
        )

    return result["count"]



def check_request(ip):
    if not ip or ip == "unknown":
        return False, "Unable to identify visitor IP"

    if is_blocked(ip):
        return False, "IP address is blocked"

    count = count_request(ip)

    if count > REQUEST_LIMIT:
        auto_block(
            ip,
            f"Exceeded {REQUEST_LIMIT} requests "
            f"in {WINDOW_SECONDS} seconds"
        )

        return False, "Request limit exceeded"

    return True, "Request allowed"



def manual_block(ip, reason="Manually blocked by administrator"):
    if not ip:
        raise ValueError("IP address is required")

    now = utc_now()

    blocked_ips.update_one(
        {"ip": ip},
        {
            "$set": {
                "ip": ip,
                "reason": reason,
                "blocked_at": now,
                "manual": True
            },
            "$unset": {"expire_at": ""}
        },
        upsert=True
    )


def unblock_ip(ip):
    result = blocked_ips.delete_one({"ip": ip})
    return result.deleted_count > 0
