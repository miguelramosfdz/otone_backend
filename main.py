#!/usr/bin/env python

from flask import Flask, request, session, jsonify, redirect, url_for, abort, render_template, flash, Response, make_response
from flask.ext.cache import Cache

from jinja2 import Environment, PackageLoader, FileSystemLoader
from collections import OrderedDict
import os, json
import uuid


# CONFIG ===================================================================================

app = Flask(__name__) #APPLICATION
app.config.from_object(__name__)

app.secret_key = "opentrons" # encryption key for session variable, security isn't really an issue

# configure Jinja template engine
app.jinja_env.add_extension('jinja2.ext.do')
app.jinja_env.lstrip_blocks = True # strip the whitespace from jinja template lines
app.jinja_env.trim_blocks = True

cache = Cache(app, config={'CACHE_TYPE': 'simple'}) # initialize cache to store objects

# NEW STUFF ================================================================================

templates_html = []
templates_js = []
templates_sass_partials = []

def collect_templates():
	temp_path = os.path.dirname(otone_backend.__file__)
	temp_folder = os.path.join(temp_path, 'templates', 'modules')
	for f in os.listdir(temp_folder):
		t_path = os.path.join(temp_folder, f)
		if os.path.isdir(t_path):
			print('tempalte folder name',f)
			process_template_folder(t_path)


def process_template_folder(template_path):
	for f in os.listdir(template_path):
		t_path = os.path.join(template_path, f)
		print('t_path: ',t_path)
		if os.path.isdir(t_path) and t_path.endswith('sass'):
			print('sass folder found')
		elif os.path.isdir(t_path) and t_path.endswith('html'):
			print('html folder found')
		elif os.path.isdir(t_path) and t_path.endswith('json'):
			print('json folder found')


# ROUTES ===================================================================================

@app.route('/')
def landing_page():
	
	uid = str(uuid.uuid4())
	session['session_id'] = uid

	session_id = session['session_id']
	print('session_id from landing_page:', session_id)

	collect_templates()
	
	# return render_template('body.html', filename='[empty]')	#modified rbw 8/26/15
	return render_template('body.html', filename='[empty]', savedFile=0, loadedFile=0)


if __name__ == '__main__':
	app.run(debug=True)