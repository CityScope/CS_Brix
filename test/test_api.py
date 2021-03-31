import unittest
from brix.classes import Handler
from brix.helpers import urljoin
import requests
import random
import json

class TestEndpoints(unittest.TestCase):

	def setUp(self):
		# Pick a vaild table from cityio.media to test with
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

		self.table_data = table_data
		self.table_name = table_name

		H = Handler(self.table_name,shell_mode=True)
		self.cityIO_post_url = H.cityIO_post_url
		self.cityIO_get_url  = H.cityIO_get_url
		self.post_headers    = H.post_headers

		print('Testing with table:',raw_table_name,'as',table_name)


	def tearDown(self):
		print('Cleaning up')
		print('Deleting:',self.table_name)
		r = requests.delete(self.cityIO_get_url)

	def test_create_table(self):
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f"test_create_table Failed: table_name={self.table_name}, status_code={r.status_code}"
		)

	def test_get(self):
		# Test get for entire table
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f'test_get Failed, table could not be posted: table_name={self.table_name}, status_code={r.status_code}'
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
		# Test deep get and deep post
		r = requests.post(self.cityIO_post_url, data=json.dumps(self.table_data), headers=self.post_headers)
		self.assertEqual(
			r.status_code,200,
			msg=f'test_deep_get_post Failed, table could not be posted: table_name={self.table_name}, status_code={r.status_code}'
		)

		print('Testing deep get and deep post')
		for branch in self.table_data.keys():
			url = urljoin(self.cityIO_get_url,branch)
			r = requests.get(url)
			self.assertEqual(
				r.status_code,200,
				msg=f'test_deep_get_post GET Failed: table_name={self.table_name}, branch={branch}, status_code={r.status_code}, url={url}'			
			)
			if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
				data = r.json()
				r = requests.post(urljoin(self.cityIO_post_url,branch), data=json.dumps(data), headers=self.post_headers)
				if branch!='meta':
					self.assertEqual(
						r.status_code,200,
						msg=f'test_deep_get_post POST Failed: table_name={self.table_name}, branch={branch}, status_code={r.status_code}'
					)
				else:
					self.assertEqual(
						r.status_code,406,
						msg=f'test_deep_get_post POST Failed for meta branch: table_name={self.table_name}, branch={branch}, status_code={r.status_code}'
					)

	def table_delete(self):
		# Test table deletion
		r = requests.delete(self.cityIO_get_url)
		self.assertEqual(
			r.status_code,200,
			msg=f'table_delete Failed: table_name={self.table_name}, status_code={r.status_code}, url={self.cityIO_get_url}'
		)


if __name__ == '__main__':
	unittest.main()