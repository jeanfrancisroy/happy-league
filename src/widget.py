from PySide.QtCore import  Qt
from PySide.QtGui import  QVBoxLayout, QApplication, QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout
from PySide import QtGui as gui
import sys
from calendar import Calendar, SUNDAY, month_name
import time as t
import datetime as dt

wDayL = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat' ]




class Schedule( QWidget):
    
    def __init__(self, schedule, *args):
        QWidget.__init__(self, *args)
        self.schedule = schedule
        gui.QTableWidget()


class ConfigDate( QWidget ):
    
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        
        dateList = gui.QListWidget()
#        dateList.addItem( gui.QListWidgetItem('select date') )

#        dateTable.verticalHeader().setVisible(False)
#        dateTable.setHorizontalHeaderLabels(['Dates list'])
        dateList.setSelectionRectVisible(False)
        dateList.setSpacing(10)
#        dateTable.setShowGrid(False)

#        dateList.clicked.connect(self.getDate)
        dateList.mouseReleaseEvent = self.getDate
        self.setLayout( QVBoxLayout())
        self.layout().addWidget(dateList)
        self.dateList = dateList
        
        self.datePicker = DatePickerDialog()
        
    
    
    def getDate(self,*argL):
        accept = self.datePicker.exec_()
        if accept:
            self.dateList.clear()
            for date in self.datePicker.getDates():
                
                self.dateList.addItem(  gui.QListWidgetItem(date.strftime('%A, %B %d, %Y'))  )


def f(*argL):
    print 'event', argL

class DatePickerDialog(gui.QDialog):
    
    def __init__(self):
        
        gui.QDialog.__init__(self)
        
        mdp = MultiDatePicker()
        self.setModal(True)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget( mdp )
        self.mdp = mdp
        
        applyLayout = QHBoxLayout()
        bApply = gui.QPushButton("&ok")
        bCancel = gui.QPushButton("&cancel")
        bApply.clicked.connect(self.accept)
        bCancel.clicked.connect(self.reject)
        applyLayout.addStretch(1)
        applyLayout.addWidget(bApply)
        applyLayout.addWidget(bCancel)
        self.layout().addLayout( applyLayout )
        self.setWindowTitle("Multiple Date Picker")

    def getDates(self): 
        dateL = list(self.mdp.dateSet)
        dateL.sort()
        return dateL

class MultiDatePicker(QWidget):
    
    def __init__(self, *args):
        QWidget.__init__(self, *args)


        table = QTableWidget(6, 7, self)
        self.table = table
        self.cal = Calendar(SUNDAY)
        table.setHorizontalHeaderLabels(wDayL)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.resizeColumnsToContents()
#        table.setColumnWidth(1,100)
        table.cellClicked.connect(self.addDate)
        table.wheelEvent= self.wheelEvent
#        table.wheelEvent.connect(f)
        
        layout = QVBoxLayout()
        monthLayout = QHBoxLayout()
        
        qLeft = gui.QPushButton()
        qLeft.setText('<')
        qLeft.clicked.connect(self.decrMonth)
        qRight = gui.QPushButton()
        qRight.setText('>')
        qRight.clicked.connect(self.incrMonth)
        monthLabel = gui.QLabel()
        monthLabel.setAlignment(Qt.AlignCenter)
        
        monthLayout.addStretch(1)
        monthLayout.addWidget(qLeft)
        monthLayout.addWidget(monthLabel)
        monthLayout.addWidget(qRight)
        monthLayout.addStretch(1)
        
  
        self.dateSet = set()
        
        layout.addLayout(monthLayout)
        layout.addWidget(table)
        self.monthLabel = monthLabel
        timeTuple= t.gmtime()
        self.year = timeTuple.tm_year
        self.month = timeTuple.tm_mon
        self.populateTable( )

        
        self.table.resizeEvent = self.resize
        
        self.setLayout(layout)

    def resize(self,eSize):
        gui.QTableWidget.resizeEvent( self.table,eSize )
        width = eSize.size().width()
        height = eSize.size().height()
        n = self.table.columnCount()
        m = self.table.rowCount()
        for i in range(n):
            self.table.setColumnWidth(i,width/n)
        for i in range(m):
            self.table.setRowHeight(i,height/m)
#        print 'resize', e,argL


    def addDate(self, row, col, *argL ):
        item = self.table.item(row, col)
        day = self.dayL[ row*7 + col]
        if day >0:
            date = dt.date( self.year, self.month, day )
            if date in self.dateSet: self.dateSet.remove(date)
            else: self.dateSet.add(date)
            self.setBgColor(item, date)


    def setBgColor(self,item, date):
        if date in self.dateSet:
            item.setBackground(  gui.QPalette().highlight() )
        else:
            item.setBackground( Qt.white )
        

    def populateTable(self):
        
        
        self.monthLabel.setText('%s %d'%(month_name[self.month], self.year) )
        self.table.setRowCount(6)
        self.dayL = []
        for i, day in enumerate( self.cal.itermonthdays(self.year,self.month) ):
            
            self.dayL.append(day)
 
            
            if day == 0:   strDay = ''
            else:          strDay = str(day)
            item = QTableWidgetItem(strDay)
            item.setFlags(Qt.ItemIsEnabled)
            
            if day != 0:            
                date = dt.date(self.year, self.month, day )
                self.setBgColor(item, date)
            else:
                item.setBackground( Qt.white )
            
            self.table.setItem(i//7, i%7, item)

        self.table.setRowCount(i//7+1)

    def decrMonth(self):
        self.month -= 1
        if self.month <1:
            self.month = 12
            self.year -=1
        self.populateTable()


    def incrMonth(self):
        self.month += 1
        if self.month >12:
            self.month = 1
            self.year +=1
        self.populateTable()

    def wheelEvent(self, e):
        incr = e.delta()
        if incr > 0: self.decrMonth()
        else:        self.incrMonth()
         
    def apply(self):
        print 'apply'
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    w = ConfigDate()
    w.show()
    sys.exit(app.exec_())
    
    