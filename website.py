from flask import Flask, send_file, request, redirect, abort
import requests
import os
app = Flask(__name__)
banned_paths = [".py", ".php"]

@app.errorhandler(404)
def page_not_found(e):
    return send_file("404.html"), 404


@app.route('/')
def home_page():
    return send_file("index.html")


@app.route('/<path:filename>')
def getfile(filename):

    for x in range(len(banned_paths)):
        if banned_paths[x] in filename:
            return abort(404), 404

    if filename[-1] == "/":

        if os.path.isfile(filename + "index.html"):

            return send_file(filename + "index.html")

        else:

            return abort(404), 404

    elif "." not in filename:

        if os.path.isfile(filename + ".html"):

            return send_file(filename + ".html")

        else:

            return abort(404), 404
    else:

        if os.path.isfile(filename):

            return send_file(filename)

        else:

            return abort(404), 404


app.run(host='0.0.0.0', port=80, use_reloader=True)
