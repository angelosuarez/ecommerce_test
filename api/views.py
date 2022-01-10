from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.serializers import ValidationError
from .serializers import ProductSerializer, OrderSerializer, OrderDetailSerializer
from .models import Product, Order, OrderDetail



ERROS = {
	'PRODUCT_QTY': 'The Product Quantity must be more than zero',
	'PRODUCT_DUPLI': 'The product already exists in the list',
	'PRODUCT_STOCK': 'Insufficient stock to assign to order'
}


class ProductViewSet(viewsets.ModelViewSet):
	queryset = Product.objects.all().order_by('name')
	serializer_class = ProductSerializer
	#authentication_classes = [TokenAuthentication] pendiente de hacer

	def get_permissions(self):
		permission_classes = [IsAuthenticated]
		return [permission() for permission in permission_classes]

	def perform_destroy(self, instance):
		try:
			instance.delete()
		except Exception as e:
			raise ValidationError(e)
			

class OrderViewSet(viewsets.ModelViewSet):
	queryset = Order.objects.all().order_by('-date_time')
	serializer_class = OrderSerializer

	def get_permissions(self):
		permission_classes = [IsAuthenticated]
		return [permission() for permission in permission_classes]

	def perform_destroy(self, instance):
		#pendiente
		OrderDetail.objects.all().filter(
			order_id=instance.id
		).delete()

		instance.delete()

class OrderDetailViewSet(viewsets.ModelViewSet):
	queryset = OrderDetail.objects.all()
	serializer_class = OrderDetailSerializer

	def get_permissions(self):
		permission_classes = [IsAuthenticated]
		return [permission() for permission in permission_classes]

	def perform_create(self, serializer):
		product = serializer.validated_data.get('product')
		order = serializer.validated_data.get('order')
		quantity = serializer.validated_data.get('quantity')

		if quantity == 0:
			raise ValidationError(ERROS['PRODUCT_QTY'])

		if self.queryset.filter(
			order_id=order.id,
			product_id=product.id):
			raise ValidationError(ERROS['PRODUCT_DUPLI'])

		product.stock -= quantity

		if product.stock < 0:
			raise ValidationError(
				'Insufficient stock to assign to order')
		if serializer.save():
			product.save()	

	def perform_update(self, serializer):
		record = self.get_object()
		prev_quantity = record.quantity
		new_quantity = serializer.validated_data.get('quantity')

		if len(self.queryset.filter(
			order_id=record.order.id,
			product_id=record.product.id)) > 1:
			raise ValidationError(ERROS['PRODUCT_DUPLI'])

		if new_quantity == 0:
			raise ValidationError(ERROS['PRODUCT_QTY'])

		record.product.stock += prev_quantity - new_quantity

		if record.product.stock < 0:
			raise ValidationError(ERROS['PRODUCT_STOCK'])

		if serializer.save():
			record.product.save()

	def perform_destroy(self, instance):
		if instance.delete():
			instance.product.stock += instance.quantity
			instance.product.save()

