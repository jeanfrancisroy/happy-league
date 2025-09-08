"""
Created on 2011-11-03

@author: alexandre
"""
import sys
import os
from os import path
import multiprocessing as mp

import cherrypy

from happy_league.server import htmlView
from happy_league.shared.util import read_pickle
from happy_league.make_schedule.makeSchedule import makeScheduleLeague


WEBPAGE_TEMPLATE = """
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
  </body>
</html>
"""


def html_page(content=""):
    return WEBPAGE_TEMPLATE.format(htmlView.HtmlMenu().__html__(), content)


class ScheduleServer(object):
    def __init__(self, workFolder):
        self.workFolder = workFolder
        self.schPath = path.join(workFolder, 'sch.pkl')
        self.subProcess = None
        self.sig = None

    @cherrypy.expose
    def index(self):
        return html_page()

    @cherrypy.expose
    def new(self):
        if self.subProcess is not None:  # may be running
            if self.subProcess.is_alive():
                stop = """
                    Currently running.
                    <br/>
                    <a href="stop">stop</a>
                """

                return html_page(stop)
            else:
                code = self.subProcess.exitcode
                self.subProcess = None
                self.sentSig = None
                return html_page("Last run finished with code %d" % code)

        upload_message = """
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
        """
        return html_page(upload_message)

    @cherrypy.expose
    def stop(self):
        if self.subProcess is not None:  # may be running
            if self.subProcess.is_alive():
                self.subProcess.terminate()
                self.sentSig = 'SIGTERM'
                return html_page("Sent the terminate signal.")
            else:
                code = self.subProcess.exitcode
                self.subProcess = None
                self.sentSig = None
                return html_page("Process ended with code %d" % code)
        else:
            return html_page("no process was running")

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


        self.subProcess = mp.Process(target=makeScheduleLeague, args=(self.workFolder, minutes))
        self.subProcess.start()

        print('process started')
        started = "<h2>Started for {} minutes...</h2>".format(minutes)
        return html_page(started)

    def _formatStdout(self, name='stdout', **fontAttr):
        strL = []
        strL.append('<h2>%s</h2>' % name)

        file_path = os.path.join(self.workFolder, name)
        sys.stdout.flush()
        sys.stderr.flush()
        if os.path.exists(file_path):
            with open(file_path) as f:
                stdout = f.read()
                stdout = stdout.replace('\n', '</br>\n')
                stdout = stdout.replace(' ', '&nbsp;')
                strL.append(htmlView.HtmlTag('tt',  htmlView.Font(stdout, **fontAttr)).__html__())

        return strL

    @cherrypy.expose
    def debug(self):
        debug_info = '\n'.join(self._formatStdout() + self._formatStdout('stderr', color='red'))
        return html_page(debug_info)

    def _buildAnalysisPage(self, builder, refresh=False):
        if not path.exists(self.schPath):
            return html_page("No schedule.")

        config, matchL, optState = read_pickle(self.schPath)
        if config is None:
            return html_page("Error reading schedule file, please try again.")

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
