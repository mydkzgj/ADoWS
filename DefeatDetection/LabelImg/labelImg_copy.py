#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import distutils.spawn
import os.path
import platform
import re
import sys
import subprocess
import labelImg_copy

#Cjy at 2019.5.22 生成缩略图
import thumbGeneration as th

#Cjy at 2018.12.06
import ctypes

from functools import partial
from collections import defaultdict
  

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *    
except ImportError:
    # needed for py3+qt4
    # Ref:
    # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
    # http://stackoverflow.com/questions/21217399/pyqt4-qtcore-qvariant-object-instead-of-a-string
    if sys.version_info.major >= 3:
        import sip
        sip.setapi('QVariant', 2)
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

import resources
# Add internal libs
from libs.constants import *
from libs.lib import struct, newAction, newIcon, addActions, fmtShortcut, generateColorByText
from libs.settings import Settings
from libs.shape import Shape, DEFAULT_LINE_COLOR, DEFAULT_FILL_COLOR
from libs.canvas import Canvas
from libs.zoomWidget import ZoomWidget
from libs.labelDialog import LabelDialog
from libs.colorDialog import ColorDialog
from libs.labelFile import LabelFile, LabelFileError
from libs.toolBar import ToolBar
from libs.pascal_voc_io import PascalVocReader
from libs.pascal_voc_io import XML_EXT
from libs.yolo_io import YoloReader
from libs.yolo_io import TXT_EXT
from libs.ustr import ustr
from libs.version import __version__

__appname__ = 'labelImg_compare'

# Utility functions and classes.

def have_qstring():
    '''p3/qt5 get rid of QString wrapper as py3 has native unicode str type'''
    return not (sys.version_info.major >= 3 or QT_VERSION_STR.startswith('5.'))

def util_qt_strlistclass():
    return QStringList if have_qstring() else list


class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar


# PyQt5: TypeError: unhashable type: 'QListWidgetItem'
class HashableQListWidgetItem(QListWidgetItem):

    def __init__(self, *args):
        super(HashableQListWidgetItem, self).__init__(*args)

    def __hash__(self):
        return hash(id(self))


class MainWindow(QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    MainWindowArg = []
    # CJY at 20181205 增加transFilePath
    def __init__(self, defaultFilename=None, defaultPrefdefClassFile=None, defaultSaveDir=None , i_x_namedict={}):
        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)
        #CJY at 2019.5.13 存储巡检信息
        self.information = []
        
        #CJY at 2019.5.12 读取img与xml的名字对应字典
        self.img_xml_namedict = {}
        if i_x_namedict != {}:
            self.img_xml_namedict = i_x_namedict                
        
        #CJY at 2019.3.7 增加对删除项的计数功能
        self.deleteNum = 0
    
        #CJY at 2019.01.17  切换normal标签显示
        self.tNPflag = False
        
        #CJY at 2018.12.06 为了给labelImg_copy传参
        self.LabelCopyArg=[]
        self.LabelCopyArg_org=[]
        
        #CJY at 2018.12.05 translate
        transFilePath = os.path.dirname(defaultPrefdefClassFile)
        self.trans = QTranslator()
        self.trans.load(transFilePath+"/zh_CN_cjy")   
        _app = QApplication.instance()
        _app.installTranslator(self.trans)
        
        #CJY at 2018.12.05
        self.MainWindowArg.append(defaultFilename)
        self.MainWindowArg.append(defaultPrefdefClassFile)
        self.MainWindowArg.append(defaultSaveDir)
        self.MainWindowArg.append(transFilePath)
        
        # Load setting in the main thread
        self.settings = Settings()
        self.settings.load()
        settings = self.settings

        # Save as Pascal voc xml
        self.defaultSaveDir = defaultSaveDir
        self.usingPascalVocFormat = True
        self.usingYoloFormat = False

        # For loading all image under a directory
        self.mImgList = []
        self.dirname = None
        self.labelHist = []
        self.lastOpenDir = None

        # Whether we need to save or not.
        self.dirty = False

        self._noSelectionSlot = False
        self._beginner = True
        self.screencastViewer = self.getAvailableScreencastViewer()
        self.screencast = "https://youtu.be/p0nR2YsCY_U"

        # Load predefined classes to the list
        self.loadPredefinedClasses(defaultPrefdefClassFile)

        # Main widgets and related state.
        self.labelDialog = LabelDialog(parent=self, listItem=self.labelHist)

        self.itemsToShapes = {}
        self.shapesToItems = {}
        self.prevLabelText = ''

        listLayout = QVBoxLayout()
        listLayout.setContentsMargins(0, 0, 0, 0)

        # Create a widget for using default label
        self.useDefaultLabelCheckbox = QCheckBox(self.tr(u'Use default label'))
        self.useDefaultLabelCheckbox.setChecked(False)
        self.defaultLabelTextLine = QLineEdit()
        useDefaultLabelQHBoxLayout = QHBoxLayout()
        useDefaultLabelQHBoxLayout.addWidget(self.useDefaultLabelCheckbox)
        useDefaultLabelQHBoxLayout.addWidget(self.defaultLabelTextLine)
        useDefaultLabelContainer = QWidget()
        useDefaultLabelContainer.setLayout(useDefaultLabelQHBoxLayout)

        # Create a widget for edit and diffc button
        self.diffcButton = QCheckBox(self.tr(u'difficult'))
        self.diffcButton.setChecked(False)
        self.diffcButton.stateChanged.connect(self.btnstate)
        self.editButton = QToolButton()
        self.editButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Add some of widgets to listLayout
        listLayout.addWidget(self.editButton)
        listLayout.addWidget(self.diffcButton)
        listLayout.addWidget(useDefaultLabelContainer)

        # Create and add a widget for showing current label items
        self.labelList = QListWidget()
        #CJY at 2019.2.13  多选
        self.labelList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        labelListContainer = QWidget()
        labelListContainer.setLayout(listLayout)
        self.labelList.itemActivated.connect(self.labelSelectionChanged)
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.labelList.itemDoubleClicked.connect(self.editLabel)
        # Connect to itemChanged to detect checkbox changes.
        self.labelList.itemChanged.connect(self.labelItemChanged)
        listLayout.addWidget(self.labelList)

        self.dock = QDockWidget(self.tr(u'Box Labels'), self)
        self.dock.setObjectName(self.tr(u'Labels'))
        self.dock.setWidget(labelListContainer)

        # Tzutalin 20160906 : Add file list and dock to move faster
        self.fileListWidget = QListWidget()
        self.fileListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        filelistLayout = QVBoxLayout()
        filelistLayout.setContentsMargins(0, 0, 0, 0)
        filelistLayout.addWidget(self.fileListWidget)
        fileListContainer = QWidget()
        fileListContainer.setLayout(filelistLayout)
        self.filedock = QDockWidget(self.tr(u'File List'), self)
        self.filedock.setObjectName(u'Files')
        self.filedock.setWidget(fileListContainer)
        
        # Cjy in 20181203 : Add Information list and dock to show information
        self.informationListWidget = QListWidget()
        #self.informationListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        informationlistLayout = QVBoxLayout()
        informationlistLayout.setContentsMargins(0, 0, 0, 0)
        informationlistLayout.addWidget(self.informationListWidget)
        informationListContainer = QWidget()
        informationListContainer.setLayout(informationlistLayout)
        self.informationdock = QDockWidget(self.tr(u'Information List'), self)
        self.informationdock.setObjectName(u'Information')
        self.informationdock.setWidget(informationListContainer)
        
        
        #Cjy at 20181211 : 图例
        self.legendListWidget = QListWidget()
        #self.informationListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        legendlistLayout = QVBoxLayout()
        legendlistLayout.setContentsMargins(0, 0, 0, 0)
        legendlistLayout.addWidget(self.legendListWidget)
        legendListContainer = QWidget()
        legendListContainer.setLayout(legendlistLayout)
        self.legenddock = QDockWidget(self.tr(u'Legend List'), self)
        self.legenddock.setObjectName(u'Legend')
        self.legenddock.setWidget(legendListContainer)
        
        

        self.zoomWidget = ZoomWidget()
        self.colorDialog = ColorDialog(parent=self)

        self.canvas = Canvas(parent=self)
        self.canvas.zoomRequest.connect(self.zoomRequest)
        self.canvas.setDrawingShapeToSquare(settings.get(SETTING_DRAW_SQUARE, False))

        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.scrollArea = scroll
        self.canvas.scrollRequest.connect(self.scrollRequest)

        self.canvas.newShape.connect(self.newShape)
        #CJY at 2019.2.13 
        self.canvas.multiSelectShapes.connect(self.multiSelectShapes)
        
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)

        self.setCentralWidget(scroll)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        # Cjy in 20181211 : Add Legend list
        self.addDockWidget(Qt.RightDockWidgetArea, self.legenddock)
        self.legenddock.setFeatures(QDockWidget.DockWidgetFloatable)
        # Cjy in 20181203 : Add Information list and dock to show information
        self.addDockWidget(Qt.RightDockWidgetArea, self.informationdock)
        self.informationdock.setFeatures(QDockWidget.DockWidgetFloatable)
        # Tzutalin 20160906 : Add file list and dock to move faster
        self.addDockWidget(Qt.RightDockWidgetArea, self.filedock)
        self.filedock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.dockFeatures = QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        self.dock.setFeatures(self.dock.features() ^ self.dockFeatures)

        # Actions
        
        #ZZX chinese Actions
        action = partial(newAction, self)
        quitname='&退出'
        openname='&打开'
        opendirname='&打开路径'
        changeSavedirname='&改变存储路径'
        openAnnotationname='&打开注释'
        openNextImgname='&下一张图片'
        openPrevImgname='&上一张图片'
        verifyname='&核实图片'
        savename='&保存'
        save_formatname='&存储格式'
        saveAsname='&标签存储'
        closename='&关闭'
        resetAllname='&布局重置'
        color1name='&矩形框颜色'
        createModename='&创建\n矩形框'
        editModename='&编辑矩形框'
        createname='&创建\n新矩形框'
        deletename='&删除矩形框'
        copyname='&复制矩形框'
        advancedModename='&上一个版本'
        hideAllname='&隐藏矩形框'
        showAllname='&显示矩形框'
        helpname='&帮助'
        zoomInname='&放大'
        zoomOutname='&缩小'
        zoomOrgname='&原图大小'
        fitWindowname='适应窗口大小'
        fitWidthname='适应窗口长度'
        showInfoname='&软件信息'
        editname='&编辑矩形框'
        shapeLineColorname='边缘颜色'
        shapeFillColorname='填充颜色'
        
        # CJY 
        compare = action(u"&对比", self.compareWithHistoricalImage,
                      'Ctrl+P', 'compare', u'与历史图片对比')
        
        clearL = action(u"&清空", self.clearLabels,
                      'Ctrl+C', 'clearL', u'清空标注')
        
        
        toggleNP = action(u"&切换显示", partial(self.toggleNormalPolygons,True),
                      'Ctrl+/', 'toggleNP', u'切换normal标签显示')
        
        cLtoN = action(u"&转换标签", self.changeLabeltoNormal,
                      'Ctrl+space', 'cLtoN', u'将标签转换为normal')
        
        mSelect = action(u"&多选", self.createMultiSelect,
                      'Ctrl+m', 'mSelect', u'多选')
        
        quit = action(quitname, self.close,
                      'Ctrl+Q', 'quit', u'退出应用')

        open = action(openname, self.openFile,
                      'Ctrl+O', 'open', u'打开图片或标签文件')

        opendir = action(opendirname, self.openDirDialog,
                         'Ctrl+u', 'open', u'打开路径')

        changeSavedir = action(changeSavedirname, self.changeSavedirDialog,
                               'Ctrl+r', 'open', u'改变默认的标签存储路径')

        openAnnotation = action(openAnnotationname, self.openAnnotationDialog,
                                'Ctrl+Shift+O', 'open', u'打开标签文件')

        openNextImg = action(openNextImgname, self.openNextImg,
                             'd', 'next', u'打开下一个')

        openPrevImg = action(openPrevImgname, self.openPrevImg,
                             'a', 'prev', u'打开上一个')

        verify = action(verifyname, self.verifyImg,
                        'space', 'verify', u'验证图像')

        save = action(savename, self.saveFile,
                      'Ctrl+S', 'save', u'存储标签', enabled=False)

        save_format = action(save_formatname, self.change_format,
                      'Ctrl+', 'format_voc', u'改变存储格式', enabled=True)

        saveAs = action(saveAsname, self.saveFileAs,
                        'Ctrl+Shift+S', 'save-as', u'存储标签为另外的文件', enabled=False)

        close = action(closename, self.closeFile, 'Ctrl+W', 'close', u'关闭当前文件')

        resetAll = action(resetAllname, self.resetAll, None, 'resetall', u'重置所有')

        color1 = action(color1name, self.chooseColor1,
                        'Ctrl+L', 'color_line', u'选择矩形框的线的颜色')

        createMode = action(createModename, self.setCreateMode,
                            'w', 'new', u'Start drawing Boxs', enabled=False)
        editMode = action(editModename, self.setEditMode,
                          'Ctrl+J', 'edit', u'Move and edit Boxs', enabled=False)

        create = action(createname, self.createShape,
                        'w', 'new', u'绘制一个新框', enabled=False)
        delete = action(deletename, self.deleteSelectedShape,
                        'Delete', 'delete', u'删除', enabled=False)
        copy = action(copyname, self.copySelectedShape,
                      'Ctrl+D', 'copy', u'为选中框创建一个副本',
                      enabled=False)

        advancedMode = action(advancedModename, self.toggleAdvancedMode,
                              'Ctrl+Shift+A', 'expert', u'转换为上一个版本（精简版本）',
                              checkable=True)

        hideAll = action(hideAllname, partial(self.togglePolygons, False),
                         'Ctrl+H', 'hide', u'隐藏所有框',
                         enabled=False)
        showAll = action(showAllname, partial(self.togglePolygons, True),
                         'Ctrl+A', 'hide', u'显示所有框',
                         enabled=False)

        help = action(helpname, self.showTutorialDialog, None, 'help', u'展示例子')
        showInfo = action(showInfoname, self.showInfoDialog, None, 'help', u'信息')

        zoom = QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            u"Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." % (fmtShortcut("Ctrl+[-+]"),
                                             fmtShortcut("Ctrl+Wheel")))
        self.zoomWidget.setEnabled(False)

        #CJY at 2018.12.12 更改快捷键
        zoomIn = action(zoomInname, partial(self.addZoom, 10),
                        'Ctrl+z', 'zoom-in', u'放大', enabled=False)
        zoomOut = action(zoomOutname, partial(self.addZoom, -10),
                         'Ctrl+x', 'zoom-out', u'缩小', enabled=False)
        zoomOrg = action(zoomOrgname, partial(self.setZoom, 100),
                         'Ctrl+=', 'zoom', u'恢复原图大小', enabled=False)
        fitWindow = action(fitWindowname, self.setFitWindow,
                           'Ctrl+F', 'fit-window', u'适应窗口大小',
                           checkable=True, enabled=False)
        fitWidth = action(fitWidthname, self.setFitWidth,
                          'Ctrl+Shift+F', 'fit-width', u'适应窗口宽度',
                          checkable=True, enabled=False)
        # Group zoom controls into a list for easier toggling.
        zoomActions = (self.zoomWidget, zoomIn, zoomOut,
                       zoomOrg, fitWindow, fitWidth)
        self.zoomMode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action(editname, self.editLabel,
                      'Ctrl+E', 'edit', u'编辑选中框的标签',
                      enabled=False)
        self.editButton.setDefaultAction(edit)

        shapeLineColor = action(shapeLineColorname, self.chshapeLineColor,
                                icon='color_line', tip=u'Change the line color for this specific shape',
                                enabled=False)
        shapeFillColor = action(shapeFillColorname, self.chshapeFillColor,
                                icon='color', tip=u'Change the fill color for this specific shape',
                                enabled=False)

        labels = self.dock.toggleViewAction()
        labels.setText('显示或隐藏标签面板')
        labels.setShortcut('Ctrl+Shift+L')

        # Lavel list context menu.
        labelMenu = QMenu()
        addActions(labelMenu, (edit, delete))
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu)

        # Draw squares/rectangles
        self.drawSquaresOption = QAction('画矩形框', self)
        self.drawSquaresOption.setShortcut('Ctrl+Shift+R')
        self.drawSquaresOption.setCheckable(True)
        self.drawSquaresOption.setChecked(settings.get(SETTING_DRAW_SQUARE, False))
        self.drawSquaresOption.triggered.connect(self.toogleDrawSquare)

        # Store actions for further handling.
        self.actions = struct(save=save, save_format=save_format, saveAs=saveAs, open=open, close=close, resetAll = resetAll,
                              lineColor=color1, create=create, delete=delete, edit=edit, copy=copy,
                              createMode=createMode, editMode=editMode, advancedMode=advancedMode,
                              shapeLineColor=shapeLineColor, shapeFillColor=shapeFillColor,
                              zoom=zoom, zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg,
                              fitWindow=fitWindow, fitWidth=fitWidth,
                              zoomActions=zoomActions,
                              fileMenuActions=(
                                  open, opendir, save, saveAs, close, resetAll, quit),
                              beginner=(), advanced=(),
                              editMenu=(edit, copy, delete,
                                        None, color1, self.drawSquaresOption),
                              beginnerContext=(create, edit, copy, delete),
                              advancedContext=(createMode, editMode, edit, copy,
                                               delete, shapeLineColor, shapeFillColor),
                              onLoadActive=(
                                  close, create, createMode, editMode),
                              onShapesPresent=(saveAs, hideAll, showAll))

        self.menus = struct(
            file=self.menu('&文件'),
            edit=self.menu('&编辑'),
            view=self.menu('&视图'),
            help=self.menu('&帮助'),
            recentFiles=QMenu('&打开最近图片'),
            labelList=labelMenu)

        # Auto saving : Enable auto saving if pressing next
        self.autoSaving = QAction("自动保存", self)
        self.autoSaving.setCheckable(True)
        self.autoSaving.setChecked(settings.get(SETTING_AUTO_SAVE, False))
        # Sync single class mode from PR#106
        self.singleClassMode = QAction("单一标签模式", self)
        self.singleClassMode.setShortcut("Ctrl+Shift+S")
        self.singleClassMode.setCheckable(True)
        self.singleClassMode.setChecked(settings.get(SETTING_SINGLE_CLASS, False))
        self.lastLabel = None
        # Add option to enable/disable labels being painted at the top of bounding boxes
        self.paintLabelsOption = QAction("彩色标签", self)
        self.paintLabelsOption.setShortcut("Ctrl+Shift+P")
        self.paintLabelsOption.setCheckable(True)
        self.paintLabelsOption.setChecked(settings.get(SETTING_PAINT_LABEL, False))
        self.paintLabelsOption.triggered.connect(self.togglePaintLabelsOption)
        
        '''
        action = partial(newAction, self)
        
        quit = action(self.tr('&Quit'), self.close,
                      'Ctrl+Q', 'quit', self.tr(u'Quit application'))

        open = action(self.tr('&Open'), self.openFile,
                      'Ctrl+O', 'open', self.tr(u'Open image or label file'))

        opendir = action(self.tr('&Open Dir'), self.openDirDialog,
                         'Ctrl+u', 'open', self.tr(u'Open Dir'))

        changeSavedir = action(self.tr('&Change Save Dir'), self.changeSavedirDialog,
                               'Ctrl+r', 'open', self.tr(u'Change default saved Annotation dir'))

        openAnnotation = action(self.tr('&Open Annotation'), self.openAnnotationDialog,
                                'Ctrl+Shift+O', 'open', self.tr(u'Open Annotation'))

        openNextImg = action(self.tr('&Next Image'), self.openNextImg,
                             'd', 'next', self.tr(u'Open Next'))

        openPrevImg = action(self.tr('&Prev Image'), self.openPrevImg,
                             'a', 'prev', self.tr(u'Open Prev'))

        verify = action(self.tr('&Verify Image'), self.verifyImg,
                        'space', 'verify', self.tr(u'Verify Image'))

        save = action(self.tr('&Save'), self.saveFile,
                      'Ctrl+S', 'save', self.tr(u'Save labels to file'), enabled=False)

        save_format = action(self.tr('&PascalVOC'), self.change_format,
                      'Ctrl+', 'format_voc', self.tr(u'Change save format'), enabled=True)

        saveAs = action(self.tr('&Save As'), self.saveFileAs,
                        'Ctrl+Shift+S', 'save-as', self.tr(u'Save labels to a different file'), enabled=False)

        close = action(self.tr('&Close'), self.closeFile, 'Ctrl+W', 'close', self.tr(u'Close current file'))

        resetAll = action(self.tr('&ResetAll'), self.resetAll, None, 'resetall', self.tr(u'Reset all'))

        color1 = action(self.tr('Box Line Color'), self.chooseColor1,
                        'Ctrl+L', 'color_line', self.tr(u'Choose Box line color'))

        createMode = action(self.tr('Create\nRectBox'), self.setCreateMode,
                            'w', 'new', self.tr(u'Start drawing Boxs'), enabled=False)
        editMode = action(self.tr('&Edit\nRectBox'), self.setEditMode,
                          'Ctrl+J', 'edit', self.tr(u'Move and edit Boxs'), enabled=False)

        create = action(self.tr('Create\nRectBox'), self.createShape,
                        'w', 'new', self.tr(u'Draw a new Box'), enabled=False)
        delete = action(self.tr('Delete\nRectBox'), self.deleteSelectedShape,
                        'Delete', 'delete', self.tr(u'Delete'), enabled=False)
        copy = action(self.tr('&Duplicate\nRectBox'), self.copySelectedShape,
                      'Ctrl+D', 'copy', self.tr(u'Create a duplicate of the selected Box'),
                      enabled=False)

        advancedMode = action(self.tr('&Advanced Mode'), self.toggleAdvancedMode,
                              'Ctrl+Shift+A', 'expert', self.tr(u'Switch to advanced mode'),
                              checkable=True)

        hideAll = action(self.tr('&Hide\nRectBox'), partial(self.togglePolygons, False),
                         'Ctrl+H', 'hide', self.tr(u'Hide all Boxs'),
                         enabled=False)
        showAll = action(self.tr('&Show\nRectBox'), partial(self.togglePolygons, True),
                         'Ctrl+A', 'hide', self.tr(u'Show all Boxs'),
                         enabled=False)

        help = action(self.tr('&Tutorial'), self.showTutorialDialog, None, 'help', self.tr(u'Show demos'))
        showInfo = action(self.tr('&Information'), self.showInfoDialog, None, 'help', self.tr(u'Information'))

        zoom = QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            u"Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." % (fmtShortcut("Ctrl+[-+]"),
                                             fmtShortcut("Ctrl+Wheel")))
        self.zoomWidget.setEnabled(False)

        zoomIn = action(self.tr('Zoom &In'), partial(self.addZoom, 10),
                        'Ctrl++', 'zoom-in', self.tr(u'Increase zoom level'), enabled=False)
        zoomOut = action(self.tr('&Zoom Out'), partial(self.addZoom, -10),
                         'Ctrl+-', 'zoom-out', self.tr(u'Decrease zoom level'), enabled=False)
        zoomOrg = action(self.tr('&Original size'), partial(self.setZoom, 100),
                         'Ctrl+=', 'zoom', self.tr(u'Zoom to original size'), enabled=False)
        fitWindow = action(self.tr('&Fit Window'), self.setFitWindow,
                           'Ctrl+F', 'fit-window', self.tr(u'Zoom follows window size'),
                           checkable=True, enabled=False)
        fitWidth = action(self.tr('Fit &Width'), self.setFitWidth,
                          'Ctrl+Shift+F', 'fit-width', self.tr(u'Zoom follows window width'),
                          checkable=True, enabled=False)
        # Group zoom controls into a list for easier toggling.
        zoomActions = (self.zoomWidget, zoomIn, zoomOut,
                       zoomOrg, fitWindow, fitWidth)
        self.zoomMode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action(self.tr('&Edit Label'), self.editLabel,
                      'Ctrl+E', 'edit', self.tr(u'Modify the label of the selected Box'),
                      enabled=False)
        self.editButton.setDefaultAction(edit)

        shapeLineColor = action(self.tr('Shape &Line Color'), self.chshapeLineColor,
                                icon='color_line', tip=self.tr(u'Change the line color for this specific shape'),
                                enabled=False)
        shapeFillColor = action('Shape &Fill Color', self.chshapeFillColor,
                                icon='color', tip=self.tr(u'Change the fill color for this specific shape'),
                                enabled=False)

        labels = self.dock.toggleViewAction()
        labels.setText('Show/Hide Label Panel')
        labels.setShortcut('Ctrl+Shift+L')

        # Lavel list context menu.
        labelMenu = QMenu()
        addActions(labelMenu, (edit, delete))
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu)

        # Draw squares/rectangles
        self.drawSquaresOption = QAction('Draw Squares', self)
        self.drawSquaresOption.setShortcut('Ctrl+Shift+R')
        self.drawSquaresOption.setCheckable(True)
        self.drawSquaresOption.setChecked(settings.get(SETTING_DRAW_SQUARE, False))
        self.drawSquaresOption.triggered.connect(self.toogleDrawSquare)

        # Store actions for further handling.
        self.actions = struct(save=save, save_format=save_format, saveAs=saveAs, open=open, close=close, resetAll = resetAll,
                              lineColor=color1, create=create, delete=delete, edit=edit, copy=copy,
                              createMode=createMode, editMode=editMode, advancedMode=advancedMode,
                              shapeLineColor=shapeLineColor, shapeFillColor=shapeFillColor,
                              zoom=zoom, zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg,
                              fitWindow=fitWindow, fitWidth=fitWidth,
                              zoomActions=zoomActions,
                              fileMenuActions=(
                                  open, opendir, save, saveAs, close, resetAll, quit),
                              beginner=(), advanced=(),
                              editMenu=(edit, copy, delete,
                                        None, color1, self.drawSquaresOption),
                              beginnerContext=(create, edit, copy, delete),
                              advancedContext=(createMode, editMode, edit, copy,
                                               delete, shapeLineColor, shapeFillColor),
                              onLoadActive=(
                                  close, create, createMode, editMode),
                              onShapesPresent=(saveAs, hideAll, showAll))

        self.menus = struct(
            file=self.menu('&File'),
            edit=self.menu('&Edit'),
            view=self.menu('&View'),
            help=self.menu('&Help'),
            recentFiles=QMenu('Open &Recent'),
            labelList=labelMenu)

        # Auto saving : Enable auto saving if pressing next
        self.autoSaving = QAction("Auto Saving", self)
        self.autoSaving.setCheckable(True)
        self.autoSaving.setChecked(settings.get(SETTING_AUTO_SAVE, False))
        # Sync single class mode from PR#106
        self.singleClassMode = QAction("Single Class Mode", self)
        self.singleClassMode.setShortcut("Ctrl+Shift+S")
        self.singleClassMode.setCheckable(True)
        self.singleClassMode.setChecked(settings.get(SETTING_SINGLE_CLASS, False))
        self.lastLabel = None
        # Add option to enable/disable labels being painted at the top of bounding boxes
        self.paintLabelsOption = QAction("Paint Labels", self)
        self.paintLabelsOption.setShortcut("Ctrl+Shift+P")
        self.paintLabelsOption.setCheckable(True)
        self.paintLabelsOption.setChecked(settings.get(SETTING_PAINT_LABEL, False))
        self.paintLabelsOption.triggered.connect(self.togglePaintLabelsOption)
        #'''
        # CJY at 2018.12.05 add compare  and  12.24 add clearL toggleNP,2019.01.21 add cLtoN
        addActions(self.menus.file,
                   (open, opendir, changeSavedir, openAnnotation, self.menus.recentFiles, compare,clearL,toggleNP,cLtoN,mSelect,save, save_format, saveAs, close, resetAll, quit))
        addActions(self.menus.help, (help, showInfo))
        addActions(self.menus.view, (
            self.autoSaving,
            self.singleClassMode,
            self.paintLabelsOption,
            labels, advancedMode, None,
            hideAll, showAll, None,
            zoomIn, zoomOut, zoomOrg, None,
            fitWindow, fitWidth))

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

        # Custom context menu for the canvas widget:
        addActions(self.canvas.menus[0], self.actions.beginnerContext)
        addActions(self.canvas.menus[1], (
            action('&Copy here', self.copyShape),
            action('&Move here', self.moveShape)))

        self.tools = self.toolbar('Tools')
        # CJY at 2018.12.11
        self.actions.beginner = (
            open, opendir, changeSavedir, save, None, create, delete, None,
            zoomIn, zoom, zoomOut, fitWindow, fitWidth)
        ''' #copy
        self.actions.beginner = (
            open, opendir, changeSavedir, openNextImg, openPrevImg, verify, save, save_format, None, create, copy, delete, None,
            zoomIn, zoom, zoomOut, fitWindow, fitWidth)
        '''
        self.actions.advanced = (
            open, opendir, changeSavedir, openNextImg, openPrevImg, save, save_format, None,
            createMode, editMode, None,
            hideAll, showAll)

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()

        # Application state.
        self.image = QImage()
        self.filePath = ustr(defaultFilename)
        self.recentFiles = []
        self.maxRecent = 7
        self.lineColor = None
        self.fillColor = None
        self.zoom_level = 100
        self.fit_window = False
        # Add Chris
        self.difficult = False

        ## Fix the compatible issue for qt4 and qt5. Convert the QStringList to python list
        if settings.get(SETTING_RECENT_FILES):
            if have_qstring():
                recentFileQStringList = settings.get(SETTING_RECENT_FILES)
                self.recentFiles = [ustr(i) for i in recentFileQStringList]
            else:
                self.recentFiles = recentFileQStringList = settings.get(SETTING_RECENT_FILES)

        size = settings.get(SETTING_WIN_SIZE, QSize(600, 500))
        position = QPoint(0, 0)
        saved_position = settings.get(SETTING_WIN_POSE, position)
        # Fix the multiple monitors issue
        for i in range(QApplication.desktop().screenCount()):
            if QApplication.desktop().availableGeometry(i).contains(saved_position):
                position = saved_position
                break
        
        #CJY copy的需要去掉
        #wW = ctypes.windll.user32.GetSystemMetrics(0)
        #wH = ctypes.windll.user32.GetSystemMetrics(1)-100
        #self.resize(wW,wH)
        self.resize(size)
        self.move(position)
        
        #CJY at 20181205   2019.5.24 为了能够在对比时标注框缩小一半
        import ctypes
        wW = ctypes.windll.user32.GetSystemMetrics(0)/2
        wH = ctypes.windll.user32.GetSystemMetrics(1)-100
        self.resize(wW,wH)
        self.move(QPoint(wH,0)) 
        
        saveDir = ustr(settings.get(SETTING_SAVE_DIR, None))
        self.lastOpenDir = ustr(settings.get(SETTING_LAST_OPEN_DIR, None))
        if self.defaultSaveDir is None and saveDir is not None and os.path.exists(saveDir):
            self.defaultSaveDir = saveDir
            self.statusBar().showMessage('%s started. Annotation will be saved to %s' %
                                         (__appname__, self.defaultSaveDir))
            self.statusBar().show()

        self.restoreState(settings.get(SETTING_WIN_STATE, QByteArray()))
        Shape.line_color = self.lineColor = QColor(settings.get(SETTING_LINE_COLOR, DEFAULT_LINE_COLOR))
        Shape.fill_color = self.fillColor = QColor(settings.get(SETTING_FILL_COLOR, DEFAULT_FILL_COLOR))
        self.canvas.setDrawingColor(self.lineColor)
        # Add chris
        Shape.difficult = self.difficult

        def xbool(x):
            if isinstance(x, QVariant):
                return x.toBool()
            return bool(x)

        if xbool(settings.get(SETTING_ADVANCE_MODE, False)):
            self.actions.advancedMode.setChecked(True)
            self.toggleAdvancedMode()

        # Populate the File menu dynamically.
        self.updateFileMenu()

        # Since loading the file may take some time, make sure it runs in the background.
        if self.filePath and os.path.isdir(self.filePath):
            self.queueEvent(partial(self.importDirImages, self.filePath or ""))
        elif self.filePath:
            self.queueEvent(partial(self.loadFile, self.filePath or ""))

        # Callbacks:
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        self.populateModeActions()

        # Display cursor coordinates at the right of status bar
        self.labelCoordinates = QLabel('')
        self.statusBar().addPermanentWidget(self.labelCoordinates)

        #CJY at 2019.5.12  打开文件夹  
        #self.filePath = "D:\myWork\\clear\\20181115412\\20181115\\1019\\1\\org\\1019_1_0_2_2019.JPG"
#        if self.filePath != None:            
#            self.openDirByFile(self.filePath)
        
        # Open Dir if deafult file
        if self.filePath and os.path.isdir(self.filePath):
            self.openDirDialog(dirpath=self.filePath)
            
        print(self.filePath)
        


    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.canvas.setDrawingShapeToSquare(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            # Draw rectangle if Ctrl is pressed
            self.canvas.setDrawingShapeToSquare(True)

    ## Support Functions ##
    def set_format(self, save_format):
        if save_format == FORMAT_PASCALVOC:
            self.actions.save_format.setText(FORMAT_PASCALVOC)
            self.actions.save_format.setIcon(newIcon("format_voc"))
            self.usingPascalVocFormat = True
            self.usingYoloFormat = False
            LabelFile.suffix = XML_EXT

        elif save_format == FORMAT_YOLO:
            self.actions.save_format.setText(FORMAT_YOLO)
            self.actions.save_format.setIcon(newIcon("format_yolo"))
            self.usingPascalVocFormat = False
            self.usingYoloFormat = True
            LabelFile.suffix = TXT_EXT

    def change_format(self):
        if self.usingPascalVocFormat: self.set_format(FORMAT_YOLO)
        elif self.usingYoloFormat: self.set_format(FORMAT_PASCALVOC)

    def noShapes(self):
        return not self.itemsToShapes

    def toggleAdvancedMode(self, value=True):
        self._beginner = not value
        self.canvas.setEditing(True)
        self.populateModeActions()
        self.editButton.setVisible(not value)
        if value:
            self.actions.createMode.setEnabled(True)
            self.actions.editMode.setEnabled(False)
            self.dock.setFeatures(self.dock.features() | self.dockFeatures)
        else:
            self.dock.setFeatures(self.dock.features() ^ self.dockFeatures)

    def populateModeActions(self):
        if self.beginner():
            tool, menu = self.actions.beginner, self.actions.beginnerContext
        else:
            tool, menu = self.actions.advanced, self.actions.advancedContext
        self.tools.clear()
        addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (self.actions.create,) if self.beginner()\
            else (self.actions.createMode, self.actions.editMode)
        addActions(self.menus.edit, actions + self.actions.editMenu)

    def setBeginner(self):
        self.tools.clear()
        addActions(self.tools, self.actions.beginner)

    def setAdvanced(self):
        self.tools.clear()
        addActions(self.tools, self.actions.advanced)

    def setDirty(self):
        self.dirty = True
        self.actions.save.setEnabled(True)

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.create.setEnabled(True)

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def queueEvent(self, function):
        QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        self.itemsToShapes.clear()
        self.shapesToItems.clear()
        self.labelList.clear()
        self.filePath = None
        self.imageData = None
        self.labelFile = None
        self.canvas.resetState()
        self.labelCoordinates.clear()

    def currentItem(self):
        items = self.labelList.selectedItems()
        if items:
            return items[0]
        return None

    def addRecentFile(self, filePath):
        if filePath in self.recentFiles:
            self.recentFiles.remove(filePath)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filePath)

    def beginner(self):
        return self._beginner

    def advanced(self):
        return not self.beginner()

    def getAvailableScreencastViewer(self):
        osName = platform.system()

        if osName == 'Windows':
            return ['C:\\Program Files\\Internet Explorer\\iexplore.exe']
        elif osName == 'Linux':
            return ['xdg-open']
        elif osName == 'Darwin':
            return ['open', '-a', 'Safari']

    ## Callbacks ##
    def showTutorialDialog(self):
        subprocess.Popen(self.screencastViewer + [self.screencast])

    def showInfoDialog(self):
        msg = u'Name:{0} \nApp Version:{1} \n{2} '.format(__appname__, __version__, sys.version_info)
        QMessageBox.information(self, u'Information', msg)

    def createShape(self):
        assert self.beginner()
        self.canvas.setEditing(False)
        self.actions.create.setEnabled(False)   

    def toggleDrawingSensitive(self, drawing=True):
        """In the middle of drawing, toggling between modes should be disabled."""
        self.actions.editMode.setEnabled(not drawing)
        if not drawing and self.beginner():
            # Cancel creation.
            print('Cancel creation.')
            self.canvas.setEditing(True)
            self.canvas.restoreCursor()
            self.actions.create.setEnabled(True)

    def toggleDrawMode(self, edit=True):
        self.canvas.setEditing(edit)
        self.actions.createMode.setEnabled(edit)
        self.actions.editMode.setEnabled(not edit)

    def setCreateMode(self):
        assert self.advanced()
        self.toggleDrawMode(False)

    def setEditMode(self):
        assert self.advanced()
        self.toggleDrawMode(True)
        self.labelSelectionChanged()

    def updateFileMenu(self):
        currFilePath = self.filePath

        def exists(filename):
            return os.path.exists(filename)
        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recentFiles if f !=
                 currFilePath and exists(f)]
        for i, f in enumerate(files):
            icon = newIcon('labels')
            action = QAction(
                icon, '&%d %s' % (i + 1, QFileInfo(f).fileName()), self)
            action.triggered.connect(partial(self.loadRecent, f))
            menu.addAction(action)

    def popLabelListMenu(self, point):
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point))

    def editLabel(self):
        if not self.canvas.editing():
            return
        item = self.currentItem()
        text = self.labelDialog.popUp(item.text())
        if text is not None:
            item.setText(text)
            item.setBackground(generateColorByText(text))
            self.setDirty()

    # Tzutalin 20160906 : Add file list and dock to move faster
    def fileitemDoubleClicked(self, item=None):
        currIndex = self.mImgList.index(ustr(item.text()))
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                self.loadFile(filename)

    # Add chris
    def btnstate(self, item= None):
        """ Function to handle difficult examples
        Update on each object """
        if not self.canvas.editing():
            return

        item = self.currentItem()
        if not item: # If not selected Item, take the first one
            item = self.labelList.item(self.labelList.count()-1)

        difficult = self.diffcButton.isChecked()

        try:
            shape = self.itemsToShapes[item]
        except:
            pass
        # Checked and Update
        try:
            if difficult != shape.difficult:
                shape.difficult = difficult
                self.setDirty()
            else:  # User probably changed item visibility
                self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)
        except:
            pass

    # React to canvas signals.
    def shapeSelectionChanged(self, selected=False):
        if self._noSelectionSlot:
            self._noSelectionSlot = False
        else:
            '''
            for shape in self.canvas.shapes:
                self.shapesToItems[shape].setSelected(True)
            '''
            shape = self.canvas.selectedShape
            if shape:
                self.shapesToItems[shape].setSelected(True)
            else:
                self.labelList.clearSelection()
            
        self.actions.delete.setEnabled(selected)
        self.actions.copy.setEnabled(selected)
        self.actions.edit.setEnabled(selected)
        self.actions.shapeLineColor.setEnabled(selected)
        self.actions.shapeFillColor.setEnabled(selected)

    def addLabel(self, shape):
        shape.paintLabel = self.paintLabelsOption.isChecked()
        item = HashableQListWidgetItem(shape.label)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        item.setBackground(generateColorByText(shape.label))
        self.itemsToShapes[item] = shape
        self.shapesToItems[shape] = item
        self.labelList.addItem(item)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)
    
    
    def remLabel(self, shape):
        if shape is None:
            # print('rm empty label')
            return
        item = self.shapesToItems[shape]
        self.labelList.takeItem(self.labelList.row(item))
        del self.shapesToItems[shape]
        del self.itemsToShapes[item]
        
    #CJY at 2019.2.13 改为删除多个
    def remLabels(self, shapes):
        for shape in shapes:
            if shape is None:
                # print('rm empty label')
                return
            item = self.shapesToItems[shape]
            #CJY 2019.3.7 增加判断item是否是原始框，并计数
            boundaryItem = self.labelList.findItems("以上为原始框",Qt.MatchFixedString)
            boundaryIndex = self.labelList.row(boundaryItem[0])
            if self.labelList.row(item)< boundaryIndex:
                self.deleteNum = self.deleteNum +1
            
            
            self.labelList.takeItem(self.labelList.row(item))
            del self.shapesToItems[shape]
            del self.itemsToShapes[item]
            
        #print(self.deleteNum)

    def loadLabels(self, shapes):
        s = []
        for label, points, line_color, fill_color, difficult in shapes:
            shape = Shape(label=label)
            for x, y in points:
                shape.addPoint(QPointF(x, y))
            shape.difficult = difficult
            shape.close()
            s.append(shape)

            if line_color:
                shape.line_color = QColor(*line_color)
            else:
                shape.line_color = generateColorByText(label)

            if fill_color:
                shape.fill_color = QColor(*fill_color)
            else:
                shape.fill_color = generateColorByText(label)

            self.addLabel(shape)

        self.canvas.loadShapes(s)

    def saveLabels(self, annotationFilePath):
        annotationFilePath = ustr(annotationFilePath)
        if self.labelFile is None:
            self.labelFile = LabelFile()
            self.labelFile.verified = self.canvas.verified
        #CJY add recordSaveAction
        f = open(os.path.join(self.MainWindowArg[3],"saveFlag.txt"),"w")
        f.write(str(self.deleteNum))
        f.close()
        

        def format_shape(s):
            return dict(label=s.label,
                        line_color=s.line_color.getRgb(),
                        fill_color=s.fill_color.getRgb(),
                        points=[(p.x(), p.y()) for p in s.points],
                       # add chris
                        difficult = s.difficult)

        shapes = [format_shape(shape) for shape in self.canvas.shapes]
        # Can add differrent annotation formats here
        try:
            if self.usingPascalVocFormat is True:
                if ustr(annotationFilePath[-4:]) != ".xml":
                    annotationFilePath += XML_EXT
                print ('Img: ' + self.filePath + ' -> Its xml: ' + annotationFilePath)
                self.labelFile.savePascalVocFormat(annotationFilePath, shapes, self.filePath, self.imageData,
                                                   self.lineColor.getRgb(), self.fillColor.getRgb())
            elif self.usingYoloFormat is True:
                if annotationFilePath[-4:] != ".txt":
                    annotationFilePath += TXT_EXT
                print ('Img: ' + self.filePath + ' -> Its txt: ' + annotationFilePath)
                self.labelFile.saveYoloFormat(annotationFilePath, shapes, self.filePath, self.imageData, self.labelHist,
                                                   self.lineColor.getRgb(), self.fillColor.getRgb())
            else:
                self.labelFile.save(annotationFilePath, shapes, self.filePath, self.imageData,
                                    self.lineColor.getRgb(), self.fillColor.getRgb())           
            return True
        except LabelFileError as e:
            self.errorMessage(u'Error saving label data', u'<b>%s</b>' % e)
            return False

    def copySelectedShape(self):
        self.addLabel(self.canvas.copySelectedShape())
        # fix copy and delete
        self.shapeSelectionChanged(True)

    def labelSelectionChanged(self):
        #CJY at 2018.12.11 配合loadxml所做的修改
        if(self.currentItem()):
            if(self.currentItem().text()=="以上为原始框"):
                return 0  
        
        #CJY at 2019.2.13
        items = self.labelList.selectedItems()
        shapes = []
        if len(items)>= 1:
            for item in items:
                if item and self.canvas.editing():
                    self._noSelectionSlot = True
                    
                    shape = self.itemsToShapes[item]
                    shapes.append(shape)
                    # Add Chris
                    self.diffcButton.setChecked(shape.difficult)
            self.canvas.selectShapes(shapes)
            return 1
        
        
        
        ''' #原函数
        item = self.currentItem()
        if item and self.canvas.editing():
            self._noSelectionSlot = True
            self.canvas.selectShape(self.itemsToShapes[item])
            shape = self.itemsToShapes[item]
            # Add Chris
            self.diffcButton.setChecked(shape.difficult)
        '''
            

    def labelItemChanged(self, item):
        shape = self.itemsToShapes[item]
        label = item.text()
        if label != shape.label:
            shape.label = item.text()
            shape.line_color = generateColorByText(shape.label)
            self.setDirty()
        else:  # User probably changed item visibility
            self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)

    # Callback functions:
    def newShape(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """
        if not self.useDefaultLabelCheckbox.isChecked() or not self.defaultLabelTextLine.text():
            if len(self.labelHist) > 0:
                self.labelDialog = LabelDialog(
                    parent=self, listItem=self.labelHist)

            # Sync single class mode from PR#106
            if self.singleClassMode.isChecked() and self.lastLabel:
                text = self.lastLabel
            else:
                text = self.labelDialog.popUp(text=self.prevLabelText)
                self.lastLabel = text
        else:
            text = self.defaultLabelTextLine.text()

        # Add Chris
        self.diffcButton.setChecked(False)
        if text is not None:
            self.prevLabelText = text
            generate_color = generateColorByText(text)
            shape = self.canvas.setLastLabel(text, generate_color, generate_color)
            self.addLabel(shape)
            if self.beginner():  # Switch to edit mode.
                self.canvas.setEditing(True)
                self.actions.create.setEnabled(True)
            else:
                self.actions.editMode.setEnabled(True)
            self.setDirty()

            if text not in self.labelHist:
                self.labelHist.append(text)
        else:
            # self.canvas.undoLastLine()
            self.canvas.resetAllLines()

    def scrollRequest(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scrollBars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * units)

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)

    def addZoom(self, increment=10):
        self.setZoom(self.zoomWidget.value() + increment)

    def zoomRequest(self, delta):
        # get the current scrollbar positions
        # calculate the percentages ~ coordinates
        h_bar = self.scrollBars[Qt.Horizontal]
        v_bar = self.scrollBars[Qt.Vertical]

        # get the current maximum, to know the difference after zooming
        h_bar_max = h_bar.maximum()
        v_bar_max = v_bar.maximum()

        # get the cursor position and canvas size
        # calculate the desired movement from 0 to 1
        # where 0 = move left
        #       1 = move right
        # up and down analogous
        cursor = QCursor()
        pos = cursor.pos()
        relative_pos = QWidget.mapFromGlobal(self, pos)

        cursor_x = relative_pos.x()
        cursor_y = relative_pos.y()

        w = self.scrollArea.width()
        h = self.scrollArea.height()

        # the scaling from 0 to 1 has some padding
        # you don't have to hit the very leftmost pixel for a maximum-left movement
        margin = 0.1
        move_x = (cursor_x - margin * w) / (w - 2 * margin * w)
        move_y = (cursor_y - margin * h) / (h - 2 * margin * h)

        # clamp the values from 0 to 1
        move_x = min(max(move_x, 0), 1)
        move_y = min(max(move_y, 0), 1)

        # zoom in
        units = delta / (8 * 15)
        scale = 10
        self.addZoom(scale * units)

        # get the difference in scrollbar values
        # this is how far we can move
        d_h_bar_max = h_bar.maximum() - h_bar_max
        d_v_bar_max = v_bar.maximum() - v_bar_max

        # get the new scrollbar values
        new_h_bar_value = h_bar.value() + move_x * d_h_bar_max
        new_v_bar_value = v_bar.value() + move_y * d_v_bar_max

        h_bar.setValue(new_h_bar_value)
        v_bar.setValue(new_v_bar_value)

    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def togglePolygons(self, value):
        for item, shape in self.itemsToShapes.items():
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def loadFile(self, filePath=None):
        """Load the specified file, or the last opened file if None."""
        self.resetState()
        self.canvas.setEnabled(False)
        if filePath is None:
            filePath = self.settings.get(SETTING_FILENAME)

        # Make sure that filePath is a regular python string, rather than QString
        filePath = ustr(filePath)

        unicodeFilePath = ustr(filePath)
        # Tzutalin 20160906 : Add file list and dock to move faster
        # Highlight the file item
        if unicodeFilePath and self.fileListWidget.count() > 0:
            index = self.mImgList.index(unicodeFilePath)
            fileWidgetItem = self.fileListWidget.item(index)
            fileWidgetItem.setSelected(True)

        if unicodeFilePath and os.path.exists(unicodeFilePath):
            if LabelFile.isLabelFile(unicodeFilePath):
                try:
                    self.labelFile = LabelFile(unicodeFilePath)
                except LabelFileError as e:
                    self.errorMessage(u'Error opening file',
                                      (u"<p><b>%s</b></p>"
                                       u"<p>Make sure <i>%s</i> is a valid label file.")
                                      % (e, unicodeFilePath))
                    self.status("Error reading %s" % unicodeFilePath)
                    return False
                self.imageData = self.labelFile.imageData
                self.lineColor = QColor(*self.labelFile.lineColor)
                self.fillColor = QColor(*self.labelFile.fillColor)
                self.canvas.verified = self.labelFile.verified
            else:
                # Load image:
                # read data first and store for saving into label file.
                self.imageData = read(unicodeFilePath, None)
                self.labelFile = None
                self.canvas.verified = False

            image = QImage.fromData(self.imageData)
            if image.isNull():
                self.errorMessage(u'Error opening file',
                                  u"<p>Make sure <i>%s</i> is a valid image file." % unicodeFilePath)
                self.status("Error reading %s" % unicodeFilePath)
                return False
            self.status("Loaded %s" % os.path.basename(unicodeFilePath))
            self.image = image
            self.filePath = unicodeFilePath
            self.canvas.loadPixmap(QPixmap.fromImage(image))
            if self.labelFile:
                self.loadLabels(self.labelFile.shapes)
            self.setClean()
            self.canvas.setEnabled(True)
            self.adjustScale(initial=True)
            self.paintCanvas()
            self.addRecentFile(self.filePath)
            self.toggleActions(True)

            # Label xml file and show bound box according to its filename
            # if self.usingPascalVocFormat is True:
            if self.defaultSaveDir is not None:
                basename = os.path.basename(
                    os.path.splitext(self.filePath)[0])
                #CJY at 2019.5.12 增加另一支路
                p,filename = os.path.split(filePath)
                if self.img_xml_namedict.get(filename) !=None:
                    xmlPath = os.path.join(self.defaultSaveDir,self.img_xml_namedict.get(filename))
                    
                    #CJY at 2019.5.13 更新显示信息
                    if self.information != []:
                        subInformation = self.img_xml_namedict.get(filename).split("_")
                        if len(subInformation)==6:
                            print(subInformation)
                            print(self.information)
                            self.information[4] = "大楼位置:  "+"("+subInformation[2]+ "," +subInformation[3]+")"
        
                            self.information[6] = "拍照时间:  " + subInformation[4]
    
                            detectionTime = subInformation[5].split(".")
                            self.information[7] = "识别时间:  "+ detectionTime[0]
                        
                            self.informationListWidget.clear()
                            for infor in self.information:
                                item = QListWidgetItem(infor)
                                self.informationListWidget.addItem(item)
                                
                        else:
                            self.information[4] = "大楼位置:  "+ "Unknown"
        
                            self.information[6] = "拍照时间:  " + "Unknown"
                            
                            self.information[7] = "识别时间:  "+ "Unknown"
                        
                            self.informationListWidget.clear()
                            for infor in self.information:
                                item = QListWidgetItem(infor)
                                self.informationListWidget.addItem(item)
                    
                    
                else:
                    xmlPath = os.path.join(self.defaultSaveDir, basename + XML_EXT)
                    txtPath = os.path.join(self.defaultSaveDir, basename + TXT_EXT)                

                """Annotation file priority:
                PascalXML > YOLO
                """
                if os.path.isfile(xmlPath):
                    self.loadPascalXMLByFilename(xmlPath)
                elif os.path.isfile(txtPath):
                    self.loadYOLOTXTByFilename(txtPath)
            else:
                xmlPath = os.path.splitext(filePath)[0] + XML_EXT
                txtPath = os.path.splitext(filePath)[0] + TXT_EXT
                if os.path.isfile(xmlPath):
                    self.loadPascalXMLByFilename(xmlPath)
                elif os.path.isfile(txtPath):
                    self.loadYOLOTXTByFilename(txtPath)

            self.setWindowTitle(__appname__ + ' ' + filePath)

            # Default : select last item if there is at least one item
            if self.labelList.count():
                self.labelList.setCurrentItem(self.labelList.item(self.labelList.count()-1))
                self.labelList.item(self.labelList.count()-1).setSelected(True)

            self.canvas.setFocus(True)
            return True
        return False

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull()\
           and self.zoomMode != self.MANUAL_ZOOM:
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.zoomWidget.setValue(int(100 * value))

    def scaleFitWindow(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        settings = self.settings
        # If it loads images from dir, don't load it at the begining
        if self.dirname is None:
            settings[SETTING_FILENAME] = self.filePath if self.filePath else ''
        else:
            settings[SETTING_FILENAME] = ''

        settings[SETTING_WIN_SIZE] = self.size()
        settings[SETTING_WIN_POSE] = self.pos()
        settings[SETTING_WIN_STATE] = self.saveState()
        settings[SETTING_LINE_COLOR] = self.lineColor
        settings[SETTING_FILL_COLOR] = self.fillColor
        settings[SETTING_RECENT_FILES] = self.recentFiles
        settings[SETTING_ADVANCE_MODE] = not self._beginner
        if self.defaultSaveDir and os.path.exists(self.defaultSaveDir):
            settings[SETTING_SAVE_DIR] = ustr(self.defaultSaveDir)
        else:
            settings[SETTING_SAVE_DIR] = ""

        if self.lastOpenDir and os.path.exists(self.lastOpenDir):
            settings[SETTING_LAST_OPEN_DIR] = self.lastOpenDir
        else:
            settings[SETTING_LAST_OPEN_DIR] = ""

        settings[SETTING_AUTO_SAVE] = self.autoSaving.isChecked()
        settings[SETTING_SINGLE_CLASS] = self.singleClassMode.isChecked()
        settings[SETTING_PAINT_LABEL] = self.paintLabelsOption.isChecked()
        settings[SETTING_DRAW_SQUARE] = self.drawSquaresOption.isChecked()
        settings.save()
    ## User Dialogs ##

    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    def scanAllImages(self, folderPath):
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        images = []

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = os.path.join(root, file)
                    path = ustr(os.path.abspath(relativePath))
                    images.append(path)
        images.sort(key=lambda x: x.lower())
        return images

    def changeSavedirDialog(self, _value=False):
        if self.defaultSaveDir is not None:
            path = ustr(self.defaultSaveDir)
        else:
            path = '.'

        dirpath = ustr(QFileDialog.getExistingDirectory(self,
                                                       '%s - Save annotations to the directory' % __appname__, path,  QFileDialog.ShowDirsOnly
                                                       | QFileDialog.DontResolveSymlinks))

        if dirpath is not None and len(dirpath) > 1:
            self.defaultSaveDir = dirpath

        self.statusBar().showMessage('%s . Annotation will be saved to %s' %
                                     ('Change saved folder', self.defaultSaveDir))
        self.statusBar().show()

    def openAnnotationDialog(self, _value=False):
        if self.filePath is None:
            self.statusBar().showMessage('Please select image first')
            self.statusBar().show()
            return

        path = os.path.dirname(ustr(self.filePath))\
            if self.filePath else '.'
        if self.usingPascalVocFormat:
            filters = "Open Annotation XML file (%s)" % ' '.join(['*.xml'])
            filename = ustr(QFileDialog.getOpenFileName(self,'%s - Choose a xml file' % __appname__, path, filters))
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]
            self.loadPascalXMLByFilename(filename)

    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return

        defaultOpenDirPath = dirpath if dirpath else '.'
        if self.lastOpenDir and os.path.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = os.path.dirname(self.filePath) if self.filePath else '.'

        targetDirPath = ustr(QFileDialog.getExistingDirectory(self,
                                                     '%s - Open Directory' % __appname__, defaultOpenDirPath,
                                                     QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))
        self.importDirImages(targetDirPath)

    def importDirImages(self, dirpath):
        if not self.mayContinue() or not dirpath:
            return


        self.lastOpenDir = dirpath
        self.dirname = dirpath
        self.filePath = None
        self.fileListWidget.clear()
        self.mImgList = self.scanAllImages(dirpath)
        self.openNextImg()
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            self.fileListWidget.addItem(item)

    def verifyImg(self, _value=False):
        # Proceding next image without dialog if having any label
        if self.filePath is not None:
            try:
                self.labelFile.toggleVerify()
            except AttributeError:
                # If the labelling file does not exist yet, create if and
                # re-save it with the verified attribute.
                self.saveFile()
                if self.labelFile != None:
                    self.labelFile.toggleVerify()
                else:
                    return

            self.canvas.verified = self.labelFile.verified
            self.paintCanvas()
            self.saveFile()

    def openPrevImg(self, _value=False):
        # Proceding prev image without dialog if having any label
        if self.autoSaving.isChecked():
            if self.defaultSaveDir is not None:
                if self.dirty is True:
                    self.saveFile()
            else:
                self.changeSavedirDialog()
                return

        if not self.mayContinue():
            return

        if len(self.mImgList) <= 0:
            return

        if self.filePath is None:
            return

        currIndex = self.mImgList.index(self.filePath)
        if currIndex - 1 >= 0:
            filename = self.mImgList[currIndex - 1]
            if filename:
                self.loadFile(filename)

    def openNextImg(self, _value=False):
        # Proceding prev image without dialog if having any label
        if self.autoSaving.isChecked():
            if self.defaultSaveDir is not None:
                if self.dirty is True:
                    self.saveFile()
            else:
                self.changeSavedirDialog()
                return

        if not self.mayContinue():
            return

        if len(self.mImgList) <= 0:
            return

        filename = None
        if self.filePath is None:
            filename = self.mImgList[0]
        else:
            currIndex = self.mImgList.index(self.filePath)
            if currIndex + 1 < len(self.mImgList):
                filename = self.mImgList[currIndex + 1]

        if filename:
            self.loadFile(filename)

    def openFile(self, _value=False):
        if not self.mayContinue():
            return
        path = os.path.dirname(ustr(self.filePath)) if self.filePath else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats + ['*%s' % LabelFile.suffix])
        filename = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.loadFile(filename)

    def saveFile(self, _value=False):
        if self.defaultSaveDir is not None and len(ustr(self.defaultSaveDir)):
            if self.filePath:
                #CJY at 2019.5.12 增加另一支路
                print("save",self.filePath)
                p,filename = os.path.split(self.filePath)
                if self.img_xml_namedict.get(filename) !=None:
                    savedPath = os.path.join(self.defaultSaveDir,self.img_xml_namedict.get(filename))
                    
                    
                else:
                    imgFileName = os.path.basename(self.filePath)
                    savedFileName = os.path.splitext(imgFileName)[0]
                    savedPath = os.path.join(ustr(self.defaultSaveDir), savedFileName)
                self._saveFile(savedPath)
                
                #CJY at 2019.5.22 生成缩略图
                #1.首先删除原始缩略图
                #errPath = os.path.dirname(self.defaultSaveDir)   
                #if os.path.exists(os.path.join(errPath,"err"))!=True:
                #    os.mkdir(os.path.join(errPath,"err"))
                #errlist = os.listdir(os.path.join(errPath,"err"))
                
                errPath = self.defaultSaveDir
                errlist = os.listdir(errPath)
                
                xml_pre = os.path.splitext(self.img_xml_namedict.get(filename))[0]
                for err_name in errlist:
                    en_pre,en_ext = os.path.splitext(err_name)
                    if en_ext == ".xml" or en_ext == ".XML" :
                        continue
                    if err_name.find(xml_pre)!= -1:
                        exist_errfullname = os.path.join(errPath,err_name)
                        os.remove(exist_errfullname)

                if os.path.exists(errPath) != True:
                    os.makedirs(errPath)
                outputErrThumb = th.GenerationErrThumb2(self.filePath,savedPath,errPath,self.deleteNum,10)
                
                
                
        else:
            imgFileDir = os.path.dirname(self.filePath)
            imgFileName = os.path.basename(self.filePath)
            savedFileName = os.path.splitext(imgFileName)[0]
            savedPath = os.path.join(imgFileDir, savedFileName)
            self._saveFile(savedPath if self.labelFile
                           else self.saveFileDialog())

    def saveFileAs(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        self._saveFile(self.saveFileDialog())

    def saveFileDialog(self):
        caption = '%s - Choose File' % __appname__
        filters = 'File (*%s)' % LabelFile.suffix
        openDialogPath = self.currentPath()
        dlg = QFileDialog(self, caption, openDialogPath, filters)
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        filenameWithoutExtension = os.path.splitext(self.filePath)[0]
        dlg.selectFile(filenameWithoutExtension)
        dlg.setOption(QFileDialog.DontUseNativeDialog, False)
        if dlg.exec_():
            fullFilePath = ustr(dlg.selectedFiles()[0])
            return os.path.splitext(fullFilePath)[0] # Return file path without the extension.
        return ''

    def _saveFile(self, annotationFilePath):
        if annotationFilePath and self.saveLabels(annotationFilePath):
            self.setClean()
            self.statusBar().showMessage('Saved to  %s' % annotationFilePath)
            self.statusBar().show()

    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    def resetAll(self):
        self.settings.reset()
        self.close()
        proc = QProcess()
        proc.startDetached(os.path.abspath(__file__))

    def mayContinue(self):
        return not (self.dirty and not self.discardChangesDialog())

    def discardChangesDialog(self):
        yes, no = QMessageBox.Yes, QMessageBox.No
        msg = self.tr(u'You have unsaved changes, proceed anyway?')
        return yes == QMessageBox.warning(self, self.tr(u'Attention'), msg, yes | no)

    def errorMessage(self, title, message):
        return QMessageBox.critical(self, title,
                                    '<p><b>%s</b></p>%s' % (title, message))

    def currentPath(self):
        return os.path.dirname(self.filePath) if self.filePath else '.'

    def chooseColor1(self):
        color = self.colorDialog.getColor(self.lineColor, u'Choose line color',
                                          default=DEFAULT_LINE_COLOR)
        if color:
            self.lineColor = color
            Shape.line_color = color
            self.canvas.setDrawingColor(color)
            self.canvas.update()
            self.setDirty()

    def deleteSelectedShape(self):
        #CJY at 2019.2.13 更改remLabel为remLabels，更改deleteSelected为MutideleteSelected，变单选为多选删除
        self.remLabels(self.canvas.MutideleteSelected())
        self.setDirty()
        if self.noShapes():
            for action in self.actions.onShapesPresent:
                action.setEnabled(False)

    def chshapeLineColor(self):
        color = self.colorDialog.getColor(self.lineColor, u'Choose line color',
                                          default=DEFAULT_LINE_COLOR)
        if color:
            self.canvas.selectedShape.line_color = color
            self.canvas.update()
            self.setDirty()

    def chshapeFillColor(self):
        color = self.colorDialog.getColor(self.fillColor, u'Choose fill color',
                                          default=DEFAULT_FILL_COLOR)
        if color:
            self.canvas.selectedShape.fill_color = color
            self.canvas.update()
            self.setDirty()

    def copyShape(self):
        self.canvas.endMove(copy=True)
        self.addLabel(self.canvas.selectedShape)
        self.setDirty()

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()

    def loadPredefinedClasses(self, predefClassesFile):
        if os.path.exists(predefClassesFile) is True:
            with codecs.open(predefClassesFile, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip()
                    if self.labelHist is None:
                        self.labelHist = [line]
                    else:
                        self.labelHist.append(line)

    def loadPascalXMLByFilename(self, xmlPath):
        if self.filePath is None:
            return
        if os.path.isfile(xmlPath) is False:
            return

        self.set_format(FORMAT_PASCALVOC)

        tVocParseReader = PascalVocReader(xmlPath)
        shapes = tVocParseReader.getShapes()
        self.loadLabels(shapes)
        self.canvas.verified = tVocParseReader.verified
        
        #CJY at 2018.12.11 
        information = []
        information.append("以上为原始框")       
        item = QListWidgetItem(information[0])
        #CJY at 2019.2.14 设置该item为不可选中
        item.setFlags(Qt.ItemIsEditable)
        self.labelList.addItem(item)
        self.toggleNormalPolygons(False)
        '''
        for infor in information:
            item = QListWidgetItem(infor)
            self.informationListWidget.addItem(item)
        print("123131")
        '''

    def loadYOLOTXTByFilename(self, txtPath):
        if self.filePath is None:
            return
        if os.path.isfile(txtPath) is False:
            return

        self.set_format(FORMAT_YOLO)
        tYoloParseReader = YoloReader(txtPath, self.image)
        shapes = tYoloParseReader.getShapes()
        print (shapes)
        self.loadLabels(shapes)
        self.canvas.verified = tYoloParseReader.verified

    def togglePaintLabelsOption(self):
        paintLabelsOptionChecked = self.paintLabelsOption.isChecked()
        for shape in self.canvas.shapes:
            shape.paintLabel = paintLabelsOptionChecked

    def toogleDrawSquare(self):
        self.canvas.setDrawingShapeToSquare(self.drawSquaresOption.isChecked())
        
    # CJY 2018.12.11
    def importLegend(self):
        item = QListWidgetItem("break               缺碎砖")
        self.legendListWidget.addItem(item)
        item = QListWidgetItem("crack               裂缝")
        self.legendListWidget.addItem(item)
        item = QListWidgetItem("rebar               钢筋")
        self.legendListWidget.addItem(item)
        item = QListWidgetItem("sundries          杂物")
        self.legendListWidget.addItem(item)
        #item = QListWidgetItem("suspect           疑似")
        #self.legendListWidget.addItem(item)
        item = QListWidgetItem("swell                鼓包")
        self.legendListWidget.addItem(item)
        item = QListWidgetItem("distortion       变形")
        self.legendListWidget.addItem(item)
        item = QListWidgetItem("normal            正常")
        self.legendListWidget.addItem(item)
        
    # CJY&ZZX 2018.12.04
    def importInformation(self,argv=[]):
        original_information = argv[1].split("\\")
        if len(original_information)==1:
            original_information = argv[1].split("/")
        print(original_information)
        self.information = []
        self.information.append("巡检编号:  "+ original_information[0])
        
        self.information.append("日期:         "+ original_information[1])
            
        self.information.append("大楼编号:  "+str(int(original_information[2])%1000))
            
        if original_information[3]=="1":
            self.information.append("大楼朝向:  "+"C")
        elif original_information[3]=="2":
            self.information.append("大楼朝向:  "+"B")
        elif original_information[3]=="3":
            self.information.append("大楼朝向:  "+"D")
        else:
            self.information.append("大楼朝向:  "+"A")
    
        subInformation = original_information[5].split("_")
        self.information.append("大楼位置:  "+"("+subInformation[2]+ "," +subInformation[3]+")")
        
        from base64 import b64decode
        base64_decrypt = b64decode(argv[2].encode('utf-8'))
        self.information.append("巡检人:      "+str(base64_decrypt,'utf-8'))
    
        self.information.append("拍照时间:  " + subInformation[4])
    
        detectionTime = subInformation[5].split(".")
        self.information.append("识别时间:  "+ detectionTime[0])
    
        
        '''
        print(information[0])
        print(information[1])
        print(information[2])
        print(information[3]) 
        print(information[4])
        print(information[5]) 
        print(information[6])
        print(information[7])
        '''  
        
        self.informationListWidget.clear()
        for infor in self.information:
            item = QListWidgetItem(infor)
            self.informationListWidget.addItem(item)
            
    def importInformationForLabelCopy(self,argv2,argv2_org):
        self.LabelCopyArg=argv2
        self.LabelCopyArg_org=argv2_org
    
    # CJY at 2018.12.05
    def compareWithHistoricalImage(self, _value=False):       
        
        
        # Load setting in the main thread
        '''
        self.settings = Settings()
        self.settings.load()          
        settings = self.settings
        size = settings.get(SETTING_WIN_SIZE, QSize(600, 500))        
        w=self.width()/2
        h=self.height()   
        '''
        wW = ctypes.windll.user32.GetSystemMetrics(0)/2
        wH = ctypes.windll.user32.GetSystemMetrics(1)-100
        self.resize(wW,wH)
        self.move(QPoint(0,0))
        
        argv = self.LabelCopyArg
        argv_org = self.LabelCopyArg_org
        if(len(argv) == 4):   
            '''
            win_copy = labelImg_copy. MainWindow(argv[0] if len(argv) >= 2 else None,
                     argv[1] if len(argv) >= 3 else os.path.join(
                         os.path.dirname(sys.argv[0]),
                         'predefClass.txt'),  #'data', 'predefined_classes.txt'
                     argv[2] if len(argv) >= 4 else None,
                     transFilePath = os.path.dirname(argv[0]))  #CJY at 20181205
            '''
            win_copy = MainWindow(argv[0] if len(argv) >= 1 else None,
                     argv[1] if len(argv) >= 2 else os.path.join(
                         os.path.dirname(sys.argv[0]),
                         'predefClass.txt'),  #'data', 'predefined_classes.txt'
                     argv[2] if len(argv) >= 3 else None,
                     argv[3] if len(argv) >= 4 else {})  #CJY at 20181205
            if(len(argv_org)==3):
                win_copy.importInformation(argv_org)   
            win_copy.show()
        
        
    # CJY at 2018.12.24
    def clearLabels(self):         
        while(len(self.labelList)!=0):
            #print(len(self.labelList))
            self.labelList.setCurrentRow(0)
            if(self.currentItem()):
                if(self.currentItem().text()=="以上为原始框"):
                    break       
            self.deleteSelectedShape()
            
    #CJY at 2019.01.17 切换normal标签的项是否显示
    def toggleNormalPolygons(self, value): 
        if value == True:  #翻转
            self.tNPflag = not self.tNPflag
            for item, shape in self.itemsToShapes.items():
                if(item.text()=="normal"):
                    item.setCheckState(Qt.Checked if self.tNPflag else Qt.Unchecked)
        else: #保持
            for item, shape in self.itemsToShapes.items():
                if(item.text()=="normal"):
                    item.setCheckState(Qt.Checked if self.tNPflag else Qt.Unchecked)
    
    #CJY at 2019.01.21
    def changeLabeltoNormal(self):
        if not self.canvas.editing():
            return
        #CJY at 2019.2.14 优化changenormal为多选模式
        items = self.labelList.selectedItems()
        for item in self.labelList.selectedItems():
            text = "normal"
            if text is not None:
                item.setText(text)
                item.setBackground(generateColorByText(text))
        self.setDirty()       
        self.toggleNormalPolygons(False)
        
        '''
        item = self.currentItem()
        #text = self.labelDialog.popUp(item.text())
        text = "normal"
        if text is not None:
            item.setText(text)
            item.setBackground(generateColorByText(text))
            self.setDirty()
        '''
    
    #CJY at 2019.2.13  add 多选功能   好像并不需要了，我融合到editing模式里了，不用按按键启动，按住左键即进入
    def createMultiSelect(self):
        assert self.beginner()
        self.canvas.setSelecting()
        #self.actions.create.setEnabled(False) 
        
    #CJY at 2019.2.13 
    # Callback functions:  仿newShape
    def multiSelectShapes(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """        
        self.diffcButton.setChecked(False)
        text = "break"
        if text is not None:
            self.prevLabelText = text
            generate_color = generateColorByText(text)
            shape = self.canvas.setLastLabel(text, generate_color, generate_color)
            self.addLabel(shape)
            if self.beginner():  # Switch to edit mode.
                self.canvas.setEditing(True)
                self.actions.create.setEnabled(True)
            else:
                self.actions.editMode.setEnabled(True)
            self.setDirty()

            if text not in self.labelHist:
                self.labelHist.append(text)
        else:
            # self.canvas.undoLastLine()
            self.canvas.resetAllLines()
        
        #判断shapes里哪些在选中框之中
        selectionRect = self.canvas.shapes[-1].points
        xmin = min(shape.points[0].x(),shape.points[2].x())
        ymin = min(shape.points[0].y(),shape.points[2].y())
        xmax = max(shape.points[0].x(),shape.points[2].x())
        ymax = max(shape.points[0].y(),shape.points[2].y())
        itemIndexList = []
        for shape in self.canvas.shapes:
            if shape.label == "normal" and self.tNPflag == False:
                continue
            shape_LTPoints = shape.points[0]            
            shape_RDPoints = shape.points[2]            
            if(shape_LTPoints.x()>=xmin) and (shape_LTPoints.y()>=ymin) and (shape_RDPoints.x()<=xmax) and (shape_RDPoints.y()<=ymax):
                self.labelList.row(self.shapesToItems[shape])
                #print("index",self.labelList.row(self.shapesToItems[shape]))
                itemIndexList.append(self.labelList.row(self.shapesToItems[shape]))
            #print(len(allShapes))
        
        #首先删除最后一个 (最后一个其实就是选择框本身)       
        self.labelList.setCurrentRow(len(self.labelList)-1)
        self.labelSelectionChanged()
        self.deleteSelectedShape()
        
        for i in itemIndexList:
            self.labelList.setCurrentRow(i,QItemSelectionModel.Select)            
        self.labelSelectionChanged()
        '''
        if not self.useDefaultLabelCheckbox.isChecked() or not self.defaultLabelTextLine.text():
            if len(self.labelHist) > 0:
                self.labelDialog = LabelDialog(
                    parent=self, listItem=self.labelHist)

            # Sync single class mode from PR#106
            if self.singleClassMode.isChecked() and self.lastLabel:
                text = self.lastLabel
            else:
                text = self.labelDialog.popUp(text=self.prevLabelText)
                self.lastLabel = text
        else:
            text = self.defaultLabelTextLine.text()

        # Add Chris
        self.diffcButton.setChecked(False)
        if text is not None:
            self.prevLabelText = text
            generate_color = generateColorByText(text)
            shape = self.canvas.setLastLabel(text, generate_color, generate_color)
            self.addLabel(shape)
            if self.beginner():  # Switch to edit mode.
                self.canvas.setEditing(True)
                self.actions.create.setEnabled(True)
            else:
                self.actions.editMode.setEnabled(True)
            self.setDirty()

            if text not in self.labelHist:
                self.labelHist.append(text)
        else:
            # self.canvas.undoLastLine()
            self.canvas.resetAllLines()
        '''
    def openDirByFile(self,fullfilename):        
        filepath,fname = os.path.split(fullfilename)
        self.importDirImages(filepath)                 
        self.loadFile(fullfilename)        
        
    
    

def inverted(color):
    return QColor(*[255 - v for v in color.getRgb()])


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except:
        return default


