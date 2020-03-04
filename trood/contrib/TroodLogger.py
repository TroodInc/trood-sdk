import logging
import logging.handlers
import sys


class TroodAdapter(logging.LoggerAdapter):
    event_code = {'CREATE_BO': '3001', 'UPDATE_BO': '3002',
                  'DELETE_BO': '3003', 'SEND_EMAIL': '1001',
                  'SCHEDULER_TASL_EXECUTION': '2001'}

    def process(self, msg, kwargs):
        if 'mailbox' in msg:
            if 'id' in msg:
                id = msg.get("id", '')
                subject = msg.get("subject", '')
                return '%s | %s' % (id, subject), kwargs
            else:
                return msg, kwargs
        elif 'events' in msg:
            data = msg.get('events', '')[0]
            action = data.get('action', '')
            if 'user' in data:
                scope = data.get('user').get('type', '')
            else:
                scope = ''
            bo_object = data.get('object', '')
            bo_before = data.get('previous', '')
            bo_after = data.get('current', '')
            if action == 'update':
                code = self.event_code.get('UPDATE_BO')
            elif action == 'create':
                code = self.event_code.get('CREATE_BO')
            elif action == 'delete':
                code = self.event_code.get('DELETE_BO')
            else:
                code = 'Undefined code action'
            return '%s | %s | %s | %s | %s | %s' % (code, scope,
                                                    bo_object, action,
                                                    bo_before,
                                                    bo_after), kwargs
        else:
            return '%s | Undefined event| | | | ' % (msg), kwargs


class TroodLogger:
    '''
    Exemple:
    from agents.TroodLogger import TroodLogger
    logger = TroodLogger(__name__).adapter
    logger.debug(data)
    '''
    def get_logger(self, name):
        logger = logging.getLogger(name)
        logging.basicConfig(
            format='%(levelname)s | %(asctime)s | %(name)s:%(lineno)s | %(message)s',
            handlers=[logging.StreamHandler()]
        )
        return logger

    def __init__(self, name):
        logger = self.get_logger(name)
        self.adapter = TroodAdapter(logger, {})
