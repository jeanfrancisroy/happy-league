'''
Created on Oct 7, 2010

@author: alex
'''
from future.utils import iteritems
import numpy as np

emptyD = {}


class TableMap:
    def __init__(self, tableD, rowL=None, colL=None, rowSortKey=None, colSortKey=None, noneStr='---'):

        self.noneStr = noneStr

        if rowL is None or colL is None:
            rowKey, colKey = zip(*tableD.keys())
            if rowL is None:
                rowL = list(set(rowKey))
                rowL.sort(key=rowSortKey)
            if colL is None:
                colL = list(set(colKey))
                colL.sort(key=colSortKey)
        self.row2idx = self.buildIdx(rowL)
        self.col2idx = self.buildIdx(colL)
        self.formatInfo()

        self.mat = np.zeros((len(rowL), len(colL)), object)
        self.mat[:, :] = None
        for key, val in iteritems(tableD):
            try:
                self.mat[self.row2idx[key[0]], self.col2idx[key[1]]] = val
            except KeyError:
                pass

    def formatInfo(self, fmt={}, align={}, title=None, rowCaption=emptyD.get, colCaption=emptyD.get):
        self.format = fmt
        self.align = align
        self.title = title
        self.colCaption = colCaption
        self.rowCaption = rowCaption
        self.texFormatD = {}

    def delCol(self, key):
        idx = self.col2idx.pop(key)
        self.mat = np.delete(self.mat, idx, 1)
        for key, idx_ in iteritems(self.col2idx):
            if idx_ > idx:
                self.col2idx[key] -= 1

    def insertCol(self, colName, colD, beforeKey):
        idx = self.col2idx[beforeKey]
        for key, idx_ in iteritems(self.col2idx):
            if idx_ >= idx:
                self.col2idx[key] += 1
        self.col2idx[colName] = idx
        self.mat = np.insert(self.mat, idx, None, 1)
        for key, val in iteritems(colD):
            rowIdx = self.row2idx[key]
            self.mat[rowIdx, idx] = val

    def orderCol(self, colL):
        self.mat = np.array([self[:, col] for col in colL]).T
        self.col2idx = self.buildIdx(colL)

    def transpose(self):
        self.mat = self.mat.T
        tmp = self.col2idx
        self.col2idx = self.row2idx
        self.row2idx = tmp

    def iterCols(self):
        for key, idx in iteritems(self.col2idx):
            yield key, self.mat[:, idx]

    def iterRows(self):
        for key, idx in iteritems(self.row2idx):
            yield key, self.mat[idx, :]

    def colKeys(self):
        return self._sortedKeys(self.col2idx)

    def rowKeys(self):
        return self._sortedKeys(self.row2idx)

    def _sortedKeys(self, key2idx):
        keyL = [(idx, key) for key, idx in iteritems(key2idx)]
        keyL.sort()
        return zip(*keyL)[1]

    def __getitem__(self, argL):
        row, col = argL
        if not isinstance(row, slice):
            row = self.row2idx[row]
        if not isinstance(col, slice):
            col = self.col2idx[col]
        return self.mat.__getitem__((row, col))

    def __setitem__(self, argL, value):
        row, col = argL
        if not isinstance(row, slice):
            row = self.row2idx[row]
        if not isinstance(col, slice):
            col = self.col2idx[col]
        return self.mat.__setitem__((row, col), value)

    def buildIdx(self, valL):
        d = {}
        for i, val in enumerate(valL):
            d[val] = i
        return d

    def toStrMat(self, colHeader=True, rowHeader=True):
        # build the columns

        colL = [None]*(len(self.col2idx))
        for colKey, colIdx in iteritems(self.col2idx):
            fmt = self.format.get(colKey, '%s')

            col = []
            for e in self.mat[:, colIdx]:
                if e is None:
                    col.append(self.noneStr)
                else:
                    try:
                        col.append(fmt % e)
                    except TypeError:
                        col.append(str(e))

            colL[colIdx] = col

            if colHeader:
                colL[colIdx].insert(0, self.colCaption(colKey, "%s" % colKey))

        if rowHeader:
            rowHead = ['']*(1 + len(self.row2idx))
            for rowKey, rowIdx in iteritems(self.row2idx):
                caption = self.rowCaption(rowKey, "%s" % rowKey)
                rowHead[1 + rowIdx] = caption
            colL.insert(0, rowHead)

        return colL

    def __str__(self):
        colL = self.toStrMat()
        colL.insert(1, ['|']*len(colL[0]))
        # set string size and center the text in each cell
        for i, col in enumerate(colL):
            maxSz = max([len(cell) for cell in col])

            colL[i] = [cell.center(maxSz) for cell in col]
            colL[i].insert(1, '-'*maxSz)

        return '\n'.join([' '.join(row) for row in zip(*colL)])

    def __tab__(self, sep='\t'):
        colL = self.toStrMat()
        return '\n'.join([sep.join(row) for row in zip(*colL)])
