# -*- coding: utf-8 -*-
#
# To build simple dialogues etc. (requires pyqt4)
#
#  Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from psychopy import logging
import numpy as np
import string, os, sys, json
from psychopy.app import localization

OK = QtGui.QDialogButtonBox.Ok

qtapp = None

def ensureQtApp():
    global qtapp
    # make sure there's a wxApp prior to showing a gui, e.g., for expInfo dialog
    if qtapp is None:
        qtapp = QtGui.QApplication(sys.argv)
    return qtapp


wasMouseVisible = True

class Dlg(QtGui.QDialog):
    """A simple dialogue box. You can add text or input boxes
    (sequentially) and then retrieve the values.

    see also the function *dlgFromDict* for an **even simpler** version

    **Example:**    ::

        from psychopy import gui

        myDlg = gui.Dlg(title="JWP's experiment")
        myDlg.addText('Subject info')
        myDlg.addField('Name:')
        myDlg.addField('Age:', 21)
        myDlg.addText('Experiment Info')
        myDlg.addField('Grating Ori:',45)
        myDlg.addField('Group:', choices=["Test", "Control"])
        ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
        if myDlg.OK:  # or if ok_data is not None
            print(ok_data)
        else:
            print('user cancelled')
    """

    def __init__(self, title=_translate('PsychoPy Dialog'),
                 pos=None, size=None, style=None,
                 labelButtonOK=_translate(" OK "),
                 labelButtonCancel=_translate(" Cancel "),
                 screen=-1):

        global app  # avoid recreating for every gui
        app = ensureQtApp()
        QtGui.QDialog.__init__(self, None, Qt.WindowTitleHint)

        self.inputFields = []
        self.inputFieldTypes = []
        self.inputFieldNames = []
        self.data = []
        self.irow = 0

        #QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))

        #add buttons for OK and Cancel
        self.buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal, parent=self)
        self.okbutton = QtGui.QPushButton(labelButtonOK, parent=self)
        self.cancelbutton = QtGui.QPushButton(labelButtonCancel, parent=self)
        self.buttonBox.addButton(self.okbutton,
                                 QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.cancelbutton,
                                 QtGui.QDialogButtonBox.ActionRole)
        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton.clicked.connect(self.reject)

        if style:
            raise RuntimeWarning(
                "Dlg does not currently support the stype kwarg.")

        self.pos = pos
        self.size = size
        self.screen = screen
        #self.labelButtonOK = labelButtonOK
        #self.labelButtonCancel = labelButtonCancel

        self.layout = QtGui.QGridLayout()
        self.layout.setColumnStretch(1, 1)
        self.layout.setSpacing(10)
        self.layout.setColumnMinimumWidth(1, 250)

        self.setLayout(self.layout)

        self.setWindowTitle(title)


    def addText(self, text, color='', isFieldLabel=False):
        textLabel = QtGui.QLabel(text, parent=self)

        if len(color):
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QtGui.QColor(color))
            textLabel.setPalette(palette)

        if isFieldLabel is True:
            self.layout.addWidget(textLabel, self.irow, 0, 1, 1)
        else:
            self.layout.addWidget(textLabel, self.irow, 0, 1, 2)
            self.irow += 1

        return textLabel


    def addField(self, label='', initial='', color='', choices=None, tip='',
                 enabled=True):
        """
        Adds a (labelled) input field to the dialogue box, optional text color
        and tooltip.

        If 'initial' is a bool, a checkbox will be created.
        If 'choices' is a list or tuple, a dropdown selector is created.
        Otherwise, a text line entry box is created.

        Returns a handle to the field (but not to the label).
        """
        self.inputFieldNames.append(label)
        if choices:
            self.inputFieldTypes.append(str)
        else:
            self.inputFieldTypes.append(type(initial))
        if type(initial) == np.ndarray:
            initial = initial.tolist()  #convert numpy arrays to lists

        #create label
        inputLabel = self.addText(label, color, isFieldLabel=True)

        #create input control
        if type(initial) == bool and not choices:
            self.data.append(initial)
            inputBox = QtGui.QCheckBox(parent=self)
            inputBox.setChecked(initial)

            def handleCheckboxChange(new_state):
                ix = self.inputFields.index(inputBox)
                self.data[ix] = inputBox.isChecked()
                logging.debug(
                    "handleCheckboxChange: inputFieldName={0}, "
                    "checked={1}".format(label, self.data[ix]))

            inputBox.stateChanged.connect(handleCheckboxChange)
        elif not choices:
            self.data.append(initial)
            inputBox = QtGui.QLineEdit(unicode(initial), parent=self)

            def handleLineEditChange(new_text):
                ix = self.inputFields.index(inputBox)
                thisType = self.inputFieldTypes[ix]

                try:
                    if thisType in (str, unicode):
                        self.data[ix] = unicode(new_text)
                    elif thisType == tuple:
                        jtext = "[" + unicode(new_text) + "]"
                        self.data[ix] = json.loads(jtext)[0]
                    elif thisType == list:
                        jtext = "[" + unicode(new_text) + "]"
                        self.data[ix] = json.loads(jtext)[0]
                    elif thisType == float:
                        self.data[ix] = string.atof(str(new_text))
                    elif thisType == int:
                        self.data[ix] = string.atoi(str(new_text))
                    elif thisType == long:
                        self.data[ix] = string.atol(str(new_text))
                    elif thisType == dict:
                        jtext = "[" + unicode(new_text) + "]"
                        self.data[ix] = json.loads(jtext)[0]
                    elif thisType == np.ndarray:
                        self.data[ix] = np.array(
                            json.loads("[" + unicode(new_text) + "]")[0])
                    else:
                        self.data[ix] = new_text
                        logging.warning(
                            "Unknown type in handleLineEditChange: "
                            "inputFieldName={0}, type={1}, value={2}".format(
                                label, thisType, self.data[ix]))
                    logging.debug(
                        "handleLineEditChange: inputFieldName={0}, type={1}, "
                        "value={2}".format(
                            label, thisType, self.data[ix]))
                except Exception as e:
                    self.data[ix] = unicode(new_text)
                    logging.error(
                        'Error in handleLineEditChange: inputFieldName={0}, '
                        'type={1}, value={2}, error={3}'.format(
                            label, thisType, self.data[ix], e))

            inputBox.textEdited.connect(handleLineEditChange)
        else:
            inputBox = QtGui.QComboBox(parent=self)
            choices = list(choices)
            for i, option in enumerate(choices):
                inputBox.addItem(unicode(option))
                #inputBox.addItems([unicode(option) for option in choices])
                inputBox.setItemData(i, (option,))

            if isinstance(initial, (int, long)) and len(choices) > initial >= 0:
                pass
            elif initial in choices:
                initial = choices.index(initial)
            else:
                initial = 0
            inputBox.setCurrentIndex(initial)

            self.data.append(choices[initial])

            def handleCurrentIndexChanged(new_index):
                ix = self.inputFields.index(inputBox)
                self.data[ix] = inputBox.itemData(new_index).toPyObject()[0]
                logging.debug(
                    "handleCurrentIndexChanged: inputFieldName={0}, "
                    "selected={1}, type: {2}".format(
                        label, self.data[ix], type(self.data[ix])))

            inputBox.currentIndexChanged.connect(handleCurrentIndexChanged)

        if len(color):
            inputBox.setPalette(inputLabel.palette())
        if len(tip):
            inputBox.setToolTip(tip)
        inputBox.setEnabled(enabled)
        self.layout.addWidget(inputBox, self.irow, 1)

        self.inputFields.append(inputBox)  #store this to get data back on OK
        self.irow += 1

        return inputBox

    def addFixedField(self, label='', initial='', color='', choices=None,
                      tip=''):
        """Adds a field to the dialog box (like addField) but the field cannot
        be edited. e.g. Display experiment version.
        """
        return self.addField(label, initial, color, choices, tip, enabled=False)

    def display(self):
        """
        Presents the dialog and waits for the user to press either OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.

        :return: self.data
        """
        return self.exec_()

    def show(self):
        """
        ** QDialog already has a show() method. So this method calls
           QDialog.show() and then exec_(). This seems to not cause issues,
           however we need to keep an eye out for any issues.

        ** Deprecated: Use dlg.display() instead. This method will be removed
           in a future version of psychopy.

        Presents the dialog and waits for the user to press either OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.

        :return: self.data
        """
        return self.display()

    def exec_(self):
        """
        Presents the dialog and waits for the user to press either OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.
        """

        self.layout.addWidget(self.buttonBox, self.irow, 0, 1, 2)

        # Center Dialog on appropriate screen
        frameGm = self.frameGeometry()
        desktop = QtGui.QApplication.desktop()
        qtscreen = self.screen
        if self.screen <= 0:
            qtscreen = desktop.primaryScreen()
        centerPoint = desktop.screenGeometry(qtscreen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

        QtGui.QDialog.show(self)
        self.raise_()
        self.activateWindow()

        self.OK = False
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            self.OK = True
            return self.data

class DlgFromDict(Dlg):
    """Creates a dialogue box that represents a dictionary of values.
    Any values changed by the user are change (in-place) by this
    dialogue box.
    e.g.:

    ::

        info = {'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1, 'Group': ['Test', 'Control']}
        dictDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment', fixed=['ExpVersion'])
        if dictDlg.OK:
            print(info)
        else:
            print('User Cancelled')

    In the code above, the contents of *info* will be updated to the values
    returned by the dialogue box.

    If the user cancels (rather than pressing OK),
    then the dictionary remains unchanged. If you want to check whether
    the user hit OK, then check whether DlgFromDict.OK equals
    True or False

    See GUI.py for a usage demo, including order and tip (tooltip).
    """
    def __init__(self, dictionary, title='',fixed=[], order=[], tip={}, screen=-1):
        Dlg.__init__(self, title, screen=screen)
        self.dictionary = dictionary
        keys = self.dictionary.keys()
        keys.sort()
        if len(order):
            keys = order + list(set(keys).difference(set(order)))
        types=dict([])
        for field in keys:
            types[field] = type(self.dictionary[field])
            tooltip = ''
            if field in tip.keys():
                tooltip = tip[field]
            if field in fixed:
                self.addFixedField(field, self.dictionary[field], tip=tooltip)
            elif type(self.dictionary[field]) in [list, tuple]:
                self.addField(field,choices=self.dictionary[field], tip=tooltip)
            else:
                self.addField(field, self.dictionary[field], tip=tooltip)

        ok_data = self.exec_()
        if ok_data:
            for n,thisKey in enumerate(keys):
                self.dictionary[thisKey]=ok_data[n]


def fileSaveDlg(initFilePath="", initFileName="",
                prompt=_translate("Select file to save"),
                allowed=None):
    """A simple dialogue allowing write access to the file system.
    (Useful in case you collect an hour of data and then try to
    save to a non-existent directory!!)

    :parameters:
        initFilePath: string
            default file path on which to open the dialog
        initFileName: string
            default file name, as suggested file
        prompt: string (default "Select file to open")
            can be set to custom prompts
        allowed: string
            a string to specify file filters.
            e.g. "Text files (*.txt) ;; Image files (*.bmp *.gif)"
            See http://pyqt.sourceforge.net/Docs/PyQt4/qfiledialog.html
            #getSaveFileName
            for further details

    If initFilePath or initFileName are empty or invalid then
    current path and empty names are used to start search.

    If user cancels the None is returned.
    """
    if allowed is None:
        allowed = "All files (*.*);;" \
                  "txt (*.txt);;" \
                  "pickled files (*.pickle *.pkl);;" \
                  "shelved files (*.shelf)"
    global qtapp  # avoid recreating for every gui
    qtapp = ensureQtApp()

    r = QtGui.QFileDialog.getSaveFileName(parent=None,
                                          caption=prompt,
                                          directory=os.path.join(initFilePath,
                                                                 initFileName),
                                          filter=allowed)
    if len(r) == 0:
        return None
    return unicode(r)


def fileOpenDlg(tryFilePath="",
                tryFileName="",
                prompt=_translate("Select file to open"),
                allowed=None):
    """A simple dialogue allowing read access to the file system.

    :parameters:
        tryFilePath: string
            default file path on which to open the dialog
        tryFileName: string
            default file name, as suggested file
        prompt: string (default "Select file to open")
            can be set to custom prompts
        allowed: string (available since v1.62.01)
            a string to specify file filters.
            e.g. "Text files (*.txt) ;; Image files (*.bmp *.gif)"
            See http://pyqt.sourceforge.net/Docs/PyQt4/qfiledialog.html
            #getOpenFileNames
            for further details

    If tryFilePath or tryFileName are empty or invalid then
    current path and empty names are used to start search.

    If user cancels, then None is returned.
    """
    global qtapp  # avoid recreating for every gui
    qtapp = ensureQtApp()

    if allowed is None:
        allowed = "All files (*.*);;" \
                  "PsychoPy Data (*.psydat);;" \
                  "txt (*.txt *.dlm *.csv);;" \
                  "pickled files (*.pickle *.pkl);;" \
                  "shelved files (*.shelf)"
    filesToOpen = QtGui.QFileDialog.getOpenFileNames(parent=None,
                                                     caption=prompt,
                                                     directory=os.path.join(
                                                         tryFilePath,
                                                         tryFileName),
                                                     filter=allowed)

    filesToOpen = [unicode(fpath) for fpath in filesToOpen if
                   os.path.exists(fpath)]
    if len(filesToOpen) == 0:
        return None
    return filesToOpen


def infoDlg(title=_translate("Information"),
            prompt=_translate(
                "No details provided. ('prompt' value not set).")):
    global qtapp  # avoid recreating for every gui
    qtapp = ensureQtApp()
    QtGui.QMessageBox.information(None,
                                  title,
                                  prompt)


def warnDlg(title=_translate("Warning"),
            prompt=_translate(
                "No details provided. ('prompt' value not set).")):
    global qtapp  # avoid recreating for every gui
    qtapp = ensureQtApp()
    QtGui.QMessageBox.warning(None,
                              title,
                              prompt)


def criticalDlg(title=_translate("Critical"),
                prompt=_translate(
                    "No details provided. ('prompt' value not set).")):
    global qtapp  # avoid recreating for every gui
    qtapp = ensureQtApp()
    QtGui.QMessageBox.critical(None,
                               title,
                               prompt)


def aboutDlg(title=_translate("About Experiment"),
             prompt=_translate(
                 "No details provided. ('prompt' value not set).")):
    global qtapp  # avoid recreating for every gui
    qtapp = ensureQtApp()
    QtGui.QMessageBox.about(None,
                            title,
                            prompt)


#
## Psychopy pyglet window show / hide util functions
#

def hideWindow(win):
    global wasMouseVisible
    if win.winHandle._visible is True:
        win.winHandle.set_visible(False)
        win.winHandle.minimize()
        wasMouseVisible = win.winHandle._mouse_visible
        win.winHandle.set_mouse_visible(True)


def showWindow(win):
    global wasMouseVisible
    if win.winHandle._visible is False:
        win.winHandle.set_mouse_visible(wasMouseVisible)
        win.winHandle.maximize()
        win.winHandle.set_visible(True)
        win.winHandle.activate()


if __name__ == '__main__':
    # Local manual test cases for dialog types....

    logging.console.setLevel(logging.DEBUG)

    # from psychopy import visual, event
    # Create, and hide, a full screen psychopy window
    # win = visual.Window([1024, 768],
    #                    fullscr=True,
    #                    allowGUI=False,
    #                    screen=0)
    # hideWindow(win)

    # Test base Dlg class

    dlg = Dlg()
    dlg.addText("This is a line of text", color="Red")
    dlg.addText("Second line of text")
    dlg.addField("A checkbox", initial=True, tip="Here is your checkbox tip!")
    dlg.addField("Another checkbox", initial=False, color="Blue")
    dlg.addFixedField("ReadOnly checkbox", initial=False, color="Blue",
                      tip="This field is readonly.")
    dlg.addField("A textline", initial="",
                 tip="Here is your <b>textline</b> tip!")
    dlg.addField("A Number:", initial=23, tip="This must be a number.")
    dlg.addField("A List:", initial=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                 tip="This must be a list.")
    dlg.addField("A ndarray:",
                 initial=np.asarray([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
                 tip="This must be a numpy array.")
    dlg.addField("Another textline", initial="default text", color="Green")
    dlg.addFixedField("ReadOnly textline", initial="default text",
                      tip="This field is readonly.")
    dlg.addField("A dropdown", initial='B', choices=['A', 'B', 'C'],
                 tip="Here is your <b>dropdown</b> tip!")

    dlg.addField("Mixed type dropdown", initial=2, choices=['A String', 1234567,
                                                            [12.34, 56.78],
                                                            ('tuple element 0',
                                                             'tuple element 1'),
                                                            {'key1': 'val1',
                                                             'key2': 23}],
                 color="Red")

    dlg.addField("Yet Another dropdown", choices=[1, 2, 3])
    dlg.addFixedField("ReadOnly dropdown", initial=2,
                      choices=['R1', 'R2', 'R3'], tip="This field is readonly.")
    ok_data = dlg.show()
    print("Dlg ok_data:", ok_data)

    # Test Dict Dialog

    info = {'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1, 'Group': ['Test', 'Control']}
    dictDlg = DlgFromDict(dictionary=info, title='TestExperiment', fixed=['ExpVersion'])
    if dictDlg.OK:
        print(info)
    else:
        print('User Cancelled')


    # Test File Dialogs

    fileToSave = fileSaveDlg(initFileName='__init__.pyc')
    print("fileToSave: [", fileToSave, "]", type(fileToSave))

    fileToOpen = fileOpenDlg()
    print("fileToOpen:", fileToOpen)

    # Test Alert Dialogs

    infoDlg(prompt="Some not important info for you.")

    warnDlg(prompt="Something non critical,\nbut still worth telling you about,\noccurred.")

    criticalDlg(title="RuntimeError", prompt="Oh boy, something really bad just happened:"
                                             "<br>"
                                             "<b>{0}</b>".format(RuntimeError("A made up runtime error")))

    aboutDlg(prompt=u"My Experiment v. 1.0"
             u"<br>"
             u"Written by: Dr. John Doe"
             u"<br>"
             u"Created using <b>PsychoPy</b> © Copyright 2015, Jonathan Peirce")


    # Restore full screen psychopy window
    # showWindow(win)
    # win.flip()
    #from psychopy import event
    #event.waitKeys()