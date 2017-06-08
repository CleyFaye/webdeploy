# encoding=utf-8
from .configloader import config
from .task import (runTask,
                   task,
                   )
from wdeploy import (tasks,
                     utils,
                     )

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
