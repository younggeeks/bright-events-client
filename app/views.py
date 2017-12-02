from functools import wraps

from flask import render_template, flash, redirect, request, url_for, session, json

from app import application
import requests


BASE_URL = "http://localhost:5000/api/v1"


def protected_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@application.route("/")
def index():
    res = requests.get("{}/events".format(BASE_URL)).json()
    return render_template("index.html", events=res.get("events"))


@application.route("/dashboard")
@protected_route
def dashboard():
    res = requests.get("{}/events".format(BASE_URL)).json()

    graphresp = requests.get("{}/events/{}/charts".format(BASE_URL, session["username"]))

    if graphresp.status_code == 200:
        categories = graphresp.json()["categories"]
        counts = graphresp.json()["count"]

        return render_template("dashboard.html", events=res.get("events"), graphs={
            "categories": categories,
            "counts": counts
        })

    return render_template("dashboard.html", events=res.get("events"), graphs=None)


@application.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        res = requests.post("{}/auth/login".format(BASE_URL), json={
            "email": email,
            "password": password
        })
        response = res.json()
        if res.status_code == 200:
            return create_session(response)
        elif res.status_code == 401:
            flash(format(response["message"]))
            return redirect(url_for("login"))
    return render_template("login.html", title="Log In")


@application.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")

        res = requests.post("{}/auth/register".format(BASE_URL), json={
            "email": email,
            "password": password,
            "full_name": full_name
        })
        response = res.json()
        if res.status_code == 201:
            return create_session(response)
        elif res.status_code == 400:
            flash(format(response["message"]))
            return redirect(url_for("signup"))
    return render_template("signup.html")


def create_session(response):
    session["username"] = response["user"]["full_name"]
    session["id"] = response["user"]["id"]
    flash("Login Successfully")
    return redirect(url_for("dashboard"))


@application.route("/logout", methods=["GET"])
def logout():
    if "username" in session:
        session.pop("username")
    if "id" in session:
        session.pop("id")
    flash("Successfully Logged Out")
    return redirect(url_for("login"))


@application.route("/create-event", methods=["GET", "POST"])
@protected_route
def create_event():

    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        price = request.form.get("price")
        category = request.form.get("category")
        description = request.form.get("description")

        res = requests.post("{}/events".format(BASE_URL), json={
            "name": name,
            "address": address,
            "start_date": start_date,
            "end_date": end_date,
            "price": price,
            "category": category,
            "description": description,
            "user": session["username"]
        })
        response = res.json()
        print(response)
        if res.status_code == 201:
            flash(format(response["message"]))
            return redirect(url_for("get_my_events"))
        elif res.status_code == 400:
            flash(format(response["message"]))
            return redirect(url_for("create_event"))

    return render_template("add-event.html")


@application.route("/edit-event/<event_id>", methods=["GET", "POST"])
@protected_route
def edit_event(event_id=""):
    if event_id == "":
        flash("ID is not found")
        return redirect(url_for("get_my_events"))
    if request.method == "POST":
        print("We surely are puttin gthings up")
        name = request.form.get("name")
        address = request.form.get("address")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        price = request.form.get("price")
        category = request.form.get("category")
        description = request.form.get("description")

        print(request.form)

        res = requests.put("{}/events/{}".format(BASE_URL, event_id), json={
            "name": name,
            "address": address,
            "start_date": start_date,
            "end_date": end_date,
            "price": price,
            "category": category,
            "description": description,
            "user": session["username"]
        })
        response = res.json()

        if res.status_code == 200:
            print("We've got something ogin")
            flash(format(response["message"]))
            return redirect(url_for("get_my_events"))
        elif res.status_code == 400:
            flash(format(response["message"]))
            return redirect(url_for("create_event"))

    res = requests.get("{}/events/{}".format(BASE_URL, event_id))

    if res.status_code == 404:
        flash("ID is not found")
        return redirect(url_for("get_my_events"))

    return render_template("edit-event.html", event=res.json()["event"])


@application.route("/my-events/delete/<event_id>", methods=['GET'])
@protected_route
def delete_event(event_id):
    if event_id == "":
        flash("ID is not found")
        return redirect(url_for("get_my_events"))

    res = requests.delete("{}/events/{}".format(BASE_URL, event_id))

    if res.status_code == 404:
        flash("{}".format(res.json()['message']))
        return redirect(url_for("get_my_events"))

    return redirect(url_for("get_my_events"))


@application.route("/my-events", methods=["GET"])
@protected_route
def get_my_events():

    res = requests.get("{}/{}/events".format(BASE_URL, session["username"]))
    print(res.json())
    if "events" in res.json():
        found_events = res.json()["events"]
        total_events = len(res.json()["events"])
    else:
        found_events = []
        total_events = 0

    return render_template("my_events.html", events=found_events, count=total_events)


@application.route("/events/show/<event_id>", methods=["GET"])
def view_event(event_id):
    if event_id == "":
        flash("ID is not found")
        return redirect(url_for("get_my_events"))

    res = requests.get("{}/events/{}".format(BASE_URL, event_id))

    guests_resp = requests.get("{}/events/{}/guests".format(BASE_URL, event_id))

    if guests_resp.status_code == 200:
        if guests_resp.json()["attendees"] is None:
            attendees = []
        if guests_resp.json()["attendees"] is not None:
            attendees = guests_resp.json()["attendees"]

    if res.status_code == 404:
        flash("{}".format(res.json()['message']))
        return redirect(url_for("get_my_events"))

    return render_template("view_event.html", event=res.json()["event"], guests=attendees)


@application.route("/category/<string:category>")
def filter_by_category(category):
    if category == "":
        flash("ID is not found")
        return redirect(url_for("index"))

    res = requests.get("{}/events/search/{}".format(BASE_URL, category))

    if res.status_code == 404:
        flash("{}".format(res.json()['message']))
        return redirect(url_for("get_my_events"))

    return render_template("view_event.html", event=res.json()["event"])


@application.route("/events/<event_id>")
def get_single_event(event_id):
    print(event_id)


