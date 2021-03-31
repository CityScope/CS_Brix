import unittest
from brix.classes import Handler
from brix.helpers import urljoin
import requests
import random
import json

class TestEndpoints(unittest.TestCase):

	def setUp(self):
		self.table_list = []

	def tearDown(self):
		print('Cleaning up')
		for table_name in self.table_list:
			print('Deleting:',table_name)
			H = Handler(table_name,shell_mode=True)
			r = requests.delete(H.cityIO_get_url)

	def test_pipeline(self):
		'''
		Test with a random table from cityio
		'''
		
		r = requests.get('https://cityio.media.mit.edu/api/tables/list/')
		table_list = r.json()

		valid_table = False
		while not valid_table:
			raw_table_name = random.choice(table_list).strip('/').split('/')[-1]
			table_name = f'{raw_table_name}_brix_test_table'
			r = requests.get(f'https://cityio.media.mit.edu/api/table/{raw_table_name}')

			if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
				table_data = r.json()
				if (table_data!='access restricted') and ('GEOGRID' in table_data.keys()):
					valid_table = True
				
		self.table_list.append(table_name)

		print('Testing with table:',raw_table_name,'as',table_name)
		H = Handler(table_name,shell_mode=True)

		# Test table create
		print('Creating table')
		r = requests.post(H.cityIO_post_url, data=json.dumps(table_data), headers=H.post_headers)
		self.assertEqual(r.status_code,200)

		# Test get
		print('Testing GET for entire table')
		r = requests.get(H.cityIO_get_url)
		self.assertEqual(r.status_code,200)
		self.assertEqual(r.headers['Content-Type'],'application/json')

		# Test post
		print('Testing POST for entire table')
		if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
			data = r.json()
			r = requests.post(H.cityIO_post_url, data=json.dumps(data), headers=H.post_headers)
			self.assertEqual(r.status_code,200)

		# Test deep get and deep post
		print('Testing deep get and deep post')
		for branch in table_data.keys():
			print(f'\tTesting GET for {branch}')
			r = requests.get(urljoin(H.cityIO_get_url,branch))
			self.assertEqual(r.status_code,200)
			if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
				data = r.json()
				print(f'\tTesting POST for {branch}')
				r = requests.post(urljoin(H.cityIO_post_url,branch), data=json.dumps(data), headers=H.post_headers)
				if branch!='meta':
					self.assertEqual(r.status_code,200)
				else:
					self.assertEqual(r.status_code,406)
		
		# Test table deletion
		print(f'Testing table deletion')
		r = requests.delete(H.cityIO_get_url)
		self.assertEqual(r.status_code,200)

if __name__ == '__main__':
	unittest.main()