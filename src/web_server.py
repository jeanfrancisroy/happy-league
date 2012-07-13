#-*- coding: utf-8 -*-    
'''
Created on 2012-07-13

@author: jf
'''

from twisted.web import server, resource, static
from twisted.internet import reactor

hello = """
<div class="span9">
 <div class="hero-unit">
   <h1>Hello, world!</h1>
   <p>This is a template for a simple marketing or informational website. It includes a large callout called the hero unit and three supporting pieces of content. Use it as a starting point to create something more unique.</p>
   <p><a class="btn btn-primary btn-large">Learn more &raquo;</a></p>
 </div>
 

</div><!--/span-->
"""


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

class HappyLeagueResource(resource.Resource):
    isLeaf = False
    
    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)
        
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        
        return template.get(0,hello)
    

class TestResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return "Test réussi!"
    

class Config(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(1,'config')
    


root = HappyLeagueResource()
root.putChild("bootstrap", static.File("web/bootstrap"))
root.putChild("test", TestResource())
root.putChild("config",Config())
root.putChild("selectSchedule",HappyLeagueResource())

reactor.listenTCP(8080, server.Site(root))
reactor.run()