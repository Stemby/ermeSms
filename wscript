#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import Configure
import Utils

# the following two variables are used by the target "waf dist"
APPNAME="MoioSMS"
VERSION = "2.19.15"

VERSION_MAJOR_MINOR = ".".join(VERSION.split(".")[0:2])

# these variables are mandatory ('/' are converted automatically)
srcdir = '.'
blddir = 'build'

def dist():
	"""Make the dist tarball and print its SHA-1 """
	import Scripting
	Scripting.g_gz = "gz"
	Scripting.dist(APPNAME, VERSION)

def set_options(opt):
	# options for disabling pyc or pyo compilation
	opt.tool_options("python")
	opt.tool_options("misc")
	opt.tool_options("gnu_dirs")
	opt.add_option('--nopyo',action='store_false',default=False,help='Do not install optimised compiled .pyo files [This is the default for Kupfer]',dest='pyo')
	opt.add_option('--pyo',action='store_true',default=False,help='Install optimised compiled .pyo files [Default:not install]',dest='pyo')

def configure(conf):
	conf.check_tool("python")
	conf.check_python_version((2,5,0))
	conf.check_tool("misc gnu_dirs")

	# BUG: intltool requires gcc
	#conf.check_tool("gcc intltool")

	python_modules = """
		pycurl
		PyQt4
		"""
	for module in python_modules.split():
		conf.check_python_module(module)

	Utils.pprint("NORMAL", "Checking optional dependencies:")

	opt_programs = ["gocr", "ocrad", "gm"]
	for prog in opt_programs:
		prog_path = conf.find_program(prog)

	#~ try:
		#~ conf.check_python_module("<module name>")
	#~ except Configure.ConfigurationError, e:
		#~ Utils.pprint("RED", "Python module <module name> is recommended")
		#~ Utils.pprint("RED", "Please see README")
		
	opt_pymodules = "pynotify psutil".split()
	for mod in opt_pymodules:
		try:
			conf.check_python_module(mod)
		except Configure.ConfigurationError, e:
			Utils.pprint("YELLOW", "python module %s is recommended" % mod)

	conf.env["VERSION"] = VERSION

	# Check sys.path
	Utils.pprint("NORMAL", "Installing python modules into: %(PYTHONDIR)s" % conf.env)
	pipe = os.popen("""%(PYTHON)s -c "import sys; print '%(PYTHONDIR)s' in sys.path" """ % conf.env)
	if "False" in pipe.read():
		Utils.pprint("YELLOW", "Please add %(PYTHONDIR)s to your sys.path!" % conf.env)

def new_module(bld, name, sources=None):
	if not sources: sources = name
	obj = bld.new_task_gen("py")
	obj.find_sources_in_dirs(sources)
	obj.install_path = "${PYTHONDIR}/%s" % name
	return obj


def build(bld):

	# modules
	new_module(bld, "moio")
	new_module(bld, "moio/errors")
	new_module(bld, "moio/lib")
	new_module(bld, "moio/plugins")
	new_module(bld, "moio/plugins/books")
	new_module(bld, "moio/plugins/captchadecoders")
	new_module(bld, "moio/plugins/senders")
	new_module(bld, "moio/plugins/uis")
	
	bld.install_files("${BINDIR}", "moiosms", chmod=0775)

	bld.add_subdirs("data")

def shutdown():
	pass

