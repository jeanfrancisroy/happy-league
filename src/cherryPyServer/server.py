'''
Created on 2011-11-03

@author: alexandre
'''
import cherrypy
from util import readPkl, readFile
import htmlView
from os import path
import subprocess as sp
import os

workFolder = '/tmp/happy-league'


makeSchedulePath = path.join( path.dirname( __file__ ), '..', "makeSchedule.py" )
try : os.makedirs(workFolder)
except OSError : pass




class ScheduleServer(object):
    
    def __init__(self,workFolder=None):
        self.workFolder = workFolder
        self.schPath = path.join( workFolder, 'sch.pkl') 
        self.subProcess = None
        self.sig = None
    
    @cherrypy.expose 
    def index(self):
        menu = """\
            <html>
            <head>
            <title>Happy League</title>
            </head>
            <body style="margin:0px;padding:0px">
                <table width="100%"  height="100%" border="0" cellpadding="0" cellspacing="0">
                    <tr>
                    <td style="width:10px;" valign="top" >
                        <br/>
                        <table border="0" cellpadding="5" cellspacing="0" style="padding-left:0.2cm" >
                        
                            <tr><td>
                            <a href="new" target="frame">New</a>
                            </td></tr>
                            
                            <tr><td>
                            <a href="config" target="frame">View Config</a>
                            </td></tr>
                            
                            <tr><td>
                            <a href="overview" target="frame">Overview</a>
                            </td></tr>
                            
                            <tr><td style="padding-left:0.5cm">
                            <a href="conflicts" target="frame">Conflicts</a>
                            </td></tr>
                            
                            <tr><td style="padding-left:0.5cm">
                            <a href="restrictions" target="frame">Restrictions</a>
                            </td></tr>
                            
                            <tr><td style="padding-left:0.5cm">
                            <a href="teamGrpConflicts" target="frame">Multi-team Conflicts</a>
                            </td></tr>
                            
                            <tr><td style="padding-left:0.5cm">
                            <a href="uniformity" target="frame">Uniformity</a>
                            </td></tr>
                            
                            <tr><td>
                            <a href="schedule" target="frame">Schedule</a>
                            </td></tr>
                            
                            <tr><td>
                            <a href="debug" target="frame">Debug</a>
                            </td></tr>
                            
                        </table>
                        </td>
                    <td >
                        <iframe  align="left" name="frame" src="new" frameborder="0" width="100%" height="100%" marginheight="10" marginwidth="10">
                          <p>Your browser does not support iframes.</p>
                        </iframe>
                    </td>
                    </tr>
                </table>
            </body>
            </html>        
            """
        return menu 
    
    @cherrypy.expose
    def new(self):
        if self.subProcess is not None: # may be running
            if self.subProcess.poll() is None: # is running
            
                return """
                <html><body>
                    Currently running.
                    <br/> 
                    <a href="stop">stop</a>
                </body></html>
                """
            else:
                code = self.subProcess.poll()
                self.subProcess = None
                self.sentSig= None
                return """
                last process ended with code %d
                """%code
                
        return """
        <html><body>
            <h2>Upload a file</h2>
            <form action="upload" method="post" enctype="multipart/form-data">
            <table cellpadding="3">
            <tr>
            <td align="right"> Configuration file </td> <td> <input type="file" name="myFile" /></td>
            </tr>
            <tr>
            <td align="right"> Runtime (minutes) </td> <td> <input type="text" name="minutes" /> </td>
            </tr>
            </table>
            </br>
            <input type="submit" />
            
            </form>
        </body></html>
        """
        
    @cherrypy.expose
    def stop(self):
        if self.subProcess is not None: # may be running
            if self.subProcess.poll() is None: # is running
                self.subProcess.terminate()
                self.sentSig= 'SIGTERM'
                return "Sent the terminate signal."
            else:
                code = self.subProcess.poll()
                self.subProcess = None
                self.sentSig = None
                return "process ended with code %d"%code
        else:
            return "no process was running"
        
    @cherrypy.expose
    def upload(self, myFile, minutes):
        
        print 'upload'
        
        filePath = path.join( self.workFolder, 'xlsConfig.xls')
        with open( filePath, 'w' ) as fd:          
            while True:
                data = myFile.file.read(8192)
                if not data: break
                fd.write(data)  
        
        print 'file Saved'
        
        print ' '.join( [makeSchedulePath, self.workFolder, minutes] )
#        stdoutFd = open(path.join(self.workFolder,'stdout'),'w')
#        stderrFd = open(path.join(self.workFolder,'stderr'),'w')
        
        self.subProcess = sp.Popen([makeSchedulePath, self.workFolder, minutes],
            stdout=open(path.join(self.workFolder,'stdout'),'w'))
        print 'process started'
        return "started for %s minutes"%(minutes) 
    
    
    def _formatStdout(self, name='stdout', **fontAttr ):
        strL = []
        strL.append( '<h2>%s</h2>'%name)
        stdout = readFile( self.workFolder, name )
        if stdout :
            stdout = stdout.replace('\n','</br>\n') 
            stdout = stdout.replace(' ','&nbsp;')
            strL.append( htmlView.HtmlTag( 'tt',  htmlView.Font( stdout, **fontAttr ) ).__html__() )
        return strL
        
    @cherrypy.expose
    def debug(self):
        return '\n'.join(self._formatStdout() + self._formatStdout('stderr',color='red'))
    
    def _buildAnalysisPage(self, builder, refresh=False):
        if not path.exists( self.schPath): return "no schedule"
        config, matchL, optState = readPkl(self.schPath)
        doc = htmlView.HtmlDoc( builder( config, matchL, optState) )
        if refresh:
            doc.head.add(htmlView.HtmlRefresh())
        return doc.__html__()
    
    @cherrypy.expose
    def overview(self):
        return self._buildAnalysisPage(htmlView.HtmlAnalysis)
    
    @cherrypy.expose
    def schedule(self):
        return self._buildAnalysisPage(htmlView.HtmlSchedule)
    
    @cherrypy.expose
    def conflicts(self):
        return self._buildAnalysisPage(htmlView.HtmlConflict)
    
    @cherrypy.expose
    def config(self):
        return self._buildAnalysisPage(htmlView.HtmlConfig)
    
    @cherrypy.expose
    def teamGrpConflicts(self):
        return self._buildAnalysisPage(htmlView.HtmlTeamGroup)
    
    @cherrypy.expose
    def uniformity(self):
        return self._buildAnalysisPage(htmlView.HtmlUniformity)
    
    @cherrypy.expose
    def restrictions(self):
        return self._buildAnalysisPage(htmlView.HtmlRestriction)
    
if __name__ == "__main__":
    cherrypy.quickstart(ScheduleServer(workFolder))
