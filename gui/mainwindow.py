import wx, os
from wx import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from database.Read_Data import set_data
from database.Plot_Data import velocity_profiler, reach_profiler
from gui import settingwindow
import numpy as np
import json
from pathlib import Path
import logging


class MyApp(wx.App):
    """
    Main app class holding the frame
    """
    def OnInit(self):
        """
        OnInit creates and displays the frame
        :return:
        """
        self.mainframe = MyFrame(None)
        self.SetTopWindow(self.mainframe)
        self.mainframe.Show()
        return True


class MyFrame(wx.Frame):
    """
    The frame for holding the panel, popup menu and setting information
    """
    def __init__(self, parent):
        """
        The constructor method creates the mainpanel, popup menu and binds keyevents (currently not working)
        :param parent: MyApp
        """
        super().__init__(parent, -1, "PySelect")
        ## Attributes
        # GUI
        self.parent = parent
        self.setting_json = Path('setting/settings.json')
        self.MainPanel = MainPanel(self)
        self.MainPanel.ButtonPanel.SetFocus()
        self.PopupMenu = PopupMenu(self)

        # Local Variables
        icon_path = os.path.join(os.getcwd(), 'gui', 'icons', 'appicon.png')
        icon = wx.Icon(icon_path, wx.BITMAP_TYPE_PNG)

        # Actions
        self.SetMenuBar(self.PopupMenu)
        self.SetIcon(icon)

        self.Bind(wx.EVT_KEY_DOWN, self.MainPanel.ButtonPanel.keypressed)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.MainPanel.Bind(wx.EVT_KEY_DOWN, self.MainPanel.ButtonPanel.keypressed)
        self.PopupMenu.Bind(wx.EVT_KEY_DOWN, self.MainPanel.ButtonPanel.keypressed)

    def set_settings(self, exp_name):
        """
        Calls mainpanels set_setting method
        :param exp_name: Name of the experiment as selected by user
        :return:
        """
        self.MainPanel.set_settings(exp_name)

    def set_settingfolder(self, file):
        """
        Sets the global setting folder for the current and future uses of the program
        :param file: File location of settings identified by the user
        """
        with open(self.setting_json, "r+") as jsonFile:
            data = json.load(jsonFile)
            data["Location"] = file
            jsonFile.seek(0)  # rewind
            json.dump(data, jsonFile)
            jsonFile.truncate()

        self.MainPanel.settingfolder = file

    def set_exp(self, setting_name):
        """
        The set_exp method calls the mainpanel's set_exp method
        :param setting_name: Name of the setting file currently selected by the user
        """
        self.MainPanel.set_exp(setting_name)

    def set_size(self, size):
        """
        The set_size method manually sets the size of the frame
        :param size: Wx.size object indicating the size of the frame
        """
        self.SetSize(size)

    def OnClose(self, event):
        """
        The onclose method is bound to closing the window . It closes the wxpython app, logs finished and exists
        the running python instance
        """
        self.Destroy()
        logging.info('Finished')
        exit()


class MainPanel(wx.Panel):
    """
    MainPanel holds the plots, setting panel and the button panel
    """
    def __init__(self, parent):
        """
        The constructor method sets the background color, buttonpanel, and handles the initial layout of pyselector
        :param parent: Myframe
        """
        super().__init__(parent=parent)
        self.parent = parent
        self.BackgroundColour = wx.Colour('SALMON')
        self.ButtonPanel = ButtonPanel(self)
        self.ButtonPanel.SetFocus()
        self.Fixp1p2mode = False
        self.clicknum = 1
        self.selected_velocity = 'pyselect'
        self.warningmsg = wx.MessageDialog(self, 'Please Choose Settings first', caption=MessageBoxCaptionStr,
                                           style=OK | CENTRE, pos=DefaultPosition)
        self.__setpanel()
        self.__dolayout()
        self.settingfolder = json.load(open(self.parent.setting_json))['Location']
        self.VelocityCanvas.mpl_connect('button_press_event',
                                        self.onVelcoityclick)

    def __setpanel(self):
        """
        The __setpanel method creates the infopanel and creates intial reach and velocity plots
        :return:
        """
        self.InfoPanel = InfoPanel(self)
        self.__setreachplot()
        self.__setvelocityplot()

    def __dolayout(self):
        """
        The __dolayout method creates and lays out the gridbag sizer for mainpanel
        """
        MainPanelSizer = wx.GridBagSizer(10, 10)
        MainPanelSizer.Add(self.ReachCanvas, pos=(0, 1), span=(1, 1), flag=wx.ALIGN_CENTRE | wx.GROW)
        MainPanelSizer.Add(self.VelocityCanvas, pos=(1, 1), span=(1, 1), flag=wx.ALIGN_CENTRE | wx.GROW)
        MainPanelSizer.Add(self.ButtonPanel, pos=(1, 0), span=(1, 1), flag=wx.GROW)
        MainPanelSizer.Add(self.InfoPanel, pos=(0, 0), span=(1, 1), flag=wx.ALIGN_CENTRE | wx.GROW)
        MainPanelSizer.AddGrowableCol(1)
        MainPanelSizer.AddGrowableCol(0)
        MainPanelSizer.AddGrowableRow(0)
        MainPanelSizer.AddGrowableRow(1)
        self.SetSizerAndFit(MainPanelSizer)
        self.parent.set_size(self.Size)

    def __setreachplot(self):
        """e
        the __setreachplot creates an empty canvas and figure on load up for the reach plot
        """
        fig = plt.figure()
        plt.axis([0, 1, 0, 1])
        self.ReachCanvas = FigureCanvas(self, -1, fig)
        self.ReachCanvas.draw()

    def __setvelocityplot(self):
        """
        the __setvelocityplot creates an empty canvas and figure on load up for the velocity plot
        """
        fig = plt.figure()
        fig.add_axes([0.1, 0.3, 0.8, 0.4])
        fig.set_size_inches(3, 3)
        self.VelocityCanvas = FigureCanvas(self, -1, fig)

    def __updatereachplot(self):
        """
        The __updatereachplot method calculates the "selected" portion of the reach data and creates and draws
        the reachplot on inital trial selection or on refresh instances of pyselector
        """
        # this is somewhat prone to errors, it should be fine as long as the program  runs velocity plots
        # before reach plots though as it does now.
        selection = self.trial_data.index[
            self.trial_data.time_ms.between(self.trial_data.selectedp1, self.trial_data.selectedp2)]
        self.trial_data.loc[selection, 'selected'] = 1
        fig = reach_profiler(self.trial_data, self.setting, self.experiment['all_targets'])
        fig.gca().set_aspect('auto')
        self.ReachCanvas.figure = fig
        self.ReachCanvas.draw()

    def __updatevelocityplot(self):
        """
        The __updatevelocityplot handles dislpay changes in p1-p2 selection , sets the inital max velocity or updates
        max velocity on user selection
        :return:
        """
        if self.Fixp1p2mode:
            self.Fixp1p2mode = False
            self.ButtonPanel.FixP1P2.Value = 0
            self.ButtonPanel.SetMax.Value = 1
            selection_index = [_ for _, val in zip(self.trial_data['time_ms'].index, self.trial_data['time_ms'])
                               if val >= self.trial_data.selectedp1 and val <= self.trial_data.selectedp2]
            self.trial_data.selected = 0
            self.trial_data.selected[selection_index] = 1
            self.selected_velocity = 'pyselect'
            self.VelocityCanvas.figure.get_axes()[0].get_children()[2].set_xdata(self.trial_data.selectedp1)
            self.VelocityCanvas.figure.get_axes()[0].get_children()[3].set_xdata(self.trial_data.selectedp2)
            logging.debug('p1 value on fixp1p2: {}'.format(self.trial_data.selectedp1))
            logging.debug('p2 value on fixp1p2: {}'.format(self.trial_data.selectedp2))

            if ~(self.trial_data.selectedp1 <= self.trial_data.selectedmaxvelocity <= self.trial_data.selectedp2):
                self.max_position = velocity_profiler(self.trial_data, 'update')
                self.VelocityCanvas.figure.get_axes()[0].get_children()[1].set_xdata(
                    self.trial_data.selectedmaxvelocity)
            logging.debug('maxvelocity on fixp1p2: {}'.format(self.trial_data.selectedmaxvelocity))
            self.VelocityCanvas.figure.gca().set_aspect('auto')
            self.VelocityCanvas.draw()

        else:
            if self.selected_velocity is 'pyselect':  # will always happen first.
                [fig, self.max_position] \
                    = velocity_profiler(self.trial_data, self.selected_velocity)
                logging.debug('maxvelocity on pyselect: {}'.format(self.trial_data.selectedmaxvelocity))

                self.VelocityCanvas.figure = fig

            elif self.selected_velocity is 'user':
                logging.debug('maxvelocity on user select: {}'.format(self.trial_data.selectedmaxvelocity))
                # maybe do this differently (outsource to a function?) . Consider this later.
                self.VelocityCanvas.figure.get_axes()[0].get_children()[1].set_xdata(
                    self.trial_data.selectedmaxvelocity)
                self.selected_velocity = 'pyselect'

            self.VelocityCanvas.figure.gca().set_aspect('auto')
            self.VelocityCanvas.draw()

    # def OnItemSelected(self, event):
    #    selected_row = event.GetIndex()
    #    __experiment__.CurrentTrialNum = self.InfoPanel.GetItemText(selected_row)
    #    self.refresh()

    def onVelcoityclick(self, event):
        """
        the onvelocityclick is bound to interactions with the velocity plot. It updates the plot appropriately
         based on the current state of pyselector.
        :param event: event instance on interaction with the velocity plot
        """
        if self.Fixp1p2mode:
            self.fixp1p2(event)
            self.selected_velocity = 'pyselect'

        else:
            self.selected_velocity = 'user'
            self.trial_data.selectedmaxvelocity = event.xdata
            self.refresh()

    def fixp1p2(self, event):
        """
        The fixp1p2 method resets p1 and p2 based on user selection and refreshes the plots when appropriate
        :param event: event instance on interaction with the velocity plot when p1-p2 mode is activated
        """
        if self.clicknum == 1:
            self.trial_data.selectedp1 = event.xdata
            self.clicknum = 2
        elif self.clicknum == 2:
            self.trial_data.selectedp2 = event.xdata
            self.clicknum = 1
            self.refresh()

    def set_settings(self, setting_name):
        """
        the set_settings method logs the settings and updates the info panel
        :param setting_name: String of name of the selected settings
        """
        logging.info('setting_name set to %s \n', setting_name)
        self.InfoPanel.set_settings(setting_name)

    def set_exp(self, exp_name):
        """
        the set_exp method logs the experiment name and updates the info panel. If no settings has been selected yet,
        it creates and displays up a warning message.
        :param exp_name: String of name of the selected experiment
        """
        logging.info('exp_name set to %s \n', exp_name)
        if self.InfoPanel.setting.GetLabel() == 'None':
            self.warningmsg.ShowModal()
        else:
            self.experiment, self.setting = set_data(exp_name, self.settingfolder, self.InfoPanel.setting.GetLabel())
            self.experiment_path = os.path.abspath(os.path.join(exp_name, os.pardir))
            self.experiment_name = os.path.splitext(os.path.basename(exp_name))[0]
            if 'selected' in self.experiment_name:
                self.output_name = self.experiment_name
            else:
                self.output_name = self.experiment_name + '_selected.csv'
            self.InfoPanel.set_exp(self.experiment_name, self.experiment)

    def set_trial_data(self, trial):
        """
        the set_trial_data method logs the active trial on trial change and updates the trial_data attribute of
        the class for the appropriate trialnumber and refreshes the plot
        :param trial: the trial number (NOT INDEX)
        """
        logging.info('=================== \n')
        logging.info('trial set to %s \n ', trial)
        logging.info('=================== \n')
        self.trial_data = self.experiment['output'].where(self.experiment['output'].trial_no == trial)
        self.trial_data.dropna(inplace=True)
        self.refresh()

    def refresh(self):
        """
        The refresh method logs refresh on every call. It updates the velocityplot, reachplot, infopanel and
        creates the appropriate layout for pyselector.
        """
        logging.info('REFRESH \n')
        self.__updatevelocityplot()
        self.__updatereachplot()
        self.InfoPanel.update()
        self.Fit()
        self.__dolayout()
        self.Layout()

    def updateoutput(self):
        """
        The updateoutput method updates the output dataframe of the experiment dictionary for mainpanel.  It sets
        the selected portion, p1-p2 and the max velocity index as accepted/rejected by user
        """
        maxvel_idx = next(
            x[0] for x in enumerate(self.trial_data.time_ms) if x[1] >= self.trial_data.selectedmaxvelocity)
        p1_idx = next(x[0] for x in enumerate(self.trial_data.time_ms) if x[1] >= self.trial_data.selectedp1)
        p2_idx = next(x[0] + 1 for x in enumerate(self.trial_data.time_ms) if x[1] >= self.trial_data.selectedp2)
        self.trial_data.selected.iloc[p1_idx:p2_idx] = 1
        self.trial_data.max_velocity.iloc[maxvel_idx] = 1
        self.experiment['output'].update(self.trial_data)

    def outputdata(self):
        """
        the outputdata method creates and writes the output csv file of pyselector
        :return:
        """
        self.experiment['output'].to_csv(os.path.join(self.experiment_path, self.output_name + '.csv'), index=False)


class InfoPanel(wx.Panel):
    """
    Infopanel contains basic information about the current trial, setting and experiment
    """
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.trial_index = 0
        self.BackgroundColour = wx.Colour('GRAY')
        self.setting = wx.StaticText(self, -1, 'None')
        self.trial_mode = wx.StaticText(self, -1, 'not_selected')
        self.experiment = wx.StaticText(self, -1, 'none')
        self.trial = wx.StaticText(self, -1, '0/0')

        settinglabel = wx.StaticText(self, -1, "Setting:")
        experimentlabel = wx.StaticText(self, -1, "Experiment:")
        triallabel = wx.StaticText(self, -1, "Trials:")
        acceptedlabel = wx.StaticText(self, -1, "Trial_mode:")

        sizer = wx.GridSizer(rows=4, cols=2, hgap=5, vgap=5)

        sizer.AddMany([settinglabel, self.setting, experimentlabel, self.experiment,
                       triallabel, self.trial, acceptedlabel, self.trial_mode])
        self.SetSizer(sizer)

    def update(self):
        """
        The update method sets the trial label and the accepted/rejected mode of info panel.
        :return:
        """
        self.trial.SetLabel(str(self.current_trial) + '/' + str(self.all_trials.iloc[-1]))
        self.set_mode()

    def set_settings(self, setting_name):
        """
        the set_settings method updates setting label on selection.
        :param setting_name: string name of the currently selected settings
        """
        self.setting.SetLabel(os.path.splitext(setting_name)[0])
        self.parent.Refresh()

    def update_trial_index(self, direction):
        """
        The update_trial_index calculates and updates the current trial number and index for pyselector. It also
        calls the set_trial_data method of mainpanel to refresh pyselector accordingly. This method updates and sets
        the global trial number for the current state of pyselector.
        :param direction: direction can be 'up' for going to next trial  , 'down' for last trial or an integer when
        the go button is used.
        :return:
        """
        if isinstance(direction, (int, float)):
            self.current_trial = direction
            self.trial_index = np.where(self.all_trials.unique() == self.current_trial)[0][0]
        elif direction is 'up':
            self.trial_index += 1
            self.current_trial = self.all_trials.unique()[self.trial_index]
        elif direction is 'down':
            self.trial_index -= 1
            self.current_trial = self.all_trials.unique()[self.trial_index]

        self.parent.set_trial_data(self.current_trial)

    def set_exp(self, exp_name, experiment):
        """
        The set_exp method updates the experiment label in info panel. It also sets the initial trial and mode for
        pyselector
        :param exp_name: String name of the experiment selected by uesr
        :param experiment: Dictionary containing output and grouped trial information for the current experiment
        """
        self.experiment.SetLabel(exp_name)
        # ====  RECODE maybe? / there has to be a nicer way of handling this
        self.current_trial = experiment['output'].trial_no.iloc[self.trial_index]
        self.all_trials = experiment['output'].trial_no
        self.trial.SetLabel(str(self.current_trial) + '/' + str(self.all_trials.iloc[-1]))
        self.parent.set_trial_data(self.current_trial)
        self.set_mode()

    def set_mode(self):
        """
        the set_mode method sets the label for the current mode of pyselector
        """
        accepted = np.unique(self.parent.trial_data.accept)[0]
        if accepted == 1:
            self.trial_mode.SetLabel('Accepted')
        elif accepted == -1:
            self.trial_mode.SetLabel('Rejected')
        else:
            self.trial_mode.SetLabel('Not_Seleted')


class ButtonPanel(wx.Panel):
    """
    ButtonPanel contains all buttons for user interaction with pyselector
    """
    def __init__(self, parent):
        """
        The constrcutor creates the button and a horizontal wx.boxsizer for holding them
        :param parent: Mainpanel. It also binds button interactions with appropriate methods.
        """
        super().__init__(parent=parent)
        self.parent = parent
        self.SetFocus()
        self.Unsure = wx.CheckBox(self, size=(100, 10), label="Unsure")
        self.Save = wx.ToggleButton(self, label="Accept")
        self.SetMax = wx.ToggleButton(self, label=" Max Velocity")
        self.FixP1P2 = wx.ToggleButton(self, label="Fix P1 P2")
        self.Delete = wx.ToggleButton(self, label="Reject ")
        self.Goto = wx.TextCtrl(self)
        self.GotoButton = wx.Button(self, label="Go")
        self.Next = wx.Button(self, label="Next")
        self.Previous = wx.Button(self, label="Previous")
        self.BackgroundColour = wx.Colour('GRAY')

        goto_sizer = wx.BoxSizer(wx.HORIZONTAL)
        goto_sizer.AddMany([(self.Goto, 1 / 3), (self.GotoButton, 2 / 3)])
        self.gridSizer = wx.GridSizer(rows=4, cols=2, hgap=2, vgap=2)
        self.gridSizer.AddMany([
            (self.FixP1P2, wx.ALIGN_CENTER), (self.SetMax, wx.ALIGN_CENTER),
            goto_sizer, (self.Unsure, wx.ALIGN_CENTER),
            (self.Save, wx.ALIGN_CENTER), (self.Delete, wx.ALIGN_CENTER),
            (self.Previous), (self.Next)
        ])
        self.SetSizer(self.gridSizer)

        self.SetMax.Value = 1
        self.SetMax.Label
        self.SetMax.SetOwnBackgroundColour('#FF0000')
        self.FixP1P2.SetOwnBackgroundColour('#0000FF')

        # Actions
        self.Bind(wx.EVT_BUTTON, self.nexttrial, self.Next)
        self.Bind(wx.EVT_BUTTON, self.prvstrial, self.Previous)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.fixp1p2, self.FixP1P2)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.unsuretrial, self.Unsure)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.savetrial, self.Save)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.deltrial, self.Delete)
        self.Bind(wx.EVT_BUTTON, self.jumptotrial, self.GotoButton)

        self.Bind(wx.EVT_KEY_DOWN, self.keypressed)

    def keypressed(self, e):
        """
        The keypressed method handles right,left or down key presses by the user and updates the trial number
        :param e: event object containing keypress information
        """
        if e.KeyCode == wx.WXK_RIGHT:
            self.nexttrial(e)
        elif e.KeyCode == wx.WXK_LEFT:
            self.prvstrial(e)
        elif e.KeyCode == wx.WXK_DOWN:
            self.savetrial(e)

    def nexttrial(self, e):
        """
        The nexttrial method is bound to the "next" button. It updates the output, updates the trial index and
        sets the appropriate mode for the next trial. It also resets all buttons to their initial state.
        :param e: the object parameter is not used.
        """
        if self.parent.trial_data.accept.min():
            self.parent.updateoutput()
            self.parent.InfoPanel.update_trial_index('up')
            self.parent.InfoPanel.set_mode()
            self.reset_buttons()

    def jumptotrial(self, e):
        """
        The jumptrial method is bound to the go button.  It updates the output, updates the trial index and
        sets the appropriate mode for the trial if indicated by user. If the gobutton box is left blank,
        it updates the trial index to the closest unselected or unsure trial. It also resets all buttons
        to their inital state.
        :param e: the event parameter is not used.
        """
        self.parent.updateoutput()
        self.parent.InfoPanel.set_mode()
        if self.Goto.GetValue():
            self.parent.InfoPanel.update_trial_index(int(self.Goto.GetValue()))
        else:
            output_data = self.parent.experiment['output']
            unselected_trials = np.unique(output_data[output_data.accept == 0].trial_no)
            unsure_trials = np.unique(output_data[output_data.unsure == 1].trial_no)
            if unselected_trials.size & unsure_trials.size:
                trial_index = np.min(unselected_trials + unsure_trials)
            elif unselected_trials.size:
                trial_index = np.min(unselected_trials)
            elif unsure_trials.size:
                trial_index = np.min(unsure_trials)
            else:
                trial_index = output_data.trial_no.max()

            self.parent.InfoPanel.update_trial_index(trial_index)

        self.reset_buttons()

    def fixp1p2(self, e):
        """
        The fixp1p2 method is bound to the p1-p2 button. It updates the current state of pyselector to change p1-p2
        as opposed to max_velocity on interaction with the velocity plot.
        :param e: the event parameter is not used.
        :return:
        """
        self.parent.Fixp1p2mode = True
        self.FixP1P2.Value = 1
        self.SetMax.Value = 0

    def prvstrial(self, e):
        """
        The prvstrial works just like the enxttrial method. However, prvstrial does not check to make sure that the
        current trial is accepted or rejected
        :param e: the
        """
        self.parent.InfoPanel.update_trial_index('down')
        self.parent.InfoPanel.set_mode()
        self.reset_buttons()

    def deltrial(self, e):
        """
        The deltrial method is bound to the reject button. It updates the trial data and the info panel to reflect
        the rejection.
        :param e:
        :return:
        """
        self.parent.trial_data['Reject'] = 1
        self.parent.trial_data['accept'] = -1
        self.Save.SetValue(0)
        self.parent.InfoPanel.set_mode()

    def savetrial(self, e):
        """
        The savetrial method is bound to the accept button. It updates the trial data and the info panel to reflect
        the rejection.
        :param e:
        """
        self.parent.trial_data['accept'] = 1
        self.parent.trial_data['Reject'] = -1
        self.Delete.SetValue(0)
        self.parent.InfoPanel.set_mode()

    def unsuretrial(self, e):
        """
        The unsuretrial method is bound to the unsure button. It updates the trial_data information for future output.
        :param e:
        :return:
        """
        self.parent.trial_data['Unsure'] = 1

    def reset_buttons(self):
        """
        The reset button returns all buttons to their intial state.
        :return:
        """
        self.SetMax.Value = 1
        self.Parent.FixP1P2 = 0
        self.FixP1P2.Value = 0
        self.Unsure.SetValue(False)
        self.Save.SetValue(False)
        self.Delete.SetValue(False)


# This is the toolbar menu at the top
class PopupMenu(wx.MenuBar):
    """
    The popupmenu class creates the file and setting menu in the toolbar for pyselector
    """
    def __init__(self, parent):  # parent is mainframe
        """
        The constructor creates two menus for file and setting handling. It also binds interactions with the menu
        to the appropriate functions
        :param parent: Mainframe.
        """
        super().__init__()
        self.parent = parent

        # The two menus
        self.filemenu = wx.Menu()
        self.settingsmenu = wx.Menu()
        self.savedsettings = wx.Menu()  # savedsetting is a submenu of settingmenu

        self.getsettings()

        # settingmenu buttons

        settingfolder = self.settingsmenu.Append(-1, "Setting Folder")
        settingchoice = self.settingsmenu.Append(-1, 'Quick Setting...', self.savedsettings)
        newsetting = self.settingsmenu.Append(-1, 'Interactive Setting')

        # filemenu buttons
        loaddata = self.filemenu.Append(-1, 'load')
        writedata = self.filemenu.Append(-1, 'save')
        # writedata_cs = filemenu.Append(-1, 'save cs')

        self.Append(self.filemenu, 'Files')
        self.Append(self.settingsmenu, 'Settings')

        self.filepicker = wx.FileDialog(self)
        self.folderpicker = wx.DirDialog(self)

        ##Bindings
        self.Bind(EVT_MENU, self.loadsettinggui, newsetting)
        self.Bind(EVT_MENU, self.outputdata, writedata)
        self.Bind(EVT_MENU, self.getsettingfolder, settingfolder)
        self.Bind(EVT_MENU, self.getdata, loaddata)
        self.savedsettings.Bind(wx.EVT_MENU, self.choosesetting)

    def loadsettinggui(self, e):
        """
        the loadsettinggui method is bound to the interaction setting button in the menu bar. It creates and shows
        an instance of the settingwdinwo
        :param e:
        :return:
        """
        win = settingwindow.SettingFrame(self, self.parent.MainPanel.settingfolder)
        win.Show(True)

    #       all_settings = [x for x in os.listdir('setting/savedsettings') if x.endswith(".json")]    # setings that already exist
    #       for item in all_settings:
    #           if item not in self.savedsettings:
    #               self.savedsettings.Append(-1, item)

    def choosesetting(self, e):
        """
        The choosesetting method updates the global setting file of pyselector
        :param e: event object containing information about the selected setting
        """
        self.parent.set_settings(self.savedsettings.FindItemById(e.GetId()).GetItemLabel())

    def getdata(self, e):
        """
        the getdata method is bound to experiment selections. It calls the mainframes set_exp method.
        :param e: the event object instance is not used. A filepicker modal is instead created and used to pass the
        appropriate values.
        """
        self.filepicker.ShowModal()
        self.parent.set_exp(self.filepicker.GetPath())

    def outputdata(self, e):
        """
        the output data method is bound to the save button. It creates and saves a .csv file for the current output
        of pyselector
        :param e:  event object instance is not used
        """
        self.parent.MainPanel.outputdata()

    def getsettingfolder(self, e):
        """
        The getsettingfolder method creates a folder modal for the user. It updates the global setting folder for
        the current and future instances of pyselector. It also updates the settings shown in the quick setting menu.
        :param e: event object instance is not used
        """
        self.folderpicker.ShowModal()
        self.parent.set_settingfolder(self.folderpicker.GetPath())
        self.getsettings()

    def getsettings(self):
        """
        The getsettings mehtod updates the quicksetting menu with the setting files avilable in the selected setting
        folder.
        """
        current_items = self.savedsettings.GetMenuItems()
        for item in current_items:
            self.savedsettings.DestroyItem(item)

        all_settings = [_ for _ in os.listdir(self.parent.MainPanel.settingfolder) if _.endswith(".json")]

        for item in all_settings:
            self.savedsettings.Append(-1, item)


def run():
    """
    The run method configures the log, and starts the main loop of the app.
    :return:
    """
    logging.basicConfig(filename='setting/mylog.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    logging.info('================= \n')
    logging.info('Started')
    app = MyApp(False)
    app.MainLoop()
    logging.info('================= \n')
    logging.info('Finished')


if __name__ == "__main__":
    run()
