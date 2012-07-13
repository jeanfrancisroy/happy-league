#-*- coding: utf-8 -*-    
'''
Created on 2012-07-13

@author: jf
'''

from twisted.web import server, resource, static
from twisted.internet import reactor
import json
import hashlib

hello = """
<div class="span9">
 <div class="hero-unit">
   <h1>Hello, world!</h1>
   <p>Enter your name:</p>
   <input id="txt_name" type="text" value="Test!" />
   <p><a class="btn btn-primary btn-large" onclick="test_function($(txt_name).val())">Learn more &raquo;</a></p>
   <div id="div_result"></div>
 </div>
 
<ul class="nav nav-tabs nav-stacked nav-pills" id="myTab">
  <li class="active"><a href="#home">Home</a></li>
  <li><a href="#profile">Profile</a></li>
  <li><a href="#messages">Messages</a></li>
  <li><a href="#settings">Settings</a></li>
</ul>
 
<div class="tab-content">
  <div class="tab-pane active" id="home">...</div>
  <div class="tab-pane" id="profile">...2</div>
  <div class="tab-pane" id="messages">...3</div>
  <div class="tab-pane" id="settings">...4</div>
</div>
 
<script>

</script>

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
    
    def render_POST(self, request):
        request.setHeader("content-type", "application/json")
        name = request.args["name"][0]
        return_dict = {"greeting": "Hello, ", "name": name, "hash": ", " + hashlib.md5(name).hexdigest()}
        return json.dumps(return_dict)

class Config(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(1,'config')
    


root = HappyLeagueResource()
root.putChild("bootstrap", static.File("web/bootstrap"))
root.putChild("js", static.File("web/js/"))
root.putChild("test", TestResource())
root.putChild("config",Config())
root.putChild("selectSchedule",HappyLeagueResource())

reactor.listenTCP(8080, server.Site(root))
reactor.run()