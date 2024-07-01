from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title']

class MenuItemSerializer (serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category =  CategorySerializer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','title', 'price', 'featured', 'category', 'category_id']

class CartSerializer (serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField( 
    queryset=User.objects.all(), 
    default=serializers.CurrentUserDefault() 
    ) 
    menuitem_id = serializers.IntegerField(write_only=True)
    menuitem =  MenuItemSerializer(read_only=True)
    class Meta:
        model = Cart
        fields = ['id','user', 'quantity', 'unit_price', 'price', 'menuitem', 'menuitem_id']


class OrderItemSerializer (serializers.ModelSerializer):
    menuitem_id = serializers.IntegerField(write_only=True)
    menuitem =  MenuItemSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']

class OrderSerializer (serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField( 
    queryset=User.objects.all(), 
    default=serializers.CurrentUserDefault() 
    ) 
    orderitem = OrderItemSerializer(many=True, read_only=True, source="orderitem_set")
    class Meta:
        model = Order
        fields = ['id','user', 'delivery_crew', 'status', 'total', 'date', 'orderitem']