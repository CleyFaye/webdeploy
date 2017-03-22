# encoding=utf-8
"""
Task management.

Decorators and functions required to define and run tasks.
"""
if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


def task(func):
    """Decorator for tasks.

    The config file contain a list of task definitions.
    A task is simply a python function called with the arguments from the task
    definition.
    """
    myself = task
    try:
        myself.taskList
    except AttributeError:
        myself.taskList = {}
    myself.taskList[func.func_name] = func
    return None


def runTask(taskDesc):
    """Call a task.

    A task definition is a list starting with the task name, and followed by
    the task function and arguments.
    """
    taskName = taskDesc[1]
    taskArgs = list(taskDesc)[2:]
    task.taskList[taskName](*taskArgs)
