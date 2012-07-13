'''
Created on 2011-11-03

@author: alexandre
'''
import sys
sys.stdout = sys.stderr

from os import path
projectDir = path.dirname( __file__ )
sys.path = [projectDir, path.join( projectDir, '..' )] + sys.path

import atexit
import cherrypy
from server import ScheduleServer, workFolder

cherrypy.config.update({'environment': 'embedded'})


if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
    cherrypy.engine.start(blocking=False)
    atexit.register(cherrypy.engine.stop)

#class Root(object):
#    def index(self):
#        return '<br/>'.join( sys.path ) 
#    index.exposed = True

config = {'/': {'tools.encode.on': True, 'tools.encode.encoding': "utf-8"}}
cherrypy.response.headers['Content-Type'] = "text/html; charset=utf-8"

application = cherrypy.Application(ScheduleServer(workFolder), script_name=None, config=config)
#application = cherrypy.Application(Root(), script_name=None, config=None)