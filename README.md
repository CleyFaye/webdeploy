WebDeploy
=========

This package allow automation of a few repetitive tasks involved when deploying a web application.
It is made to work with Django projects, but that's not a requirement.

Some of the tasks are:

* Copying all source files in an out-of-tree structure
* Compressing/minifying ressources (Javascript, pictures...)
* Generating apache configuration and wsgi scripts
* Creating directories structure


Setup
-----

To operate, this script require a config.py file to exist.
This file must define a set of variables that will define the project.


Config
------

The config.py file must define at least the following variables:
- TASKS: a list of task definition; each task will be executed in order. A single task definition is a tuple made of an information string (displayed to the user), the task name, and the task arguments.
- ROOT: the root directory of the project. Most tasks will assume that source paths are relative to this directory
- PREFIX: the destination directory. Most tasks will assume that target paths are relative to this directory
- PROJECT\_NAME: the name of the project
- PREFIX\_USER: the system user owning the prefix directory
- PREFIX\_GROUP: the system group owning the prefix directory
- PREFIX\_PERMISSIONS: the permissions to set on the prefix directory


Tasks
-----


### a2site

Enable or disable an apache site configuration.
This is based on the a2ensite and a2dissite command.
Arguments are a boolean indicating if the site should be enabled, and the site name, matching the config filename in the apache configuration.


### apachecfg

Generate a suitable apache configuration file for a vhost hosting the site.
See wdeploy.tasks.apachecfg() for more info.


### cgi

Generate a suitable wsgi file for a Django application.
Argument is the path to generate the file into.


### create\_symlink

Create a symlink.
Arguments are source and destination.


### makefile

Run a makefile.
Arguments are the script name, the target to build, makefile arguments as a dictionary, and a boolean indicating if the makefile must run as root, or as the user specified in the configuration.


### makepages

Build static page files by combining headers, body and footers.
See wdeploy.tasks.makepages() for more info.


### mkdir

Create a new directory.
Argument is the directory name.


### service

Perform an action on a system service.
This will attempt to use systemctl if available, and fallback to service.
Arguments are the action and the service name.


### synctree

Mirror a directory tree into another directory.
Arguments are source directory, destination directory and a boolean indicating if we must delete stalled files (files present in destination but not in source).


### third

Add third-party dependencies to the output directory.
Read a list of json files describing third party dependencies.
See wdeploy.tasks.third() for more info.

