debug = 0

def parseLine(patterns,line,results = {}):
	"""Function which runs through the hash table of
	regular expression keys and functions to extract line meaning
	which are returned as a hash table of results"""
	if debug: print 'Parsing: ', line,
	parsed = 0
	for pattern,parser in patterns.items():
		m = pattern.match(line)
		if m:
		   results.update(m.groupdict())
		   results['Match'] = parser.func_name
		   parser(results)
		   if parsed: print "ERROR: parsed twice",line
		   parsed = 1
		   if debug: print 'Parsed: ', results['Match'], m.groupdict()
	if not parsed:
		print "ERROR:  unparsed",line
		#raise EOFError

def parseFile(patterns, filename, results = {}):
	"""Run through a file, pulling out interesting info"""
	if debug:
		print 'Parsing FILE',filename
	for line in open(filename,'r'):
		parseLine(patterns,line,results)
	return results
