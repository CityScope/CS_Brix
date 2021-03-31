import unittest
from brix.classes import Handler
from brix.helpers import urljoin
import requests
import json

class TestEndpoints(unittest.TestCase):

	def setUp(self):
		self.table_name = 'dungeonmaster'

		self.post_headers = Handler.cityio_post_headers
		self.GEOGRID_varname = Handler.GEOGRID_endpoint
		self.GEOGRIDDATA_varname = Handler.GEOGRIDDATA_endpoint

		H = Handler(self.table_name)
		self.cityIO_get_url = H.cityIO_get_url
		self.cityIO_post_url = H.cityIO_post_url

	def tearDown(self):
		pass

	def test_get(self):	
		r = requests.get(self.cityIO_get_url)
		self.assertEqual(r.status_code,200)
		self.assertEqual(r.headers['Content-Type'],'application/json')

	def getpost_branch(self,branch,expected_get_exit_status=200,expected_post_exit_status=200):
		r = requests.get(urljoin(self.cityIO_get_url,branch))
		self.assertEqual(
			r.status_code, expected_get_exit_status,
			msg=f'GET Failed for {branch}, status_code={r.status_code}'
		)
		self.assertEqual(
			r.headers['Content-Type'], 'application/json',
			msg=f"GET Failed for {branch}, wrong Content-Type, Content-Type={r.headers['Content-Type']}"
		)
		if (r.status_code==expected_get_exit_status) and (r.headers['Content-Type']=='application/json'):
			data = r.json()
			r = requests.post(urljoin(self.cityIO_post_url,branch), data=json.dumps(data), headers=self.post_headers)
			self.assertEqual(
				r.status_code,expected_post_exit_status,
				msg=f'POST Failed for {branch}, status_code={r.status_code}'
			)

	def test_getpost_meta(self):
		branch = 'meta'
		self.getpost_branch(branch,expected_post_exit_status=406)
		
	def test_getpost_indicators(self):
		branch = 'indicators'
		self.getpost_branch(branch)

	def test_getpost_access(self):
		branch = 'access'
		self.getpost_branch(branch)

	def test_get_GEOGRIDDATA(self):
		branch = self.GEOGRIDDATA_varname
		self.getpost_branch(branch)

	def test_get_GEOGRID(self):
		branch = self.GEOGRID_varname
		self.getpost_branch(branch)
	
	def test_get_GEOGRID_features(self):
		branch = self.GEOGRID_varname+'/features'
		self.getpost_branch(branch)

	def test_get_GEOGRID_properties(self):
		branch = self.GEOGRID_varname+'/properties'
		self.getpost_branch(branch)

	def test_get_GEOGRID_type(self):
		branch = self.GEOGRID_varname+'/type'
		self.getpost_branch(branch)

if __name__ == '__main__':
	unittest.main()