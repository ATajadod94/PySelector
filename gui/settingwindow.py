import collections

import json
import os
import wx
from wx import *


class SettingFrame(wx.Frame):
    def __init__(self, parent, setting_folder):
        super().__init__(parent=parent)

        # Attributes
        self.parent = parent
        self.MainPanel = MainSettingPanel(self, setting_folder)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.MainPanel, wx.GROW)
        self.SetSizerAndFit(sizer)


class MainSettingPanel(wx.Panel):
    def __init__(self, parent, setting_folder):
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

    def save(self, event):
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
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        header = wx.StaticText(self, label='Return Units:')
        units = wx.Choice(self, choices=['CM', 'PIX'], id=5000)

        sizer.AddMany([header, units])
        return sizer

    def xyfields(self, id):
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
        x = wx.StaticText(self, label='Start')
        y = wx.StaticText(self, label='End')
        xinput = wx.TextCtrl(self, id=id)
        yinput = wx.TextCtrl(self, id=id * 100)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([x, xinput, y, yinput])
        return sizer


class SettingsList(wx.ListCtrl):
    def __init__(self, parent, settingfolder):
        super().__init__(parent=parent, style=wx.LC_REPORT)
        self.InsertColumn(0, "Name")
        self.settingfolder = settingfolder
        all_settings = [x for x in os.listdir(settingfolder) if x.endswith(".json")]
        for item in all_settings:
            self.InsertItem(0, item)

    def refresh(self):
        # find a nicer way to do this
        self.DeleteAllItems()
        all_settings = [x for x in os.listdir(self.settingfolder) if x.endswith(".json")]
        for item in all_settings:
            self.InsertItem(0, item)


class SettingButtonPanel(wx.Panel):
    def __init__(self, parent):
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
        event.Skip()

    def close(self, e):
        self.parent.parent.Close()

    def load(self, e):
        e.Skip()


if __name__ == "__main__":
    pass
