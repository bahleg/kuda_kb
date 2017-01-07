# -*- coding: utf-8 -*-
#http://www.akadia.com/services/ssh_test_certificate.html
from functools import wraps

from flask import Flask, request, make_response, redirect, render_template, url_for
import cherrypy
from flask_bootstrap import Bootstrap

from front.pass_storage import PassStorage

from back.logger import init_logger
import config
from back.categories import get_cats
from back.query_entity import  Query
from back.events import get_results_by_query
from back.rankers import load_w2v
import os
from back.geo import get_city
app = Flask('KUDABLYAT')

Bootstrap(app)
app.debug = True


def run_cherrypy_server():
    init_logger('kuda_proj', 'DEBUG')
    cherrypy.tree.graft(app, '/')
    port = int(config.server_port)
    # Set the configuration of the web server
    cherrypy.config.update({
        'engine.autoreload.on': False,
        'log.screen': True,
        'server.socket_port': port,
        'server.socket_host': '0.0.0.0',
	'server.ssl_module':'pyopenssl',
'server.ssl_certificate':'server.crt',
        'server.ssl_private_key':'server.key',
        'server.ssl_certificate_chain':'server.crt'
    })

    for command in config.geo_servers:
        print 'running', command
        os.system(config.geo_servers[command][0])
    load_w2v()
    cherrypy.engine.start()
    cherrypy.engine.block()

def atexit_func():
    os.system('killall -9 osrm-routed')



def auth_wrap(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        login = request.cookies.get('login', '')
        passwd = request.cookies.get('pass', '')
        if not PassStorage.is_user(login, passwd):
            return redirect(url_for('page_auth'))
        else:
            print args, kwargs
            return f(*args, **kwargs)

    return wrapped


@app.route('/logout', methods=['GET', 'POST'])
def page_logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('login', '')
    resp.set_cookie('pass', '')
    return resp


@app.route('/auth', methods=['GET', 'POST'])
def page_auth():
    if request.method == 'POST':
        form = request.form
        login = form['login']
        passwd = form['pass']
        if PassStorage.is_user(login, passwd):
            resp = make_response(redirect('/'))
            resp.set_cookie('login', login)
            resp.set_cookie('pass', passwd)
            return resp
        else:
            return render_template('auth.html')
    else:
        return render_template('auth.html')


@app.route('/test')
def test_page():
    return render_template('test.html')


@app.route('/query', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
@auth_wrap
def query():
    if request.method == 'GET':
        return render_template('query.html', cats=get_cats())
    else:
        form = request.form
        q = Query()
        q.lat=float(form['address'].split(';')[0])
        q.lon=float(form['address'].split(';')[1])
        q.tags = [t for t in form['tags'].split(' ') if len(t)>0][:config.max_tags]
        if 'use_car' in form:
            q.use_car = True
        else:
            q.use_car = False
        q.city = get_city(q)
        if 'search_events' in form or 'search_both' in form:
            q.search.add('events')
        if 'search_places'in form  or 'search_both' in form:
            q.search.add('places')

        all_cats = get_cats()
        for cat in form.getlist('cats'):
            q.cats.append(all_cats[cat])
        q.price = int(form['price'])
        q.time_to_travel = int(form['time_to_travel'])
        results = get_results_by_query(q)
        return render_template('result.html', results=results)


if __name__ == '__main__':
    import atexit
    atexit.register(atexit_func)
    run_cherrypy_server()
