import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class ClicohTestCases(TestCase):
	path = ''
	default_data = {}

	def authenticate(self):
		if not len(User.objects.all()):
			user = User(
				email='asuarez@test.com',
				first_name='Testing',
				last_name='Testing',
				username='testing_login'
			)
			user.set_password('admin123')
			user.save()

		client = APIClient()
		response = client.post(
			'/api/token/', {
				'email': 'asuarez@test.com',
				'username': 'testing_login',
				'password': 'admin123'
			})

		return f'Bearer {response.json()["access"]}'

	def parser(self, data):
		return json.loads(data.content)

	def api_client(self):
		client = APIClient()
		client.credentials(
			HTTP_AUTHORIZATION=self.authenticate())
		return client

	def create(self):
		return self.api_client().post(
			f'/{self.path}/', self.default_data)

	def get(self, id=None):
		return self.api_client().get(
			f'/{self.path}/{f"{id}/" if id else ""}')

	def delete(self, id):
		return self.api_client().delete(
			f'/{self.path}/{id}/')


class ProductTestCase(ClicohTestCases):
	path = 'products'
	default_data = {
		'name': 'Notebook lenovo legion',
		'price': '225000',
		'stock': 12
	}

	def test_create(self):
		response = self.create()
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	def test_list(self):
		self.create()
		response = self.get()
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(len(json.loads(response.content)) > 0)

	def test_get(self):
		product = self.parser(self.create())
		response = self.get(product['id'])
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(self.parser(response), {
			'id': 1, 'name': 'Notebook Lenovo Legion', 'price': 225000.0, 'stock': 12})

	def test_update(self):
		product = self.parser(self.create())
		response = self.api_client().put(
			f'/{self.path}/{product["id"]}/', {
			'name': 'Notebook Lenovo Legion Update',
			'price': '225500',
			'stock': 10
		})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(self.parser(response), {
			'id': 1, 'name': 'Notebook Lenovo Legion Update', 'price': 225500.0, 'stock': 10})

	def test_update_stock(self):
		product = self.parser(self.create())

		response = self.api_client().patch(
			f'/{self.path}/{product["id"]}/', {'stock': 200})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(self.parser(response).get('stock'), 200)

	def test_delete(self):
		record = self.parser(self.create())
		response = self.delete(record['id'])

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class OrderTestCase(ClicohTestCases):
	path = 'orders'

	def test_create(self):
		response = self.create()
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	def test_list(self):
		self.create()
		ProductTestCase().create()
		detail = OrderDetailsTestCase().create()
		response = self.get()

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(len(self.parser(response)) > 0)

		for data in self.parser(response):
			self.assertTrue(len(data.get('order_details')) > 0)
			self.assertEqual(data.get('order_details'), [
				self.parser(detail)])

	def test_get(self):
		order = self.parser(self.create())
		ProductTestCase().create()
		detail = OrderDetailsTestCase().create()

		response = self.get(order['id'])
		data = self.parser(response)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(len(data) > 0)
		self.assertEqual(data.get('order_details'), [
			self.parser(detail)])

	def test_delete(self):
		record = self.parser(self.create())
		response = self.delete(record['id'])
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class OrderDetailsTestCase(ClicohTestCases):

	path = 'order_details'
	default_data = {
		'quantity': 1,
		'order': 1,
		'product': 1
	}

	def set_quantity(self, value):
		self.default_data['quantity'] = value

	def test_create(self):
		OrderTestCase().create()
		product = self.parser(
			ProductTestCase().create())
		response = self.create()
		product_afer_used = self.parser(
			ProductTestCase().get(product['id']))

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(product['stock'] > product_afer_used['stock'])

	def test_list(self):
		self.test_create()
		response = self.get()

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(len(self.parser(response)) > 0)

	def test_get(self):
		self.test_create()
		response = self.get(1)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(self.parser(response), {
			'id': 1, 'quantity': 1, 'product': 1, 'order': 1})

	def test_update(self):
		self.test_create()
		product_afer_create = self.parser(
			ProductTestCase().get(1))
		self.set_quantity(10)
		response = self.api_client().put(
			f'/{self.path}/1/', self.default_data)
		self.set_quantity(1)

		product_afer_update = self.parser(
			ProductTestCase().get(product_afer_create["id"]))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(product_afer_update['stock'] < product_afer_create['stock'])

	def test_add_duplicated_product_error(self):
		OrderTestCase().create()
		ProductTestCase().create()
		self.create()
		response = self.create()

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data[0].title(),
			'The Product Already Exists In The List')

	def test_add_stock_product_error(self):
		OrderTestCase().create()
		ProductTestCase().create()
		self.set_quantity(1000)

		response = self.create()
		self.set_quantity(1)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data[0].title(),
			'Insufficient Stock To Assign To Order')

	def test_add_product_qty_zero_error(self):
		OrderTestCase().test_create()
		ProductTestCase().create()
		self.set_quantity(0)

		response = self.create()
		self.set_quantity(1)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data[0].title(),
			'The Product Quantity Must Be More Than Zero')

	def test_delete(self):
		OrderTestCase().create()
		product = self.parser(
			ProductTestCase().create())
		detail = self.parser(self.create())
		response = self.delete(detail['id'])

		product_afer_delete = self.parser(
			ProductTestCase().get(product['id']))

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertEqual(product['stock'], product_afer_delete['stock'])

