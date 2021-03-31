import unittest
from brix.classes import Handler
from brix.examples import RandomIndicator, ShellIndicator, Diversity
from brix.test_tools import User
from time import sleep
import requests

class TestHandler(unittest.TestCase):

	def setUp(self):
		self.table_list = ['dungeonmaster']

	def test_hash(self):
		'''
		Test that Handler gets the right hash
		'''
		for table_name in self.table_list:
			H = Handler(table_name)
			cityIO_get_url = H.cityIO_get_url.strip('/')
			hashes = requests.get(f'{cityIO_get_url}/meta/hashes').json()
			self.assertEqual(H.get_grid_hash(),hashes['GEOGRIDDATA'])

	def test_update_package_numeric(self):
		'''
		Tests that the update package contains all the indicators passed to Handler.
		'''
		for table_name in self.table_list:
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

	def test_user(self):
		for table_name in self.table_list:
			U = User(table_name)
			U.start_user()
			H = Handler(table_name)
			initial_hash = H.get_grid_hash()
			sleep(2*U.sleep_time)
			final_hash   = H.get_grid_hash()
			self.assertNotEqual(initial_hash, final_hash)

	def test_update_package_keys(self):
		for table_name in self.table_list:
			H = Handler(table_name)
			update_package = H.update_package()
			update_package_keys = set(update_package.keys())
			self.assertIn('numeric', update_package_keys)
			self.assertIn('heatmap', update_package_keys)
			self.assertIn('textual', update_package_keys)

			if 'heatmap' in update_package_keys:
				heatmap = update_package['heatmap']
				heatmap_keys = set(heatmap.keys())
				self.assertIn('features',   heatmap_keys)
				self.assertIn('properties', heatmap_keys)
				self.assertIn('type',       heatmap_keys)

if __name__ == '__main__':
	unittest.main()