#-*- coding: utf-8 -*-    
'''
Created on 2012-07-13

@author: jf
'''

from twisted.web import server, resource, static
from twisted.internet import reactor
import json
import hashlib

# Preload html files
config = open('web/config.html').read()
config_fields = open('web/config_fields.html').read()
select_schedule = open('web/select_schedule.html').read()
generate_schedule = open('web/generate_schedule.html').read()


class Template:
    
    def __init__(self):
        with open("web/template.html") as fd:
            self.content = fd.read()
    
    def get(self, content ):
        pages_dict = {
                      "[!main_content!]": content,
                      "[!config_fields!]": config_fields,
                      "[!config_teams!]": "",
                      "[!config_restrictions!]": "",
                      }
        
        old_content = ""
        new_content = self.content
        
        while (new_content != old_content):
            old_content = new_content
            
            for (key, value) in pages_dict.iteritems():
                new_content = new_content.replace(key, value)
            
        return new_content
        
template = Template()

class HappyLeagueResource(resource.Resource):
    isLeaf = False
    
    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)
        
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        
        return template.get(select_schedule)
    

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
        return template.get(config)
    
    
class SelectScheduleResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(select_schedule)
    
    
class GenerateScheduleResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(generate_schedule)
    

root = HappyLeagueResource()

# Static childs
root.putChild("bootstrap", static.File("web/bootstrap"))
root.putChild("slick", static.File("web/slick"))
root.putChild("js", static.File("web/js/"))

# Dynamic childs
root.putChild("test", TestResource())
root.putChild("selectSchedule", SelectScheduleResource())
root.putChild("config", ConfigResource())
root.putChild("generateSchedule", GenerateScheduleResource())

reactor.listenTCP(8080, server.Site(root))
reactor.run()