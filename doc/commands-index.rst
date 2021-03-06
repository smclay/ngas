.. _commands:

########
Commands
########

An NGAS server works by replying to HTTP requests sent to it. All URLs used to
contact NGAS have the following structure::

 http://<server>:<port>/<command>?<parameters>

The ``server`` and ``port`` parts indicate where the NGAS server is listening
for requests. The ``command`` part is a simple name, usually in uppercase, like
``ARCHIVE`` or ``RETRIEVE``, and indicates the action to be performed by the
server. An optional list of parameters, separated by an ampersand (&) sign, and
optionally each having a value, provides further details about the action to be
performed.

NGAS currently supports the ``POST``, ``GET`` and ``PUT`` HTTP methods only. In
general the method used to invoke a command does not make a difference, but some
commands have different behavior depending on the HTTP Method being used. Refer
to the documentation of each command for more details.

All commands return an HTTP status code that reflects the outcome of the
operation (200 for success, 3xx for redirections, 4xx for errors). Additionally
some commands return a *status* XML document with a more detailed description of
the operation result.

One can configure an NGAS server to accept HTTP requests only from authenticated
users, and moreover to allow certain commands to certain users only. Please
refer to :ref:`server.authorization` for more details.

The following is a list of the most relevant commands supported by NGAS. More
commands can be added in the form of *plug-ins*
(see :doc:`plugins/commands` for details).

There are three ways in which commands are found by NGAS:

* There is a fixed set of built-in commands.
  Users cannot override these with their own.
  Commands like ``RETRIEVE`` and ``STATUS`` belong to this category.
* Modules with a name following the pattern ``ngamsPlugin.ngamsCmd_<CMD>``.
  For historical reasons there are a number of commands
  that are shipped with NGAS, but that are implemented as plug-ins,
  and are named following this pattern.
  In future releases these will be shipped as regular built-in commands,
  and therefore this special pattern will no longer be considered.
* User-written plug-ins that are registered
  in the :ref:`config.commands` section of the server configuration.


.. toctree::

	commands/core
	commands/storage
	commands/containers
	commands/others
