# encoding=utf-8
from os.path import join
from wdeploy import config


"""
Task management.

Decorators and functions required to define and run tasks.
"""
if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')


def task(sourcePathArguments=None,
         destinationPathArguments=None,
         ):
    """Decorator for tasks.

    The config file contain a list of task definitions.
    A task is simply a python function called with the arguments from the task
    definition.

    The sourcePathArguments is a list of kw args that will be prefixed with
    config().ROOT
    The destinationPathArguments is a list of kw args that will be prefixed
    with config().PREFIX
    Both can be either a string, or a list.
    """
    def decorator(func):
        myself = task
        try:
            myself.taskList
        except AttributeError:
            myself.taskList = {}

        def processTask(**kwargs):
            args = kwargs.copy()
            if sourcePathArguments:
                for argName in sourcePathArguments:
                    if isinstance(args[argName], str):
                        args[argName] = join(config().ROOT, args[argName])
                    else:
                        args[argName] = [join(config().ROOT, x)
                                         for x in args[argName]]
            if destinationPathArguments:
                for argName in destinationPathArguments:
                    if isinstance(args[argName], str):
                        args[argName] = join(config().PREFIX, args[argName])
                    else:
                        args[argName] = [join(config().PREFIX, x)
                                         for x in args[argName]]
            func(**args)
        myself.taskList[func.func_name] = processTask
        return None
    return decorator


def runTask(taskDesc):
    """Call a task.

    A task definition is a list starting with the task name, and followed by
    the task function and arguments.
    """
    taskName = taskDesc['name']
    taskArgs = taskDesc['args'].copy()
    task.taskList[taskName](**taskArgs)
