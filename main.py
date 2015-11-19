#!/usr/bin/env python

from flask import Flask, request, session, jsonify, redirect, url_for, abort, render_template, flash, Response, make_response
from flask.ext.cache import Cache

from jinja2 import Environment, PackageLoader, FileSystemLoader
from collections import OrderedDict
import os, json
import uuid
from protocol.protocol import Protocol


# CONFIG ===================================================================================

app = Flask(__name__) #APPLICATION
app.config.from_object(__name__)

app.secret_key = "protocol_editor" # encryption key for session variable, security isn't really an issue

# configure Jinja template engine
app.jinja_env.add_extension('jinja2.ext.do')
app.jinja_env.lstrip_blocks = True # strip the whitespace from jinja template lines
app.jinja_env.trim_blocks = True

cache = Cache(app, config={'CACHE_TYPE': 'simple'}) # initialize cache to store objects


# ROUTES ===================================================================================

@app.route('/')
def landing_page():
	
	uid = str(uuid.uuid4())
	session['session_id'] = uid

	session_id = session['session_id']
	print('session_id from landing_page:', session_id)
	
	# return render_template('body.html', filename='[empty]')	#modified rbw 8/26/15
	return render_template('body.html', filename='[empty]', savedFile=0, loadedFile=0)
