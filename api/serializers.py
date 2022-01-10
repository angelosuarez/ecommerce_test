from rest_framework import serializers
from .models import Product, Order, OrderDetail
# i dont known if HyperlinkedModelSerializer is required, bur write here to memorize

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')


class OrderDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderDetail
        fields = ('id', 'quantity', 'product', 'order')

    """
    def create(self, request, *args, **kwargs):
        import pdb; pdb.set_trace()
    """


class OrderSerializer(serializers.ModelSerializer):

    order_details = OrderDetailSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order
        fields = ('id', 'date_time', 'order_details', 'get_total', 'get_total_usd')