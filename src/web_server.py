#-*- coding: utf-8 -*-    
'''
Created on 2012-07-13

@author: jf
'''

from twisted.web import server, resource, static
from twisted.internet import reactor
import json
import hashlib

class Template:
    
    def __init__(self):
        self.nMenuItem = 3
        with open("web/template.html") as fd:
            self.content = fd.read()
    
    def get(self, activeMenuIdx, content ):
        formatParam = ['']*self.nMenuItem
        formatParam[activeMenuIdx] = 'class="active"'
        return self.content%tuple(formatParam+[content])
        
template = Template()
config = open('web/config.html').read()
select_schedule = open('web/select_schedule.html').read()

class HappyLeagueResource(resource.Resource):
    isLeaf = False
    
    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)
        
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        
        return template.get(0, select_schedule)
    

class TestResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return "Test réussi!"
    
    def render_POST(self, request):
        request.setHeader("content-type", "application/json")
        name = request.args["name"][0]
        return_dict = {"greeting": "Hello, ", "name": name, "hash": ", " + hashlib.md5(name).hexdigest()}
        return json.dumps(return_dict)


class ConfigResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(1, config)
    
class SelectScheduleResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(0, select_schedule)
    

root = HappyLeagueResource()
root.putChild("bootstrap", static.File("web/bootstrap"))
root.putChild("js", static.File("web/js/"))
root.putChild("test", TestResource())
root.putChild("config", ConfigResource())
root.putChild("selectSchedule", SelectScheduleResource())

reactor.listenTCP(8080, server.Site(root))
reactor.run()