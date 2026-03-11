import mesop as me
from dataclasses import field
import requests
from db import (
    register_user, authenticate_user, create_reservation,
    get_user_reservations, update_reservation, delete_reservation, get_reservation
)

# Backend service URL
BACKEND_URL = "http://localhost:8000/notify"

@me.stateclass
class State:
    # Auth
    is_logged_in: bool = False
    user_id: str = ""
    username_input: str = ""
    password_input: str = ""
    auth_message: str = ""
    is_signup_mode: bool = False

    # Navigation
    current_page: str = "home" # home, form

    # Form
    form_mode: str = "create" # create, edit
    edit_reservation_id: str = ""

    project_name: str = ""
    allowed_users: str = ""
    job_count: int = 0
    start_date: str = ""
    expire_date: str = ""

    form_message: str = ""

    # Data
    reservations: list[dict] = field(default_factory=list)

def notify_backend(action, data):
    try:
        payload = {
            "action": action,
            "project_name": data.get("project_name", ""),
            "user_id": data.get("user_id", ""),
            "job_count": data.get("job_count", 0),
            "start_date": data.get("start_date", ""),
            "expire_date": data.get("expire_date", ""),
            "allowed_users": data.get("allowed_users", "")
        }
        requests.post(BACKEND_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Error notifying backend: {e}")

# Event Handlers

def on_input_change(e: me.InputEvent):
    state = me.state(State)
    setattr(state, e.key, e.value)

def on_number_change(e: me.InputEvent):
    state = me.state(State)
    try:
        setattr(state, e.key, int(e.value))
    except ValueError:
        setattr(state, e.key, 0)

def toggle_signup_mode(e: me.ClickEvent):
    state = me.state(State)
    state.is_signup_mode = not state.is_signup_mode
    state.auth_message = ""

def on_login(e: me.ClickEvent):
    state = me.state(State)
    if not state.username_input or not state.password_input:
        state.auth_message = "Please enter both username and password."
        return

    user_id = authenticate_user(state.username_input, state.password_input)
    if user_id:
        state.is_logged_in = True
        state.user_id = user_id
        state.auth_message = ""
        state.password_input = ""
        load_reservations()
    else:
        state.auth_message = "Invalid username or password."

def on_signup(e: me.ClickEvent):
    state = me.state(State)
    if not state.username_input or not state.password_input:
        state.auth_message = "Please enter both username and password."
        return

    success, message = register_user(state.username_input, state.password_input)
    state.auth_message = message
    if success:
        state.is_signup_mode = False

def on_logout(e: me.ClickEvent):
    state = me.state(State)
    state.is_logged_in = False
    state.user_id = ""
    state.username_input = ""
    state.current_page = "home"

def load_reservations():
    state = me.state(State)
    if state.user_id:
        state.reservations = get_user_reservations(state.user_id)

def go_to_create(e: me.ClickEvent):
    state = me.state(State)
    state.current_page = "form"
    state.form_mode = "create"
    state.edit_reservation_id = ""
    state.project_name = ""
    state.allowed_users = ""
    state.job_count = 0
    state.start_date = ""
    state.expire_date = ""
    state.form_message = ""

def go_to_edit(e: me.ClickEvent):
    state = me.state(State)
    res_id = e.key
    res = get_reservation(res_id)
    if res and res['user_id'] == state.user_id:
        state.current_page = "form"
        state.form_mode = "edit"
        state.edit_reservation_id = res_id
        state.project_name = res['project_name']
        state.allowed_users = res['allowed_users']
        state.job_count = res['job_count']
        state.start_date = res['start_date']
        state.expire_date = res['expire_date']
        state.form_message = ""

def go_back(e: me.ClickEvent):
    state = me.state(State)
    state.current_page = "home"
    load_reservations()

def on_submit_reservation(e: me.ClickEvent):
    state = me.state(State)

    if not state.project_name or not state.start_date or not state.expire_date:
        state.form_message = "Please fill in all required fields."
        return

    if state.form_mode == "create":
        res, message = create_reservation(
            state.user_id, state.project_name, state.allowed_users,
            state.job_count, state.start_date, state.expire_date
        )
        if res:
            state.form_message = message
            notify_backend("created", res)
            go_back(e)
        else:
            state.form_message = message
    else:
        res, message = update_reservation(
            state.edit_reservation_id, state.user_id, state.project_name,
            state.allowed_users, state.job_count, state.start_date, state.expire_date
        )
        if res:
            state.form_message = message
            notify_backend("updated", res)
            go_back(e)
        else:
            state.form_message = message

def on_delete_reservation(e: me.ClickEvent):
    state = me.state(State)
    res_id = e.key
    success, res = delete_reservation(res_id, state.user_id)
    if success:
        notify_backend("deleted", res)
        load_reservations()

# UI Components

def render_auth_page():
    state = me.state(State)
    with me.box(style=me.Style(
        display="flex",
        flex_direction="column",
        align_items="center",
        margin=me.Margin.all(40)
    )):
        me.text("Resource Reservation System", type="headline-3")
        with me.box(style=me.Style(
            display="flex", flex_direction="column", gap=16,
            padding=me.Padding.all(24),
            border=me.Border.all(me.BorderSide(width=1, color="#e0e0e0", style="solid")),
            border_radius=8,
            width=300
        )):
            title = "Sign Up" if state.is_signup_mode else "Login"
            me.text(title, type="headline-5")

            me.input(label="Username", key="username_input", on_blur=on_input_change, value=state.username_input)
            me.input(label="Password", key="password_input", on_blur=on_input_change, type="password", value=state.password_input)

            if state.auth_message:
                me.text(state.auth_message, style=me.Style(color="red" if "Invalid" in state.auth_message or "exists" in state.auth_message else "green"))

            if state.is_signup_mode:
                me.button("Register", on_click=on_signup, type="flat")
                me.button("Back to Login", on_click=toggle_signup_mode)
            else:
                me.button("Login", on_click=on_login, type="flat")
                me.button("Create Account", on_click=toggle_signup_mode)

def render_home_page():
    state = me.state(State)
    with me.box(style=me.Style(padding=me.Padding.all(24))):
        with me.box(style=me.Style(display="flex", justify_content="space-between", margin=me.Margin(bottom=24))):
            me.text(f"Welcome, {state.username_input}", type="headline-4")
            me.button("Logout", on_click=on_logout)

        me.button("Create New Request", on_click=go_to_create, type="flat")

        me.text("Your Reservations", type="headline-5", style=me.Style(margin=me.Margin(top=24, bottom=16)))

        if not state.reservations:
            me.text("No reservations found.")
        else:
            for res in state.reservations:
                with me.box(style=me.Style(
                    border=me.Border.all(me.BorderSide(width=1, color="#ccc", style="solid")),
                    border_radius=8,
                    padding=me.Padding.all(16),
                    margin=me.Margin(bottom=16),
                    display="flex",
                    justify_content="space-between",
                    align_items="center"
                )):
                    with me.box():
                        me.text(res['project_name'], style=me.Style(font_weight="bold"))
                        me.text(f"Dates: {res['start_date']} to {res['expire_date']}")
                        me.text(f"Jobs: {res['job_count']}")
                        me.text(f"Allowed Users: {res['allowed_users']}")

                    with me.box(style=me.Style(display="flex", gap=8)):
                        me.button("Edit", on_click=go_to_edit, key=res['_id'])
                        me.button("Delete", on_click=on_delete_reservation, key=res['_id'], style=me.Style(color="red"))

def render_form_page():
    state = me.state(State)
    with me.box(style=me.Style(padding=me.Padding.all(24))):
        me.button("Back to Manage", on_click=go_back)

        title = "Create Reservation" if state.form_mode == "create" else "Edit Reservation"
        me.text(title, type="headline-4", style=me.Style(margin=me.Margin(top=16, bottom=24)))

        with me.box(style=me.Style(display="flex", flex_direction="column", gap=16, width=400)):
            me.input(label="Project Name *", key="project_name", on_blur=on_input_change, value=state.project_name)
            me.input(label="Allowed Users (comma-separated)", key="allowed_users", on_blur=on_input_change, value=state.allowed_users)
            me.input(label="Job Count *", key="job_count", on_blur=on_number_change, value=str(state.job_count) if state.job_count else "0", type="number")
            me.input(label="Start Date (YYYY-MM-DD) *", key="start_date", on_blur=on_input_change, value=state.start_date)
            me.input(label="Expire Date (YYYY-MM-DD) *", key="expire_date", on_blur=on_input_change, value=state.expire_date)

            if state.form_message:
                me.text(state.form_message, style=me.Style(color="red" if "exceeded" in state.form_message or "must be" in state.form_message or "Invalid" in state.form_message or "Please" in state.form_message else "green"))

            me.button("Submit", on_click=on_submit_reservation, type="flat")

@me.page(path="/", stylesheets=["/fonts.css"])
def app():
    state = me.state(State)
    if not state.is_logged_in:
        render_auth_page()
    else:
        if state.current_page == "home":
            render_home_page()
        elif state.current_page == "form":
            render_form_page()
