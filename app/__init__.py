from functools import wraps

from flask import Flask, redirect, url_for, request, session
from flask_cors import CORS

application = Flask(__name__, instance_relative_config=True)

from app import views
CORS(application)
application.config.from_object('config')

