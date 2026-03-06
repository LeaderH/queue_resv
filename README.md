# Resource Reservation System

This is a Python-based web application built with **Mesop** and **MongoDB** that allows users to fill out requests for reserving computing resources within a specific time window.

## Features

- **User Authentication:** Users can register and log in securely (passwords hashed via bcrypt).
- **Resource Request Management:** Users can create, view, edit, and delete their past computing resource requests.
- **Form Fields:** Requires project name, allowed users, job count, start date, and expire date.
- **Resource Validation:** Validates overlapping reservations to ensure that the total jobs on any given day do not exceed the hard-coded maximum limit of 100.
- **Backend Notifications:** A secondary lightweight Python backend service (FastAPI) listens for any database updates and triggers a mock email to an administrator.
- **Database Storage:** All user and reservation data is stored securely in a MongoDB instance.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (to run the local MongoDB instance)

## Installation & Setup

1. **Start the MongoDB Database:**
   ```bash
   docker-compose up -d
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Backend Notification Service:**
   Start the FastAPI server in a separate terminal to listen for reservation updates.
   ```bash
   python backend.py
   ```

4. **Run the Mesop Web Application:**
   Start the frontend application.
   ```bash
   mesop main.py
   ```
   Open your browser and navigate to `http://localhost:32123` to access the application.

## Architecture

- `main.py`: Contains the Mesop UI, State management, and HTTP requests to the backend.
- `db.py`: Handles connection to MongoDB, authentication, resource availability calculations, and CRUD operations.
- `backend.py`: A simple FastAPI server that receives notification payloads and logs mock emails to the console.
- `docker-compose.yml`: Spins up the local `mongo:latest` instance.
