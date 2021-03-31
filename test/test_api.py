# Author: C. Jara-Figueroa
# Last updated: March 31st, 2021
# Unittest for new cityio API using requests and cs-brix
# This test copies a table from cityio.media.mit.edu into cityiotest.mirage.city and runs tests on it
# Deletes table afterwars

import unittest
from brix.classes import Handler
from brix.helpers import urljoin
import requests
import random
import json

class TestEndpoints(unittest.TestCase):
	stable_host = 'cityio.media.mit.edu'
	use_brix = True

	def setUp(self):
		'''
		Pick a random valid table from cityio.media to clone.
		Valid tables have at least a GEOGRID endpoint, are not restricted access, and do not exist in cityiotest.
		Uses the get and post urls from brix.Handler. This also tests brix's behavior. 

		'''
		if self.use_brix: # Get parameters directly from brix
			self.host = Handler.remote_host
			self.post_headers = Handler.cityio_post_headers
		else:
			self.host = 'https://cityiotest.mirage.city' 
			self.post_headers  = {'Content-Type': 'application/json'}

		r = requests.get(f'https://{self.stable_host}/api/tables/list/')
		table_list = r.json()

		r = requests.get(urljoin(self.host,'api/tables/list'))
		table_list_mirage = r.json()

		valid_table = False
		while not valid_table:
			raw_table_name = random.choice(table_list).strip('/').split('/')[-1]
			table_name = f'{raw_table_name}_brix_table_for_unittest'
			if table_name not in table_list_mirage:
				r = requests.get(f'https://{self.stable_host}/api/table/{raw_table_name}')
				if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
					table_data = r.json()
					if (table_data!='access restricted') and ('GEOGRID' in table_data.keys()):
						valid_table = True
		self.table_data = table_data
		self.table_name = table_name

		
		if self.use_brix: # retrieve GET and POST urls directly from brix
			H = Handler(self.table_name,shell_mode=True) 
			self.cityIO_post_url = H.cityIO_post_url
			self.cityIO_get_url  = H.cityIO_get_url
		else:
			self.cityIO_get_url  = urljoin(self.host,'api/table',self.table_name)
			self.cityIO_post_url = urljoin(self.host,'api/table',self.table_name)

		print('Testing with table:',raw_table_name,'as',table_name,'in',self.host,f'brix={self.use_brix}')


	def tearDown(self):
		'''
		Delete the table that we tested with.
		'''
		print('Cleaning up:',self.table_name)
		r = requests.delete(self.cityIO_get_url)

	def test_create_table(self):
		'''
		Tests create table endpoint by posting the table_data.
		'''
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f"test_create_table Failed: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_post_url}, post_headers={self.post_headers}"
		)

	def test_get(self):
		'''
		Test GET for entire table. 
		As test methos run asynchronously, this method posts the table again and alerts when post failed.
		'''
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f'test_get Failed, test-table could not be posted: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_post_url}'
		)
		r = requests.get(self.cityIO_get_url)
		self.assertEqual(
			r.status_code,200,
			msg=f'test_get Failed: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_get_url}'
		)
		self.assertEqual(
			r.headers['Content-Type'],'application/json',
			msg=f"test_get Failed with wrong Content-Type: table_name={self.table_name}, content_type={r.headers['Content-Type']}, url={self.cityIO_get_url}"
		)

	def test_deep_get_post(self):
		'''
		Tests GET and POST from deeper endpoints, going through all available table_name/endpoint. 
		Tests that meta is not writeable.
		As test methos run asynchronously, this method posts the table again and alerts when post failed.
		'''
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f'test_deep_get_post Failed, test-table could not be posted: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_post_url}'
		)

		for branch in self.table_data.keys():
			url = urljoin(self.cityIO_get_url,branch)
			r = requests.get(url)
			self.assertEqual(
				r.status_code,200,
				msg=f'test_deep_get_post GET Failed: table_name={self.table_name}, branch={branch}, status_code={r.status_code}, url={url}'			
			)
			if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
				data = r.json()
				url = urljoin(self.cityIO_post_url,branch)
				r = requests.post(url, data=json.dumps(data), headers=self.post_headers)
				if branch!='meta':
					self.assertEqual(
						r.status_code,200,
						msg=f'test_deep_get_post POST Failed: table_name={self.table_name}, branch={branch}, status_code={r.status_code}, url={url}, post_headers={self.post_headers}'
					)
				else:
					self.assertEqual(
						r.status_code,406,
						msg=f'test_deep_get_post POST Failed for meta branch: table_name={self.table_name}, branch={branch}, status_code={r.status_code}, url={url}, post_headers={self.post_headers}'
					)

	def table_delete(self):
		'''
		Tests whether the table can be deleted.
		As test methos run asynchronously, this method posts the table again and alerts when post failed.
		'''
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f'table_delete Failed, test-table could not be posted: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_post_url}, post_headers={self.post_headers}'
		)
		r = requests.delete(self.cityIO_get_url)
		self.assertEqual(
			r.status_code,200,
			msg=f'table_delete Failed: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_get_url}'
		)

if __name__ == '__main__':
	unittest.main()