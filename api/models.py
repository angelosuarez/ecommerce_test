from django.db import models
from django.utils import timezone
from django.conf import settings
import requests
import locale

locale.setlocale(locale.LC_ALL, "")

class Product(models.Model):

	name = models.CharField(max_length=60, unique=True)
	price = models.FloatField(default='0')
	stock = models.IntegerField(default=0)

	def save(self, *args, **kwargs):
		self.name = self.name.title()
		super(Product, self).save(*args, **kwargs)

	"""
	def valid_stock(self, order_data):
		return self.stock < 0

	def subtract_stock(self, order_data):
		product = self.objects.get(
			id=order_data['product'].id)
		if not product:
			raise 'Product is not exist'

		product.stock = product.stock - order_data['quantity']

		if self.valid_stock:
			raise 'Insufficient stock to order'

		product.save()
	"""

	def __str__(self):
		return self.name


class Order(models.Model):

	date_time = models.DateTimeField(null=False, default=timezone.now)

	def __str__(self):
		return f'Order #{self.id}-{self.date_time}'

	@property
	def get_total(self):
		total = 0
		for d in OrderDetail.objects.all().filter(order_id=self.id):
			total += d.product.price * d.quantity
		return total
	

	@property
	def get_total_usd(self):
		try:
			response_api = requests.get(
				settings.EXTERNAL_APIS_CONF['DOLLAR_EXCHANGE']
			)
			exchange = [x.get('casa', {}) for x in response_api.json() \
				if x.get('casa', {}).get('nombre') == 'Dolar Blue'][0].get('venta', 1)
			return round(self.get_total / locale.atof(exchange), 2)

		except:
			return 'Not allowed'


class OrderDetail(models.Model):

	order = models.ForeignKey(
		Order,
		on_delete=models.PROTECT,
		related_name='order_details'
	)
	quantity = models.IntegerField(default=0)
	product = models.ForeignKey(
		Product,
		on_delete=models.PROTECT,
		related_name='product_order_details'
	)

