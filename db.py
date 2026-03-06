import os
import bcrypt
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client['resource_reservation']

# Collections
users_collection = db['users']
reservations_collection = db['reservations']

# Maximum jobs limit
MAX_JOBS = 100

def init_db():
    # Create indexes for better performance
    users_collection.create_index("username", unique=True)
    reservations_collection.create_index("user_id")
    reservations_collection.create_index("start_date")
    reservations_collection.create_index("expire_date")

def register_user(username, password):
    if users_collection.find_one({"username": username}):
        return False, "Username already exists."

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = {
        "username": username,
        "password": hashed_password.decode('utf-8'),
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(user)
    return True, "User registered successfully."

def authenticate_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return str(user['_id'])
    return None

def check_job_availability(start_date, expire_date, requested_jobs, exclude_reservation_id=None):
    """
    Validates if the requested_jobs plus existing jobs in any overlapping day
    exceeds the MAX_JOBS limit.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        expire_dt = datetime.strptime(expire_date, "%Y-%m-%d")
        if start_dt > expire_dt:
            return False, "Start date cannot be after expire date."
    except ValueError:
         return False, "Invalid date format. Use YYYY-MM-DD."

    # Find all reservations that overlap with the requested period
    # A reservation overlaps if its start <= requested_expire AND its expire >= requested_start
    query = {
        "start_date": {"$lte": expire_date},
        "expire_date": {"$gte": start_date}
    }
    if exclude_reservation_id:
        query["_id"] = {"$ne": ObjectId(exclude_reservation_id)}

    overlapping_reservations = list(reservations_collection.find(query))

    # Simple check: calculate total jobs in the overlapping reservations.
    # Note: To be perfectly precise per day, we'd iterate over each day in the requested range.
    # Since we're doing a simple overlap check, we'll check each day in the range.

    import datetime as dt
    delta = expire_dt - start_dt
    for i in range(delta.days + 1):
        current_day = start_dt + dt.timedelta(days=i)
        current_day_str = current_day.strftime("%Y-%m-%d")

        daily_total = requested_jobs
        for res in overlapping_reservations:
            res_start = datetime.strptime(res['start_date'], "%Y-%m-%d")
            res_expire = datetime.strptime(res['expire_date'], "%Y-%m-%d")

            if res_start <= current_day <= res_expire:
                daily_total += res['job_count']

        if daily_total > MAX_JOBS:
            return False, f"Job limit exceeded on {current_day_str}. Requested + Existing = {daily_total} (Max: {MAX_JOBS})"

    return True, "Jobs are available."

def create_reservation(user_id, project_name, allowed_users, job_count, start_date, expire_date):
    if job_count <= 0:
        return None, "Job count must be greater than 0."

    is_available, message = check_job_availability(start_date, expire_date, job_count)
    if not is_available:
        return None, message

    reservation = {
        "user_id": user_id,
        "project_name": project_name,
        "allowed_users": allowed_users,
        "job_count": job_count,
        "start_date": start_date,
        "expire_date": expire_date,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = reservations_collection.insert_one(reservation)
    reservation['_id'] = str(result.inserted_id)
    return reservation, "Reservation created successfully."

def get_user_reservations(user_id):
    reservations = list(reservations_collection.find({"user_id": user_id}))
    for res in reservations:
        res['_id'] = str(res['_id'])
    return reservations

def get_reservation(reservation_id):
    try:
        res = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
        if res:
            res['_id'] = str(res['_id'])
        return res
    except:
        return None

def update_reservation(reservation_id, user_id, project_name, allowed_users, job_count, start_date, expire_date):
    if job_count <= 0:
        return None, "Job count must be greater than 0."

    # Verify ownership
    existing = get_reservation(reservation_id)
    if not existing or existing['user_id'] != user_id:
        return None, "Reservation not found or access denied."

    is_available, message = check_job_availability(start_date, expire_date, job_count, exclude_reservation_id=reservation_id)
    if not is_available:
        return None, message

    update_data = {
        "project_name": project_name,
        "allowed_users": allowed_users,
        "job_count": job_count,
        "start_date": start_date,
        "expire_date": expire_date,
        "updated_at": datetime.utcnow()
    }

    reservations_collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": update_data}
    )

    updated_reservation = get_reservation(reservation_id)
    return updated_reservation, "Reservation updated successfully."

def delete_reservation(reservation_id, user_id):
    # Verify ownership
    existing = get_reservation(reservation_id)
    if not existing or existing['user_id'] != user_id:
        return False, None

    reservations_collection.delete_one({"_id": ObjectId(reservation_id)})
    return True, existing

# Export functions for import
__all__ = [
    'init_db',
    'register_user',
    'authenticate_user',
    'create_reservation',
    'get_user_reservations',
    'get_reservation',
    'update_reservation',
    'delete_reservation'
]
