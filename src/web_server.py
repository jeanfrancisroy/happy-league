#-*- coding: utf-8 -*-    
'''
Created on 2012-07-13

@author: jf
'''

from twisted.web import server, resource, static
from twisted.internet import reactor
import json
import math

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
    
    def render_POST(self, request):
        request.setHeader("content-type", "application/json")
        test_dict = {"text": "Allo", "chiffre": math.pi}
        return json.dumps(test_dict)

class Config(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        request.setHeader("content-type", "text/html")
        return template.get(1,config)
    
config="""
    <div id="content">
        <ul class="nav nav-tabs nav-stacked" data-tabs="tabs">
            <li class="active"><a href="#red">Red</a></li>
            <li><a href="#orange">Orange</a></li>
            <li><a href="#yellow">Yellow</a></li>
            <li><a href="#green">Green</a></li>
            <li><a href="#blue">Blue</a></li>
        </ul>
        <div id="my-tab-content" class="tab-content">
            <div class="tab-pane active" id="red">
                <h1>Red</h1>
                <p>red red red red red red</p>
            </div>
            <div class="tab-pane" id="orange">
                <h1>Orange</h1>
                <p>orange orange orange orange orange</p>
            </div>
            <div class="tab-pane" id="yellow">
                <h1>Yellow</h1>
                <p>yellow yellow yellow yellow yellow</p>
            </div>
            <div class="tab-pane" id="green">
                <h1>Green</h1>
                <p>green green green green green</p>
            </div>
            <div class="tab-pane" id="blue">
                <h1>Blue</h1>
                <p>blue blue blue blue blue</p>
            </div>
        </div>
    </div>
 
    <script type="text/javascript" src="http://code.jquery.com/jquery.min.js"></script>
    <script type="text/javascript" src="http://twitter.github.com/bootstrap/1.4.0/bootstrap-tabs.js"></script>
    <script type="text/javascript">
        jQuery(document).ready(function ($) {
            $(".tabs").tabs();
        });
    </script>
"""

root = HappyLeagueResource()
root.putChild("bootstrap", static.File("web/bootstrap"))
root.putChild("js", static.File("web/js/"))
root.putChild("test", TestResource())
root.putChild("config",Config())
root.putChild("selectSchedule",HappyLeagueResource())

reactor.listenTCP(8080, server.Site(root))
reactor.run()