import os
from setuptools import setup


def read(fname,
         ):
    """Utility function to read the README file.

    Notes
    -----
    This is used for the long_description.
    """
    return open(os.path.join(os.path.dirname(__file__),
                             fname),
                'r',
                'utf-8',
                ).read()


setup(name="web_deploy",
      version="0.2.1",
      author="Gabriel Paul 'Cley Faye' Risterucci",
      author_email="gabriel.risterucci@gmail.com",
      description=("A basic tool to automate the tasks involved in deploying a"
                   "Django web project into a runtime directory"),
      license="MIT",
      keywords="deploy django make",
      url="https://repos.cleyfaye.net/trac/WebDeploy",
      py_modules=['webdeploy'],
      packages=['wdeploy',
                'wdeploy.tasks',
                ],
      entry_points={
          'console_scripts': ['webdeploy=webdeploy:main'],
      },
      long_description=read('README.md'),
      python_requires='>=3',
      classifiers=[
          "Development Status :: 4 - Beta",
          "Topic :: Software Development :: Build Tools",
          "License :: OSI Approved :: MIT License",
      ],
      )
