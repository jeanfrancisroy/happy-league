import os
import socket
import tempfile
import threading
import multiprocessing as mp

import cherrypy
import webview

from happy_league.server.server import ScheduleServer


def find_free_port():
    """Find an available TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))  # bind to free port assigned by OS
    addr, port = s.getsockname()
    s.close()
    return port


def start_cherrypy(port):
    work_folder = tempfile.mkdtemp(prefix='happy-league-')

    try:
        os.makedirs(work_folder)
    except OSError:
        pass

    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': port,
        'engine.autoreload.on': False,   # disable dev reloader
    })

    static_dir = os.path.dirname(os.path.abspath(__file__)) + '/server' + os.path.sep
    cherrypy.quickstart(ScheduleServer(work_folder),
                        config={
                            '/': {
                                'tools.staticdir.root': static_dir,
                            },
                            '/css': {
                                'tools.staticdir.on': True,
                                'tools.staticdir.dir': 'static/css',
                            },
                            '/js': {
                                'tools.staticdir.on': True,
                                'tools.staticdir.dir': 'static/js',
                            },
                            '/fonts': {
                                'tools.staticdir.on': True,
                                'tools.staticdir.dir': 'static/fonts',
                            }
                        })


def main():
    port = find_free_port()

    # Run CherryPy in a background thread
    t = threading.Thread(target=start_cherrypy, args=(port,), daemon=True)
    t.start()

    # Start pywebview pointing to our CherryPy server
    webview.create_window("Happy League", f"http://127.0.0.1:{port}", text_select=True)
    webview.start(gui="qt")


if __name__ == "__main__":
    mp.freeze_support()
    main()
