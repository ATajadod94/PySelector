import matplotlib.patches as patches
import numpy as np
from matplotlib import pyplot as plt
from scipy import signal
from scipy.interpolate import interp1d

# Turn interactive plotting off
plt.ioff()


def velocity_profiler(data, velocity_choice):
    """
    The velocity_profiler handles passing the velocity_profile request to the appropriate method
    :param data: A dataframe holding information about one trial
    :param velocity_choice: A string identifying where the request for velocity profile came from (pyselect, User
    , or update)
    :return: Returns a max_position list (on update) or a figure and a max_position list (on Pyselect). On user selection
    , it does not return anything
    """
    if velocity_choice is 'pyselect':
        return velocityprofile(data)
    elif velocity_choice is 'user':
        pass
    elif velocity_choice is 'update':
        return velocityupdate(data)


def reach_profiler(data, setting, targets):
    """
    The reach_profiler method calls the reachprofile method. It can be expanded on in the future for more flexibility
    :param data: A dataframe holding information about one trial
    :param setting: Setting dictionary for the loaded experiment
    :param targets: List of all the targets in the loaded experiment
    :return: Returns the reachprofile figure
    """
    return reachprofile(data, setting, targets)


def velocityupdate(data):
    """
    The velocityupdate method calculates the max velocity position based on the interpolated data
    :param data: A Pandas dataframe for one trial.  The dataframe must also hold the interpolated information as an attribute
    :return: Returns a max_position list
    """
    start_time = data.selectedp1
    end_time = data.selectedp2
    selection_index = [_ for _, val in enumerate(data.Interpolated[1]) if val > start_time and val < end_time]
    interpolated_speed, interpolated_time = data.Interpolated[0][selection_index], data.Interpolated[1][selection_index]
    maxspeedidx = interpolated_speed.argmax()
    data.selectedmaxvelocity = interpolated_time[maxspeedidx]
    max_position = [data.handx_cm.iloc[maxspeedidx], data.handy_cm.iloc[maxspeedidx]]
    return max_position


def velocityprofile(data):
    """
    The velocityprofile method calculates interpolated data if not already done, sets p1,p2 and max velocity and
    creates an appropriate figure
    :param data: Pandas dataframe with information about about one trial
    :return: Returns a figure and a max_position list.
    """
    if not (hasattr(data, 'Interpolated_speed')):
        # VelocityPorfile/ Interpolate and draw
        if 'handx_cm' in data.keys():
            xpoly, ypoly = interp1d(data['time_ms'], data.handx_cm), interp1d(data['time_ms'], data.handy_cm)
        else:
            raise Exception('There is no hand data, please check your settings')

        ## Time calculations
        interpolated_time = np.linspace(data['time_ms'].iloc[0], data['time_ms'].iloc[-1], endpoint=True)
        xpoly, ypoly = xpoly(interpolated_time), ypoly(interpolated_time)

        nyquist = data['time_ms'].diff().mean()
        filter_freq = 3
        [b, a] = signal.butter(1, filter_freq / nyquist, 'low')
        xpoly, ypoly = signal.filtfilt(b, a, xpoly), signal.filtfilt(b, a, ypoly)
        interpolated_speed = np.append(0, calculate_speeds(xpoly, ypoly, interpolated_time))

        # adding it to our trialdata object in  gui.mainwindow
        data.Interpolated = [interpolated_speed,
                             interpolated_time]  # we can treat data as-if it was passed by reference here

        data.RealSpeed = calculate_speeds(data.handx_cm.astype('float'), data.handy_cm.astype('float'),
                                          data['time_ms'])

        max_velocity = interpolated_speed.max()
        p1_speed = max_velocity * 0.1
        p1idx = np.argmax(interpolated_speed > p1_speed)
        maxspeedidx = interpolated_speed.argmax()
        p2idx = maxspeedidx + 1 + np.argmax(interpolated_speed[maxspeedidx + 1::] <= p1_speed)
        data.selectedp1 = next(x for x in data['time_ms'] if x > interpolated_time[p1idx])
        data.selectedp2 = next(x for x in data['time_ms'] if x >= interpolated_time[p2idx])
        data.selectedmaxvelocity = interpolated_time[maxspeedidx]
        data.selected = 0
        selectedindex = (data['time_ms'] >= data.selectedp1) & (data['time_ms'] <= data.selectedp2)
        data.selected[selectedindex] = 1

    selection_starttime = data[data.selected == 1].iloc[0].time_ms
    selection_endtime = data[data.selected == 1].iloc[-1].time_ms

    interpolated_time = data.Interpolated[1][
        (data.Interpolated[1] > selection_starttime) & (data.Interpolated[1] < selection_endtime)]
    interpolated_speed = data.Interpolated[0][
        (data.Interpolated[1] > selection_starttime) & (data.Interpolated[1] < selection_endtime)]
    interpolated_selected_idx = np.where(
        (data.Interpolated[1] > selection_starttime) & (data.Interpolated[1] < selection_endtime))

    maxspeed = interpolated_speed.max()
    maxspeedidx = np.where(data.Interpolated[0] == maxspeed)[0][0]
    data.selectedmaxvelocity = data.Interpolated[1][maxspeedidx]

    p1_speed = data.selectedmaxvelocity * 0.1
    try:
        p1_speed = interpolated_speed[interpolated_speed > p1_speed][0]
    except(IndexError):
        p1_speed = interpolated_speed[0]

    if p1_speed == maxspeed:
        p1_idx = maxspeedidx - 1
    else:
        p1_idx = np.where(data.Interpolated[0] == p1_speed)[0][0]

    data.selectedp1 = next(x for x in data['time_ms'] if x > data.Interpolated[1][p1_idx])
    p2_idx = np.argmax(data.Interpolated[0][maxspeedidx + 1::] < (maxspeed * 0.1))
    if p2_idx == 0:
        p2_idx = -2
    else:
        p2_idx += maxspeedidx + 1
    data.selectedp2 = next(x for x in data['time_ms'] if x > data.Interpolated[1][p2_idx])
    maxspeedidx = np.where(data.time_ms >= data.selectedmaxvelocity)[0][0]
    max_position = [data.handx_cm.iloc[maxspeedidx], data.handy_cm.iloc[maxspeedidx]]

    fig = plt.figure(facecolor='gray', edgecolor='r')
    ax = fig.add_axes([0.1, 0.2, 0.8, 0.6])

    ax.plot(data.Interpolated[1], data.Interpolated[0])
    ax.axvline(data.selectedmaxvelocity, ymax=max(data.Interpolated[1]), color='r', label='velocity')
    ax.axvline(data.selectedp1, ymax=max(data.Interpolated[1]), color='b', label='p1')
    ax.axvline(data.selectedp2, ymax=max(data.Interpolated[1]), color='b', label='p2')
    plt.close()
    return fig, max_position


def reachprofile(data, setting, targets):
    """
    The reachprofile method creates the reach data plot for the real and display data.
    :param data: Pandas dataframe with information about about one trial
    :param setting: Setting dictionary for the loaded experiment
    :param targets: List of all the targets in the loaded experiment
    :return: Returns the reachprofile figure
    """
    selected_data = data.index[data.selected == 1].tolist()
    reachplotdata = data.loc[selected_data].copy()
    maxspeedidx = next(
        _ for _, x in enumerate(reachplotdata['time_ms']) if x >= data.selectedmaxvelocity.astype('float'))

    max_pen_position = [float(reachplotdata.handx_cm.iloc[maxspeedidx]),
                        float(reachplotdata.handy_cm.iloc[maxspeedidx])]

    max_cursor_position = [float(reachplotdata.cursorx_cm.iloc[maxspeedidx]),
                           float(reachplotdata.cursory_cm.iloc[maxspeedidx])]

    # ReachProfile/ draw
    target_locations = np.unique(
        list(zip(list(reachplotdata.targetx_cm.astype('float')), list(reachplotdata.targety_cm.astype('float')))),
        axis=0)
    trial_target = patches.Circle(target_locations[0], radius=.5, color='g', fill=True)
    max_penvelocity = patches.Circle(max_pen_position, radius=.5, color='b', fill=True)
    max_cursorvelocity = patches.Circle(max_cursor_position, radius=.5, color='b', fill=True)
    fig2 = plt.figure(facecolor='gray', edgecolor='b')
    ax = fig2.add_subplot(111)
    ax.set_aspect('equal')

    # if setting['Display Origin'] == ['', '', '']:
    range = reachplotdata.cursorx_cm.max() - reachplotdata.cursorx_cm.min()
    disprange_x = [reachplotdata.cursorx_cm.min() - (range / 2), reachplotdata.cursorx_cm.max() + (range / 2)]
    range = reachplotdata.cursory_cm.max() - reachplotdata.cursory_cm.min()
    disprange_y = [reachplotdata.cursory_cm.min() - (range / 2), reachplotdata.cursory_cm.max() + (range / 2)]

    xleft = disprange_x[0]
    xright = disprange_x[1]
    ydown = disprange_y[0]
    yup = disprange_y[1]
    left = min(xleft, ydown)
    right = max(xright, yup)

    ax.set_ylim([left, right])
    ax.set_xlim([left, right])

    ax.plot(reachplotdata.handx_cm.astype('float'), reachplotdata.handy_cm.astype('float'), 'g', linestyle=' ',
            marker="o", fillstyle='none')
    ax.plot(reachplotdata.cursorx_cm.astype('float'), reachplotdata.cursory_cm.astype('float'), 'r')

    for target in targets:
        all_targets = patches.Circle(target, radius=.5, color='g', fill=False)
        ax.add_patch(all_targets)

    if setting['Display Origin'] and 'homex_px' in data.keys():
        homepos_x = (float(data.homex_px[0]) - setting['Display Origin'][0]) * float(setting['PX_CM_Ratio'])
        homepos_y = (float(data.homey_px[0]) - setting['Display Origin'][1]) * float(setting['PX_CM_Ratio'])
    else:
        homepos_x = 0
        homepos_y = -8.5

    home = patches.Circle([homepos_x, homepos_y], radius=.5, color='yellow', fill=True)
    ax.add_patch(home)

    ax.add_patch(trial_target)
    ax.add_patch(max_penvelocity)
    ax.add_patch(max_cursorvelocity)
    ax.legend(['Real', 'Display'])
    plt.close()

    return fig2


def calculate_speeds(x, y, Time):
    """
    The calculate speed method calculates 2D cartesian velocity
    :param x: numpy array of the x_cordinates of the data
    :param y: numpy array of the y_cordinates of the data
    :param Time: numpy array of the time_cordinates of the data
    :return: numpy array of the caluclated velocity
    """
    [xdiff, ydiff, timediff] = map(np.diff, [x, y, Time])
    return np.divide(np.sqrt(np.add(np.square(xdiff), np.square(ydiff))), timediff)


def find_position(data, time, velocity):
    """
    The find_position method finds the index of the position of first instance of the reach where the velocity is
    above a certain value
    :param data:  Pandas dataframe with information about about one trial
    :param time:  An iterable data type with the temporal values for the trial
    :param velocity: A number indicating the velocity thershold needed for the position
    :return:  a 2*1 list of x and y values for the first instance passing the velocity thereshold
    """
    x = [row[0] for row in data]
    y = [row[1] for row in data]
    velocity_idx = next(x[0] for x in enumerate(time) if x[1] >= velocity)
    return [x[velocity_idx], y[velocity_idx]]
