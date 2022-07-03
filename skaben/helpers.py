from random import randint
from datetime import datetime


def new_task_id(name='task'):
    """ generate task id """
    dt = datetime.now()
    num = ''.join([str(randint(0, 9)) for _ in range(10)])
    return f'{name}-{num}{dt.microsecond}'
