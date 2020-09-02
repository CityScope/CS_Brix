# Helper functions live here

def is_number(s):
	'''
	Returns True if input can be turned into a number, else Fals
	'''
	try:
		float(s)
		return True
	except:
		return False