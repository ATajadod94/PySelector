import wx, os, json
from wx import *
from wx.lib.splitter import MultiSplitterWindow
import numpy as np
import collections
import wx.lib.agw.gradientbutton as gbtn



class SettingFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=parent)

        # Attributes
        self.parent = parent
        self.MainPanel = MainSettingPanel(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.MainPanel, wx.GROW)
        self.SetSizerAndFit(sizer)



class MainSettingPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent

        self.settingpanel = SettingPanel(self)
        self.settinglist = SettingsList(self)
        self.buttonpanel = SettingButtonPanel(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.settinglist, 1, wx.GROW)
        sizer.Add(self.buttonpanel, 1, wx.GROW)
        sizer.Add(self.settingpanel, 1, wx.GROW)
        self.SetSizer(sizer)


        self.settingdata = collections.defaultdict(dict)

        self.Bind(wx.EVT_BUTTON, self.save)

    def save(self, event):
        for idx, item in enumerate(self.settingpanel.textinputs):
            x = self.settingpanel.FindWindowById(idx+1).GetValue()
            y = self.settingpanel.FindWindowById((idx+1)*100).GetValue()
            self.settingdata[item] = ([x, y])

        self.settingdata['Filter'] = self.settingpanel.FindWindowById(1000).GetValue()
        self.settingdata['Use_Pixels'] = self.settingpanel.FindWindowById(1001).GetValue()

        if self.settingpanel.FindWindowById(1002).GetValue():
            self.settingdata['Header'] = self.settingpanel.FindWindowById(1004).GetValue()
        else:
            self.settingdata['Header'] = 0

        self.settingdata['return_units'] = self.settingpanel.FindWindowById(5000).GetStringSelection()
        self.settingdata['Name'] = self.buttonpanel.expname.GetValue()

        output_fname = 'setting/savedsettings/' + self.settingdata['Name'] + '.json'
        with open(output_fname, 'w') as fp:
            json.dump(self.settingdata, fp, sort_keys=True, indent=4, separators=(',', ': '))

        self.settinglist.refresh()
        self.Layout()


class SettingPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.textinputs = ['Display Scale', 'Display Origin', 'Real Scale', 'Real Origin', 'Segments']
        self.checkinputs = ['Butter Filter', 'Use Pixels', 'Define Header']


        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.textwidgets(), 5, wx.EXPAND)
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
            sizer.AddMany([header, self.xyfields(idx+1)])

        return sizer

    def checkwidgets(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        id = 1000
        for item in self.checkinputs:
            header = wx.StaticText(self, label=item)
            check = wx.CheckBox(self, id =id)
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

    def xyfields(self,id):
        x = wx.StaticText(self, label='X')
        y = wx.StaticText(self, label='Y')
        xinput = wx.TextCtrl(self, id=id)
        yinput = wx.TextCtrl(self, id=id*100)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([x, xinput, y, yinput])
        return sizer


class SettingsList(wx.ListCtrl):
    def __init__(self, parent):
        super().__init__(parent=parent, style=wx.LC_REPORT)
        self.InsertColumn(0, "Name")
        all_settings = [x for x in os.listdir('setting/savedsettings') if x.endswith(".json")]
        for item in all_settings:
            self.InsertItem(0, item)

    def refresh(self):
        #find a nicer way to do this
        self.DeleteAllItems()
        all_settings = [x for x in os.listdir('setting/savedsettings') if x.endswith(".json")]
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





if __name__ == "__main__":
    pass