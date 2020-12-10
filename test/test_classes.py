import unittest
from brix.classes import Handler
from brix.examples import RandomIndicator, ShellIndicator, Diversity

import requests
class TestHandler(unittest.TestCase):

	def test_hash(self):
		'''
		Test that Handler gets the right hash
		'''
		table_name = 'dungeonmaster'
		H = Handler(table_name)
		hashes = requests.get(f'https://cityio.media.mit.edu/api/table/{table_name}/meta/hashes').json()
		self.assertEqual(H.get_grid_hash(),hashes['GEOGRIDDATA'])

	def test_update_package_numeric(self):
		'''
		Tests that the update package contains all the indicators passed to Handler.
		'''
		table_name = 'dungeonmaster'
		H = Handler(table_name)
		geogrid_data = H.get_geogrid_data()

		indicator_list = []
		rand = RandomIndicator()
		indicator_list.append(rand)
		shell = ShellIndicator()
		indicator_list.append(shell)
		div = Diversity()
		indicator_list.append(div)
		H.add_indicators(indicator_list)

		names = []
		for I in indicator_list:
			value = I.return_indicator(geogrid_data)
			if isinstance(value,float):
				names.append(I.name)
			elif isinstance(value,dict):
				if 'name' in value.keys():
					names.append(value['name'])
				else:
					names.append(I.name)
			elif isinstance(value,list):
				names+=[i['name'] for i in value]
			else:
				names.append(I.name)
		print('Indicators used:',names)

		package = H.update_package()
		package_names = [i['name'] for i in package['numeric']]

		for name in names:
			self.assertIn(name,package_names)

if __name__ == '__main__':
    unittest.main()