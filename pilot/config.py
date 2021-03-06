import os
import time
import datetime
from fair_research_login import ConfigParserTokenStorage

TRANSFER_LOG_MAX_SIZE = 2


class Config(ConfigParserTokenStorage):
    CFG_FILENAME = os.path.expanduser('~/.pilot1.cfg')
    TRANSFER_LOG_FIELDS = ['dataframe', 'status', 'task_id',
                           'start_time']

    def _save_log(self, log_id, log_dict):
        cfg = self.load()
        if isinstance(log_dict['start_time'], datetime.datetime):
            timestamp = log_dict['start_time'].timestamp()
            log_dict['start_time'] = str(int(timestamp))
        field_list = [log_dict.get(f) for f in self.TRANSFER_LOG_FIELDS]
        log_data = ','.join(field_list)
        if 'transfer_log' not in cfg:
            cfg['transfer_log'] = {}
        cfg['transfer_log'][str(log_id)] = log_data
        self.save(cfg)

    def add_transfer_log(self, transfer_result, datapath):
        cfg = self.load()
        if 'transfer_log' not in cfg:
            cfg['transfer_log'] = {}
        last_id = max([int(i) for i in cfg['transfer_log'].keys()] or [-1])
        log_id = str(last_id + 1)
        log_data = [
            datapath,
            transfer_result.data['code'],
            transfer_result.data['task_id'],
            str(int(time.time()))
        ]
        self._save_log(log_id, dict(zip(self.TRANSFER_LOG_FIELDS, log_data)))

    def get_transfer_log(self):
        cfg = self.load()
        if 'transfer_log' not in cfg:
            return []

        logs = []
        for log_id, data in cfg['transfer_log'].items():
            tlog = dict(zip(self.TRANSFER_LOG_FIELDS, data.split(',')))
            tlog['id'] = int(log_id)
            timestamp = int(tlog['start_time'])
            tlog['start_time'] = datetime.datetime.fromtimestamp(timestamp)
            logs.append(tlog)
        logs.sort(key=lambda l: l['id'], reverse=True)
        return logs

    def get_transfer_log_by_task(self, task_id):
        for tlog in self.get_transfer_log():
            if tlog['task_id'] == task_id:
                return tlog

    def update_transfer_log(self, task_id, new_status):
        tlog = self.get_transfer_log_by_task(task_id)
        tlog['status'] = new_status
        self._save_log(tlog['id'], tlog)

    def get_user_info(self):
        cfg = self.load()
        if 'profile' in cfg:
            return dict(self.load()['profile'])
        return {}

    def save_user_info(self, user_info):
        cfg = self.load()
        cfg['profile'] = user_info
        self.save(cfg)

    def clear(self):
        cfg = self.load()
        cfg.clear()
        self.save(cfg)


config = Config(filename=Config.CFG_FILENAME, section='tokens')
