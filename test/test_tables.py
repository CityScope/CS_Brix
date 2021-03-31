import unittest
from brix.classes import Handler
from brix.helpers import urljoin
import requests
import random
import json

class TestEndpoints(unittest.TestCase):

	def setUp(self):
		self.table_list   = ['dungeonmaster']

	def test_get(self):
		for table_name in self.table_list:
			H = Handler(table_name)

			r = requests.get(H.cityIO_get_url)
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

	def test_deep_get(self):
		for table_name in self.table_list:
			H = Handler(table_name)

			r = requests.get(urljoin(H.cityIO_get_url,'indicators'))
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

			# r = requests.get(urljoin(H.cityIO_get_url,'access'))
			# self.assertEqual(r.status_code,200)
			# self.assertEqual(r.headers['Content-Type'],'application/json')

			r = requests.get(urljoin(H.cityIO_get_url,H.GEOGRIDDATA_varname))
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

			r = requests.get(urljoin(H.cityIO_get_url,H.GEOGRID_varname))
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

			r = requests.get(urljoin(H.cityIO_get_url,H.GEOGRID_varname,'features'))
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

			r = requests.get(urljoin(H.cityIO_get_url,H.GEOGRID_varname,'properties'))
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

			r = requests.get(urljoin(H.cityIO_get_url,H.GEOGRID_varname,'type'))
			self.assertEqual(r.status_code,200)
			self.assertEqual(r.headers['Content-Type'],'application/json')

	def test_post(self):
		for table_name in self.table_list:
			H = Handler(table_name)

			r = requests.get(H.cityIO_get_url)
			if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
				data = r.json()
				r = requests.post(H.cityIO_post_url, data=json.dumps(r.json()), headers=H.post_headers)
				self.assertEqual(r.status_code,200)

	def test_deep_post(self):
		for table_name in self.table_list:
			H = Handler(table_name)

			r = requests.get(urljoin(H.cityIO_get_url,H.GEOGRIDDATA_varname))
			if (r.status_code==200) and (r.headers['Content-Type']=='application/json'):
				data = r.json()
				r = requests.post(urljoin(H.cityIO_post_url,H.GEOGRIDDATA_varname), data=json.dumps(r.json()), headers=H.post_headers)
				self.assertEqual(r.status_code,200)


if __name__ == '__main__':
	unittest.main()