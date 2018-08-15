import json
from pathlib import Path

import numpy as np
import pandas as pd


def set_data(data_address, setting_locator, setting_name):
    setting_path = Path(setting_locator) / (setting_name + '.json')
    with open(setting_path, 'r') as fp:
        setting = json.loads(fp.read())

    if 'selected' in data_address:
        data = pd.read_csv(data_address)
    else:
        if setting['Header']:
            setting['Header'] = eval(setting['Header'])
            assert (len(setting['Header']) == len(
                pd.read_csv(data_address, sep='\t').columns)), 'Column numbers do NOT match'
            for idx, item in enumerate(setting['Header']):
                if item in ['', [], ' ', 'unused']:
                    setting['Header'][idx] = 'unused' + str(idx)

            data = pd.read_csv(data_address, sep='\t', names=setting['Header'])
            try:
                int(data.iloc[0][0])
            except ValueError:
                data = data[2::]

        else:
            data = pd.read_csv(data_address, sep='\t')

        unify_data(data, setting)  # this is to set the columns and units

    return set_experiment(data, setting), setting


def set_experiment(data, setting):
    cfg = {}
    cfg['Trial'] = {}
    target_locations = np.unique(list(zip(list(data.targetx_cm), list(data.targety_cm))), axis=0)
    cfg['all_targets'] = target_locations
    cfg['output'] = data

    if hasattr(data, 'selected') == 0:
        data['accept'] = 0
        data['max_velocity'] = 0
        data['selected'] = 0
        data['interpolated'] = 0
        data['unsure'] = 0

    step_start = setting['Segments'][0]
    step_end = setting['Segments'][1]

    for name, group in data.groupby(['trial_no']):  ##looking through trials
        if hasattr(group, 'accept') and np.unique(group.accept) in [1, -1]:
            continue
        if step_start is '':
            data.loc[group.index, 'selected'] = 1
        else:
            step_start = int(step_start)
            step_end = int(step_end)
            indices = group[group.step.astype(int).between(int(step_start), int(step_end))].index
            data.loc[indices, 'selected'] = 1

    return cfg


def unify_data(data, setting):
    data.dropna(
        inplace=True)  # remove any rows or columns with Nan's (maybe add a special pop up for this? some notice)
    if setting['Display Origin'] == ['', '', '']:
        setting['Display Origin'] = [528, 395, 'px']

    if setting['Header'] and ~ len(setting['Header']) == len(data.columns):
        assert ('Header columns and data columns do not match')

    else:
        setting_headers = data.columns
        for key in setting_headers:
            if key.startswith('time'):
                unit = key.split('_')[1]
                if unit != 'ms':
                    if unit == 's':
                        data.insert(data.columns.get_loc['time_s'], 'time_ms', data.time_s.astype('float') * 1000)
                        data.drop('time_s', axis=1, inplace=True)
                    elif unit == 'm':
                        data.insert(data.columns.get_loc['time_m'], 'time_ms', data.time_m.astype('float') / 60000)
                        data.drop('time_m', axis=1, inplace=True)
                    else:
                        assert ('I don''t know how to handle this unit for time:  ' + unit)
                if unit == 'ms':
                    data['time_ms'] = data.time_ms.astype('float')

            if key.startswith('cursorx'):
                unit = key.split('_')[1]
                if unit == 'px':
                    data.insert(data.columns.get_loc(key), 'cursorx_cm',
                                (data.cursorx_px.astype('float') - setting['Display Origin'][0]) * float(
                                    setting['PX_CM_Ratio']))
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'cm':
                    keyloc = data.columns.get_loc(key)
                    mydata = data[key].astype('float')
                    data.drop(key, axis=1, inplace=True)
                    data.insert(keyloc, 'cursorx_cm', mydata)

            if key.startswith('cursory'):
                unit = key.split('_')[1]
                if unit == 'px':
                    data.insert(data.columns.get_loc(key), 'cursory_cm',
                                (data.cursory_px.astype('float') - setting['Display Origin'][1]) * float(
                                    setting['PX_CM_Ratio']))
                    data.drop('cursory_px', axis=1, inplace=True)
                elif unit == 'cm':
                    keyloc = data.columns.get_loc(key)
                    mydata = data[key].astype('float')
                    data.drop(key, axis=1, inplace=True)
                    data.insert(keyloc, 'cursory_cm', mydata)

            if key.startswith(('penx', 'robotx', 'mousex', 'handx')):
                label, unit = key.split('_')
                if unit == 'm':
                    data.insert(data.columns.get_loc(key), 'handx_cm',
                                data[key].astype('float') * 100)
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'px':
                    ## ("\"is not  division , tells python to read next line)
                    data.insert(data.columns.get_loc(key), 'handx_cm',
                                (data.cursory_px.astype('float') - setting['Display Origin'][1]) * float(
                                    setting['PX_CM_Ratio']))
                    data['handx_cm'] = (data[key].astype('float') - setting['Display Origin'][1]) \
                                       * float(setting['PX_CM_Ratio'])
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'cm':
                    keyloc = data.columns.get_loc(key)
                    mydata = data[key].astype('float')
                    data.drop(key, axis=1, inplace=True)
                    data.insert(keyloc, 'handx_cm', mydata)

            if key.startswith(('peny', 'roboty', 'mousey', 'handy')):
                if unit == 'm':
                    data.insert(data.columns.get_loc(key), 'handy_cm',
                                data[key].astype('float') * 100)
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'px':
                    data.insert(data.columns.get_loc(key), 'handy_cm',
                                (data[key].astype('float') - setting['Display Origin'][1])
                                * float(setting['PX_CM_Ratio']))
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'cm':
                    keyloc = data.columns.get_loc(key)
                    mydata = data[key].astype('float')
                    data.drop(key, axis=1, inplace=True)
                    data.insert(keyloc, 'handy_cm', mydata)

            if key.startswith('targetx'):
                unit = key.split('_')[1]
                if unit == 'px':
                    data.insert(data.columns.get_loc(key), 'targetx_cm',
                                (data.targetx_px.astype('float') - setting['Display Origin'][0]) * float(
                                    setting['PX_CM_Ratio']))
                    data.drop('targetx_px', axis=1, inplace=True)
                elif unit == 'm':
                    data.insert(data.columns.get_loc(key), 'targetx_cm',
                                data[key].astype('float') * 100)
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'cm':
                    data[key] = data[key].astype('float')

            if key.startswith('targety'):
                unit = key.split('_')[1]
                if unit == 'px':
                    data.insert(data.columns.get_loc(key), 'targety_cm',
                                (data.targety_px.astype('float') - setting['Display Origin'][1]) * float(
                                    setting['PX_CM_Ratio']))
                    data.drop('targety_px', axis=1, inplace=True)

                elif unit == 'm':
                    data.insert(data.columns.get_loc(key), 'targety_cm',
                                data[key].astype('float') * 100)
                    data.drop(key, axis=1, inplace=True)
                elif unit == 'cm':
                    data[key] = data[key].astype('float')

            if key.startswith('step'):
                data[key] = data[key].astype('int')
