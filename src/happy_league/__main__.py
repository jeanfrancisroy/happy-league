import os
import socket
import threading

import cherrypy
import webview

from happy_league.cherryPyServer.server import workFolder, ScheduleServer

def find_free_port():
    """Find an available TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))  # bind to free port assigned by OS
    addr, port = s.getsockname()
    s.close()
    return port


def start_cherrypy(port):
    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': port,
        'engine.autoreload.on': False,   # disable dev reloader
    })

    static_dir = os.path.dirname(os.path.abspath(__file__)) + '/cherryPyServer' + os.path.sep
    cherrypy.quickstart(ScheduleServer(workFolder),
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
    webview.create_window("Happy League", f"http://127.0.0.1:{port}")
    webview.start(gui="qt")


if __name__ == "__main__":
    main()
