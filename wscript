#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import Configure
import Options
import Utils

# the following two variables are used by the target "waf dist"
APPNAME="MoioSMS"
VERSION = "2.19.17"

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
    opt.add_option('--nopyo',action='store_false',default=False,help='Do not install optimised compiled .pyo files [This is the default]',dest='pyo')
    opt.add_option('--pyo',action='store_true',default=False,help='Install optimised compiled .pyo files [Default:not install]',dest='pyo')
    opt.add_option('--nopyc',action='store_false',default=False,help='Do not install compiled .pyc files [This is the default]',dest='pyc')
    opt.add_option('--no-runtime-deps',action='store_false',default=True,
        help='Do not check for any runtime dependencies',dest='check_deps')
    opt.add_option('--pythondir-install',action='store_true',default=False,
        help="Install Kupfer's modules as standard python modules [Default: Install into DATADIR]",
        dest='pythondir_install')

def configure(conf):
    conf.check_tool("python")
    conf.check_python_version((2,5,0))
    conf.check_tool("misc gnu_dirs")

    conf.env["MOIOSMS"] = Utils.subst_vars("${BINDIR}/moiosms", conf.env)
    conf.env["VERSION"] = VERSION

    if not Options.options.pythondir_install:
        conf.env["PYTHONDIR"] = Utils.subst_vars("${DATADIR}/moiosms", conf.env)
    Utils.pprint("NORMAL",
        "Installing python modules into: %(PYTHONDIR)s" % conf.env)

    if not Options.options.check_deps:
        return

	python_modules = """
		pycurl
		PyQt4
		"""
	for module in python_modules.split():
		conf.check_python_module(module)

    Utils.pprint("NORMAL", "Checking optional dependencies:")

    opt_programs = {
            "gocr": "",
            "ocrad": "",
            "gm": ""
    }
    opt_pymodules = {
            "pynotify": "",
            "psutil": "",
            "vobject": "",
            "evolution": ""
    }

    for prog in opt_programs:
        prog_path = conf.find_program(prog, var=prog.replace("-", "_").upper())
        if not prog_path:
            Utils.pprint("YELLOW", "Optional, allows: %s" % opt_programs[prog])

    for mod in opt_pymodules:
        try:
            conf.check_python_module(mod)
        except Configure.ConfigurationError, e:
            Utils.pprint("YELLOW", "module %s is recommended, allows %s" % (
                mod, opt_pymodules[mod]))

def _new_package(bld, name):
    """Add module @name to sources to be installed,
    where the name is the full (relative) path to the package
    """
    obj = bld.new_task_gen("py")
    obj.find_sources_in_dirs(name)
    obj.install_path = "${PYTHONDIR}/%s" % name
    return obj

def _find_packages_in_directory(bld, name):
    """Go through directory @name and recursively add all
    Python packages with contents to the sources to be installed
    """
    for dirname, dirs, filenames in os.walk(name):
        if "__init__.py" in filenames:
            _new_package(bld, dirname)

def _dict_slice(D, keys):
	return dict((k,D[k]) for k in keys)

def build(bld):
    bld.env["VERSION"] = VERSION

    obj = bld.new_task_gen(
        source="moiosms.py",
        install_path="${PYTHONDIR}")

    # modules
    _find_packages_in_directory(bld, "moio")

    binary_subst_file = "moiosms-activate.sh"
    bin = bld.new_task_gen("subst",
        source = binary_subst_file,
        target = "data/moiosms",
        install_path = "${BINDIR}",
        chmod = 0755,
        dict = _dict_slice(bld.env, "PYTHON PYTHONDIR".split()))

    bld.add_subdirs("data")

def shutdown():
	pass

