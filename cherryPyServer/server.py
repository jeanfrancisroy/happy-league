"""
Created on 2011-11-03

@author: alexandre
"""
from __future__ import unicode_literals
import cherrypy
from util import read_pickle
import htmlView
from os import path
import subprocess as sp
import os

workFolder = '/tmp/happy-league'
makeSchedulePath = path.join(path.dirname(__file__), '..', "makeSchedule.py")

try:
    os.makedirs(workFolder)
except OSError:
    pass


class ScheduleServer(object):
    def __init__(self, workFolder=None):
        self.workFolder = workFolder
        self.schPath = path.join(workFolder, 'sch.pkl')
        self.subProcess = None
        self.sig = None

    @cherrypy.expose
    def index(self):
        menu = """\
            <html>
            <head>
            <title>Happy League</title>
            <link href="/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                {}
            </body>
            </html>
            """.format(htmlView.HtmlMenu().__html__())
        return menu

    @cherrypy.expose
    def new(self):
        if self.subProcess is not None:  # may be running
            if self.subProcess.poll() is None:  # is running

                return """
                <html>
                <head>
                <link href="/css/bootstrap.min.css" rel="stylesheet">
                <link href="/css/bootstrap-theme.min.css" rel="stylesheet">
                </head>
                <body>
                    {}
                    <div class="container">
                        Currently running.
                        <br/>
                        <a href="stop">stop</a>
                    </div>
                </body></html>
                """.format(htmlView.HtmlMenu().__html__())
            else:
                code = self.subProcess.poll()
                self.subProcess = None
                self.sentSig = None
                return """
                last process ended with code %d
                """ % code

        return """
        <html>
        <head>
        <link href="/css/bootstrap.min.css" rel="stylesheet">
        <link href="/css/bootstrap-theme.min.css" rel="stylesheet">
        </head>
        <body>
            {}
            <div class="container" role="main">
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
            </div>
        </body></html>
        """.format(htmlView.HtmlMenu().__html__())

    @cherrypy.expose
    def stop(self):
        if self.subProcess is not None:  # may be running
            if self.subProcess.poll() is None:  # is running
                self.subProcess.terminate()
                self.sentSig = 'SIGTERM'
                return "Sent the terminate signal."
            else:
                code = self.subProcess.poll()
                self.subProcess = None
                self.sentSig = None
                return "process ended with code %d" % code
        else:
            return "no process was running"

    @cherrypy.expose
    def upload(self, myFile, minutes):

        print('upload')
        filePath = path.join(self.workFolder, 'xlsConfig.xls')
        with open(filePath, 'wb') as fd:
            while True:
                data = myFile.file.read(8192)
                if not data:
                    break
                fd.write(data)

        print('file Saved')
        print(' '.join([makeSchedulePath, self.workFolder, minutes]))

        self.subProcess = sp.Popen([makeSchedulePath, self.workFolder, minutes], stdout=open(path.join(self.workFolder, 'stdout'), 'w'))
        print('process started')
        return """
        <html>
        <head>
        <link href="/css/bootstrap.min.css" rel="stylesheet">
        <link href="/css/bootstrap-theme.min.css" rel="stylesheet">
        </head>
        <body>
            {}
            <div class="container" role="main">
                <h2>Started for {} minutes...</h2>
            </div>
        </body></html>
        """.format(htmlView.HtmlMenu().__html__(), minutes)

    def _formatStdout(self, name='stdout', **fontAttr):
        strL = []
        strL.append('<h2>%s</h2>' % name)

        file_path = os.path.join(self.workFolder, name)
        if os.path.exists(file_path):
            with open(file_path) as f:
                stdout = f.read()
                stdout = stdout.replace('\n', '</br>\n')
                stdout = stdout.replace(' ', '&nbsp;')
                strL.append(htmlView.HtmlTag('tt',  htmlView.Font(stdout, **fontAttr)).__html__())

        return strL

    @cherrypy.expose
    def debug(self):
        return """
        <html>
        <head>
        <link href="/css/bootstrap.min.css" rel="stylesheet">
        <link href="/css/bootstrap-theme.min.css" rel="stylesheet">
        </head>
        <body>
            {}
            <div class="container" role="main">
                {}
            </div>
        </body></html>
        """.format(htmlView.HtmlMenu().__html__(), '\n'.join(self._formatStdout() + self._formatStdout('stderr', color='red')))

    def _buildAnalysisPage(self, builder, refresh=False):
        if not path.exists(self.schPath):
            return "no schedule"
            return """
                <html>
                <head>
                <link href="/css/bootstrap.min.css" rel="stylesheet">
                <link href="/css/bootstrap-theme.min.css" rel="stylesheet">
                </head>
                <body>
                    {}
                    <div class="container" role="main">
                        No Schedule.
                    </div>
                </body></html>
        """.format(htmlView.HtmlMenu().__html__())

        config, matchL, optState = read_pickle(self.schPath)
        doc = htmlView.HtmlDoc(builder(config, matchL, optState))
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

current_dir = os.path.dirname(os.path.abspath(__file__)) + os.path.sep

if __name__ == "__main__":
    cherrypy.quickstart(ScheduleServer(workFolder),
                        config={
                            '/': {
                                'tools.staticdir.root': current_dir,
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
