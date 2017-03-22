# encoding=utf-8
from .configloader import config
from .task import (
        runTask,
        task,
        )
import wdeploy.tasks
import wdeploy.utils

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
