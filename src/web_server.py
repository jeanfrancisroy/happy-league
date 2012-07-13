#-*- coding: utf-8 -*-
'''
Created on 2012-07-13

@author: jf
'''

from twisted.web import server, resource, static
from twisted.internet import reactor
import json
import math

class HappyLeagueResource(resource.Resource):
    isLeaf = False
    
    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)
        
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        index_content = open("web/index.html").read()
        return index_content
    

class TestResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return "Test réussi!"
    
    def render_POST(self, request):
        request.setHeader("content-type", "application/json")
        test_dict = {"text": "Allo", "chiffre": math.pi}
        return json.dumps(test_dict)

root = HappyLeagueResource()
root.putChild("bootstrap", static.File("web/bootstrap"))
root.putChild("js", static.File("web/js/"))
root.putChild("test", TestResource())


reactor.listenTCP(8080, server.Site(root))
reactor.run()