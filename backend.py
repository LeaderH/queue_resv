from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Configure logging to simulate email sending
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service")

class ReservationNotification(BaseModel):
    action: str  # e.g., "created", "updated", "deleted"
    project_name: str
    user_id: str
    job_count: int
    start_date: str
    expire_date: str
    allowed_users: str

@app.post("/notify")
def notify_admin(notification: ReservationNotification):
    try:
        # Simulate sending an email to the admin
        subject = f"Reservation {notification.action.capitalize()}: {notification.project_name}"
        body = (
            f"Action: {notification.action.upper()}\n"
            f"User: {notification.user_id}\n"
            f"Project: {notification.project_name}\n"
            f"Job Count: {notification.job_count}\n"
            f"Start Date: {notification.start_date}\n"
            f"Expire Date: {notification.expire_date}\n"
            f"Allowed Users: {notification.allowed_users}\n"
        )

        logger.info(f"--- MOCK EMAIL TO ADMIN ---")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body:\n{body}")
        logger.info(f"---------------------------")

        return {"status": "success", "message": "Notification sent successfully"}
    except Exception as e:
        logger.error(f"Failed to process notification: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
