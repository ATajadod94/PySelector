import collections

import json
import os
import wx
from wx import *


class SettingFrame(wx.Frame):
    """
    The only frame for the setting window
    """
    def __init__(self, parent, setting_folder):
        """
        The constructor method creates and fits the panel for setting window.
        :param parent:
        :param setting_folder:
        """
        super().__init__(parent=parent)

        # Attributes
        self.parent = parent
        self.MainPanel = MainSettingPanel(self, setting_folder)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.MainPanel, wx.GROW)
        self.SetSizerAndFit(sizer)


class MainSettingPanel(wx.Panel):
    """
    The mainsettingpanell contains the settingpanel, settinglist and the buttonpanel for interaction
    """
    def __init__(self, parent, setting_folder):
        """
        The constructor method creates the setting panel , the setting list and the button panel. It also creates and
        sets the sizer for the main panel and binds buttons.
        :param parent:
        :param setting_folder:
        """
        super().__init__(parent=parent)
        self.parent = parent

        self.settingpanel = SettingPanel(self)
        self.settinglist = SettingsList(self, setting_folder)
        self.buttonpanel = SettingButtonPanel(self)
        self.setting_folder = setting_folder
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.settinglist, 1, wx.GROW)
        sizer.Add(self.buttonpanel, 1, wx.GROW)
        sizer.Add(self.settingpanel, 1, wx.GROW)
        self.SetSizer(sizer)
        self.settingdata = collections.defaultdict(dict)

        self.buttonpanel.savebutton.Bind(EVT_BUTTON, self.save)
        self.buttonpanel.loadbutton.Bind(EVT_BUTTON, self.load)

    def save(self, e):
        """
        the save method is bound to the save button of the button panel. It creates a json file of the created or altered
        settings and saves it to the global setting folder.
        :param e: the event object instance is not used.
        """
        # investigating using label instead of Id --- makes it much more readable
        for idx, item in enumerate(self.settingpanel.textinputs):
            x = self.settingpanel.FindWindowById(idx + 1).GetValue()
            y = self.settingpanel.FindWindowById((idx + 1) * 100).GetValue()
            if item != 'Segments':
                unit = self.settingpanel.FindWindowById((idx + 1) * 1001).GetValue()
            self.settingdata[item] = ([x, y, unit])

        self.settingdata['Filter'] = self.settingpanel.FindWindowById(1000).GetValue()
        self.settingdata['Use_Pixels'] = self.settingpanel.FindWindowById(1001).GetValue()
        self.settingdata['PX_CM_Ratio'] = self.settingpanel.FindWindowById(25).GetValue()

        if self.settingpanel.FindWindowById(1002).GetValue():
            self.settingdata['Header'] = self.settingpanel.FindWindowById(1004).GetValue()
        else:
            self.settingdata['Header'] = 0

        self.settingdata['return_units'] = self.settingpanel.FindWindowById(5000).GetStringSelection()
        self.settingdata['Name'] = self.buttonpanel.expname.GetValue()

        output_fname = self.setting_folder + self.settingdata['Name'] + '.json'
        with open(output_fname, 'w') as fp:
            json.dump(self.settingdata, fp, sort_keys=True, indent=4, separators=(',', ': '))

        self.settinglist.refresh()
        self.Layout()

    def load(self, e):
        """
        The load method is bound to the load button in the buttonpanel. It displays information of the selected
        settings from the json file.
        :param e: The event object instance is not used.
        """
        selected_setting = self.settinglist.GetItem(self.settinglist.GetFocusedItem()).GetText()
        set_name = os.path.join(self.setting_folder, selected_setting)
        with open(set_name, 'r') as fp:
            setting = json.loads(fp.read())

        for idx, item in enumerate(self.settingpanel.textinputs):
            self.settingpanel.FindWindowById(idx + 1).SetValue(setting[item][0])
            self.settingpanel.FindWindowById((idx + 1) * 100).SetValue(setting[item][1])
            if item != 'Segments':
                self.settingpanel.FindWindowById((idx + 1) * 1001).SetValue(setting[item][2])

        self.settingpanel.FindWindowById(1000).SetValue(setting['Filter'])
        self.settingpanel.FindWindowById(1001).SetValue(setting['Use_Pixels'])
        self.settingpanel.FindWindowById(25).SetValue(setting['PX_CM_Ratio'])

        if setting['Header']:
            self.settingpanel.FindWindowById(1004).SetValue(setting['Header'])

        self.settingpanel.FindWindowById(5000).SetStringSelection(setting['return_units'])
        self.buttonpanel.expname.SetValue(setting['Name'])

        self.settinglist.refresh()
        self.Layout()


class SettingPanel(wx.Panel):
    """
    The settingpanel contains all the buttons and inputs for creating settings. It also creates and sets the sizer for
    the pane/
    """
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.textinputs = ['Display Scale', 'Display Origin', 'Real Scale', 'Real Origin', 'Segments']
        self.checkinputs = ['Butter Filter', 'Use Pixels', 'Define Header']

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.textwidgets(), 5, wx.ALIGN_LEFT)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.checkwidgets(), 5, wx.EXPAND)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.units(), 5, wx.EXPAND)
        sizer.AddStretchSpacer(1)
        self.SetSizer(sizer)

    def textwidgets(self):
        """
        The textwidgets method creates a vertical wx.boxsizer for the the text inputs available in the setting panel.
        :return: The wx.boxsizer instance, containing the statictext buttons and input fields is returned
        """
        sizer = wx.BoxSizer(wx.VERTICAL)

        for idx, item in enumerate(self.textinputs):
            header = wx.StaticText(self, label=item)
            if header.GetLabel() == 'Segments':
                # sizer.Add(['Number of Segments', wx.TextCtrl)] add this later to get multiple segments
                # for i = 1: wx.TextCtr-output:
                sizer.AddMany([header, self.segmentfields(idx + 1)])
            else:
                sizer.AddMany([header, self.xyfields(idx + 1)])

        sizer.AddMany([wx.StaticText(self, label='PixelToCM_Ratio'), wx.TextCtrl(self, id=25)])
        return sizer

    def checkwidgets(self):
        """
        The checkwidgets method creats a vertical wx.boxsizer for the checkbox inputs available in the setting panel. it
        also creates a unique id for each item which is used in reading the inputs.
        :return: The wx.boxsizer instance, containing the statictext buttons and CheckBox fields is returned.
        """
        sizer = wx.BoxSizer(wx.VERTICAL)
        id = 1000
        for item in self.checkinputs:
            header = wx.StaticText(self, label=item)
            check = wx.CheckBox(self, id=id)
            id += 1
            minisizer = wx.BoxSizer(wx.HORIZONTAL)
            minisizer.AddMany([header, check])
            sizer.Add(minisizer)

        header = wx.TextCtrl(self, id=1004)
        sizer.Add(header, wx.GROW)
        return sizer

    def units(self):
        """
        The units methods creates a horizontal wx.sizer for selecting 'cm' or 'px'.
        :return: wx.horizontal sizer is returned.
        """
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        header = wx.StaticText(self, label='Return Units:')
        units = wx.Choice(self, choices=['CM', 'PIX'], id=5000)

        sizer.AddMany([header, units])
        return sizer

    def xyfields(self, id):
        """
        the xyfields method creates a horizontal sizer with wx.statictext widgets for x,y and unit with the appropriate
        textctrl and id for each widget.
        :param id: id is a hardcoded number set in checkwidgets.
        :return: The wx.horizontal sizer is returned.
        """
        x = wx.StaticText(self, label='X')
        y = wx.StaticText(self, label='Y')
        unit = wx.StaticText(self, label='Unit')
        xinput = wx.TextCtrl(self, id=id)
        yinput = wx.TextCtrl(self, id=id * 100)
        unitinput = wx.TextCtrl(self, id=id * 1001)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([x, xinput, y, yinput, unit, unitinput])
        return sizer

    def segmentfields(self, id):
        """
        the segmentfields methods creates a horizontal sizer containing start and end labels and inputs for the segments
        method. If segments is expanded in the future, this method should be called to create the input fields.
        :param id: id is a hardcoded number set in checkwidgets.
        :return: The wx.horizontal sizer is returned.
        """
        x = wx.StaticText(self, label='Start')
        y = wx.StaticText(self, label='End')
        xinput = wx.TextCtrl(self, id=id)
        yinput = wx.TextCtrl(self, id=id * 100)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([x, xinput, y, yinput])
        return sizer


class SettingsList(wx.ListCtrl):
    """
    The Settingslist panel contains a list of all available settings
    """
    def __init__(self, parent, settingfolder):
        """
        The constructor methods adds all .json files to the settinglist panel
        :param parent: Mainpanel
        :param settingfolder: The global settingfolder as identified by user on current or previous iterations of
        pyselector.
        """
        super().__init__(parent=parent, style=wx.LC_REPORT)
        self.InsertColumn(0, "Name")
        self.settingfolder = settingfolder
        all_settings = [x for x in os.listdir(settingfolder) if x.endswith(".json")]
        for item in all_settings:
            self.InsertItem(0, item)

    def refresh(self):
        """
        The refresh method resets the settings in the settinglist. Similar to the constructor, it reads the json files
        directly from file.
        """
        # find a nicer way to do this
        self.DeleteAllItems()
        all_settings = [x for x in os.listdir(self.settingfolder) if x.endswith(".json")]
        for item in all_settings:
            self.InsertItem(0, item)


class SettingButtonPanel(wx.Panel):
    """
    The settingbuttonpanel contains the save,load and done button for interaction with the setting window.
    """
    def __init__(self, parent):
        """
        The constructor creates , layouts and binds the save, close and load buttons. It also displays or creates
        an input for the setting name
        :param parent:
        """
        super().__init__(parent=parent)
        self.parent = parent
        self.loadbutton = wx.Button(self, label=" > Load > ")
        self.expname = wx.TextCtrl(self)
        self.savebutton = wx.Button(self, label=" < Save < ")
        self.donebutton = wx.Button(self, label="Done")
        self.__dolayout()

        # Event Handlers
        self.savebutton.Bind(wx.EVT_BUTTON, self.save)
        self.donebutton.Bind(wx.EVT_BUTTON, self.close)
        self.loadbutton.Bind(wx.EVT_BUTTON, self.load)

    def __dolayout(self):
        """
        The layout method creates, sets and fits a  vertical boxsizer for the button panel.
        :return:
        """
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany([
            self.loadbutton,
            (10, 10),
            self.expname,
            (10, 10),
            self.savebutton,
            (10, 10),
            (self.donebutton, wx.ALIGN_BOTTOM)])
        self.SetSizerAndFit(sizer)

    def save(self, event):
        """
        the save method is bound to the save button. It does not handle the events but propagates it upwards to the
        mainpanel.
        :param event: event object instance created on clicking the save button
        """
        event.Skip()

    def close(self, e):
        """
        the close method is bound to the done button.  It closes the mainframe for the setting window.
        :param e:
        :return:
        """
        self.parent.parent.Close()

    def load(self, e):
        """
        the load method is bound to the load button. It does not handle the events but propagates it upwards to the
        mainpanel.
        :param event: event object instance created on clicking the save button
        """
        e.Skip()


if __name__ == "__main__":
    pass
