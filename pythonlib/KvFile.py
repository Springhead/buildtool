#!/usr/local/bin/python3.4
# -*- coding: utf-8 -*-
# ======================================================================
#  CLASS:
#	KvFile
#	    Class for making dictionary from key-value pair file.
#
#  INITIALIZER:
#	obj = KvFile(path, sep=None, list=False, desig='#', verbose=0)
#	  arguments:
#	    path:	Key-value pair file path.
#	    sep:	Separator of key and value.
#	    list:	Make value list (duplicated key allowed).
#	    desig:	Comment designator.
#	    verbose:	Verbose mode.
#
#  METHODS:
#	nitems = read()
#	    Read the file and make dictionary.
#	  returns:	Number of items in the dictionary (int).
#
#	set(key, value)
#	    Add dictionary to arbitraly key-value pair.
#	  arguments:
#	    key:	Key to add the dictionary.
#	    value:	Value associated with the key.
#
#	value = get(key)
#	    Get value associated with the key.
#	  arguments:
#	    key:	Key to get value from the dictionary.
#	  returns:	Value associated with the key (obj).
#
#	keys = keys()
#	  returns:	List of keys.
#
#	result = check(keys)
#	    Check if all of specified keys are defiend in the dictionary.
#	  arguments:
#	    keys:	List of keys to check.
#	  returns:	0: all are in the dictionary, -1: else
#
#	show(line_by_line=0)
#	  arguments:
#	    line_by_line:	>= 0: Number of preceeding spaces.
#				      (line-by-line mode)
#				else: Use system format.
#
#	errmsg = error()
#	  returns:	Error message (most recent one only) (str).
#	
#  VERSION:
#	Ver 1.0  2016/06/13 F.Kanehori	Release version.
#	Ver 1.1  2016/06/20 F.Kanehori  Add %include function.
#					Allow continued line.
#	Ver 1.2	 2016/10/03 F.Kanehori	Key-without-value introduced
#					Add keys() method.
#	Ver 1.3  2016/10/17 F.Kanehori	Rewritten by using class Fio.
#	Ver 1.4  2016/11/06 F.Kanehori	I/O class changed to TextFio.
#	Ver 1.5  2017/01/11 F.Kanehori	Correspond to TextFio.read().
#	Ver 1.6  2017/03/21 F.Kanehori	Allow key duplication.
#	Ver 2.0  2017/04/10 F.Kanehori	Ported to unix.
#	Ver 2.1  2017/04/26 F.Kanehori	Bug fixed.
#	Ver 2.11 2017/09/08 F.Kanehori	Change comments.
# ======================================================================
import sys
import re
from TextFio import *
from Util import *

class KvFile:
	#  Initializer
	#
	def __init__(self, path, sep=None, list=False, desig='#', verbose=0):
		self.clsname = self.__class__.__name__
		self.version = 2.11
		#
		self.sep = sep
		self.list = list
		self.desig = desig
		self.verbose = verbose
		#
		self.dict = {}
		self.fobj = TextFio(path, verbose=verbose)
		self.errmsg = None

	#  Read file and make dictionary.
	#
	def read(self, dic=None):
		f = self.fobj
		if f.open() < 0:
			self.errmsg = f.error()
			return -1
		f.add_filter(f.WRAP)
		f.add_filter(f.ELIM)
		f.read()
		lines = f.lineinfo()
		f.close()
		if lines is None:
			return 0
		self.dict = self.__make_dict(lines, dic)
		return len(self.dict)
		
	#  Add new key-value-pair to the dictionary.
	#
	def set(self, key, value):
		self.dict[key] = value

	#  Get the value associated with the key.
	#
	def get(self, key):
		return self.dict[key] if key in self.dict else None

	#  Get list of the keys in the dictionary.
	#
	def keys(self):
		return self.dict.keys()

	#  Check if all of specified keys are defiend.
	#
	def check(self, keys):
		result = 0
		for key in keys:
			val = self.get(key)
			if val is None:
				self.errmsg = "required key '%s' missing" % key
				result = -1
		return result

	#  Show the contents of dictionary.
	#
	def show(self, line_by_line=0):
		disp_dict = self.__make_disp_dict()
		if line_by_line:
			for key in sorted(disp_dict):
				key_part = ' ' * line_by_line + key
				val_part = ' \t' + str(disp_dict[key])
				print(key_part + val_part)
		else:
			print(disp_dict)

	def __make_disp_dict(self):
		disp_dict = {}
		for key in self.dict:
			value = self.dict[key]
			if isinstance(value, list):
				showlist = []
				for elem in value:
					showlist.append(self.__disp_elem(elem))
				disp_dict[key] = showlist
			else:
				disp_dict[key] = self.__disp_elem(value)
		return disp_dict

	def __disp_elem(self, value):
		disp_elem = str(value)
		if isinstance(value, bool):
			disp_elem += ' <bool>'
		return disp_elem

	#  Error message adapter.
	#
	def error(self):
		return self.errmsg


	# --------------------------------------------------------------
	#  For class private use
	# --------------------------------------------------------------

	#  Make dictionary.
	#
	def __make_dict(self, lines, dic):
		# arguments:
		#   lines:	Line data read from the file (list).
		# returns:	Dictionary (dict).

		dict = dic if dic is not None else {}
		for numb, line in lines:
			# %include
			m = re.match('^%include\s+([\w/\\.]+)', line)
			if m:
				if self.verbose:
					print('%%include %s' % m.group(1))
				kvf = KvFile(Util.pathconv(m.group(1)),
					     sep=self.sep, desig=self.desig,
					     verbose=self.verbose)
				if kvf is None:
					self.errmsg = 'can\'t include "%s"' % m.group(1)
					result = -1
				if kvf.read() <= 0:
					if self.verbose:
						print('-> include file empty')
					continue
				for key in kvf.keys():
					dict[key] = kvf.get(key)
				continue
			# key-value pair
			if self.sep is None:
				pair = line.rstrip().split()
			else:
				pair = line.rstrip().split(self.sep)
			if len(pair) < 2:
				self.__register(pair[0], True, dict)
			else:
				key = pair[0].strip()
				val = ' '.join(pair[1:]).strip()
				val = self.__expand(val, dict)
				self.__register(key, self.__convert(val), dict)
		return dict

	#  Expand macros.
	#  Only already registered keys are valid for macro expansion.
	#
	def __expand(self, str, dict):
		# arguments:
		#   str:	Original line data (str).
		#   dict:	Dictionary to lookup prior to self.dict.
		# returns:	Expanded line data (str).
		#		Same that input data if no macros met.

		m = re.match('([^\$]*)\$\(([^\)]+)\)(.*$)', str)
		if m:
			if self.verbose:
				group = [m.group(1), m.group(2), m.group(3)]
				msg = 'MATCH: \'' + m.group(0) + '\' => '
				msg += '[ ' + ', '.join(group) + ' ]'
				print(msg)
			if m.group(2) in dict:
				val = dict[m.group(2)]
			else:
				val = self.get(m.group(2))
			if val is not None:
				str = m.group(1) + val + m.group(3)
				str = self.__expand(str, dict)
		return str

	#  Register to the dictionary.
	#
	def __register(self, key, value, dict):
		# arguments:
		#   key:	Register key (str).
		#   value:	Value to be registered (str).
		#   dict:	Dictionary to register the value (dict).

		if self.list is False:
			# override previous value (if exists).
			dict[key] = value
		else:
			# append to the list.
			if key in dict:
				dict[key].append(value)
			else:
				dict[key] = [value]

	#  Convert 'True'/'False' to corresponding boolean value.
	#
	def __convert(self, value):
		# arguments:
		#   value:	Any object (obj).
		# returns:	True/False if value is 'True'/'False'.
		#		Otherwise value itself.

		if value in ['True', 'False']:
			return True if value == 'True' else False
		return value

# end: KvFile.py
