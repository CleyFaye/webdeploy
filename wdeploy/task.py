# encoding=utf-8
"""Task management.

Decorators and functions required to define and run tasks.
"""
from os.path import join
from wdeploy import config
from logging import getLogger

if __name__ == '__main__':
    raise Exception('This program cannot be run in DOS mode.')
logg = getLogger(__name__)


def task(sourcePathArguments=None,
         destinationPathArguments=None,
         ):
    """Returns a decorator for tasks.

    Parameters
    ----------
    sourcePathArguments : list(string)
        A list of arguments names that will be prefixed by config().ROOT before
        running the task function.
    destinationPathArguments : list(string)
        A list of arguments names that will be prefixed by config().PREFIX
        before running the task function.


    Returns
    -------
    A suitable decorator to mark a function as a runnable task.


    Notes
    -----

    The config file contain a list of task definitions.
    A task is simply a python function called with the arguments from the task
    definition.
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
                    if isinstance(args[argName],
                                  str):
                        args[argName] = join(config().ROOT,
                                             args[argName],
                                             )
                    else:
                        args[argName] = [join(config().ROOT,
                                              x,
                                              )
                                         for x in args[argName]
                                         ]
            if destinationPathArguments:
                for argName in destinationPathArguments:
                    if isinstance(args[argName],
                                  str,
                                  ):
                        args[argName] = join(config().PREFIX,
                                             args[argName],
                                             )
                    else:
                        args[argName] = [join(config().PREFIX,
                                              x,
                                              )
                                         for x in args[argName]
                                         ]
            func(**args)
        myself.taskList[func.__name__] = processTask
        logg.debug('Registering task %s'
                   % func.__name__)
        return None
    return decorator


def runTask(taskDesc):
    """Call a task.

    Parameters
    ----------
    taskDesc : dict
        The task definition. If must contain the properties 'name' and 'args'.
        'name' is the name of the task (in fact, the name of a function using
        the @task decorator), and 'args' is a list of keyword arguments that
        will be passed to the task function.
    """
    taskName = taskDesc['name']
    taskArgs = taskDesc['args'].copy()
    logg.info('Running task "%s" (%s)'
              % (taskName,
                 taskArgs,
                 ),
              )
    task.taskList[taskName](**taskArgs)
