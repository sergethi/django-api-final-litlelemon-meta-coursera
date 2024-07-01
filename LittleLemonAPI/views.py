from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, UserSerializer
from .permissions import IsManager, IsDelivery_crew
from django.contrib.auth.models import User, Group
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

# Create your views here.

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if(self.request.method == 'GET'):
            return []
        return [IsAuthenticated(), IsManager()]

# Menu Items GET, POST
class MenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'category']
    filterset_fields = ['price', 'category']
    search_fields = ['title']

    def get_permissions(self):
        if(self.request.method == 'GET'):
            return []
        return [IsAuthenticated(), IsManager()]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if(self.request.method == 'GET'):
            return []
        return [IsAuthenticated(), IsManager()]

# Manager Group GET ADD DELETE
class ManagersView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, *args, **kwargs):
        managers_group = Group.objects.get(name="Manager")
        managers = managers_group.user_set.all()
        serializer = UserSerializer(managers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({"message": "username is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, username=username)
        managers_group = Group.objects.get(name="Manager")
        managers_group.user_set.add(user)
        return Response({"message": "User added to managers group"}, status=status.HTTP_200_OK)


class RemoveManagerView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        managers_group = Group.objects.get(name="Manager")
        managers_group.user_set.remove(user)
        return Response({"message": "User removed from managers group"}, status=status.HTTP_200_OK)

# Delivery Crew Group GET, ADD, DELETE
class DeliveryCrewView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, *args, **kwargs):
        delivery_crew_group = Group.objects.get(name="Delivery crew")
        delivery_crew = delivery_crew_group.user_set.all()
        serializer = UserSerializer(delivery_crew, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({"message": "username is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, username=username)
        delivery_crew_group = Group.objects.get(name="Delivery crew")
        delivery_crew_group.user_set.add(user)
        return Response({"message": "User added to delivery_crew group"}, status=status.HTTP_200_OK)

class RemoveDeliveryCrewView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        delivery_crew_group = Group.objects.get(name="Delivery crew")
        delivery_crew_group.user_set.remove(user)
        return Response({"message": "User removed from delivery_crew group"}, status=status.HTTP_200_OK)

# Cart Management GET, POST, DELETE
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
    
        queryset = Cart.objects.all()
        user = request.user
        if not user.is_anonymous:
            queryset = Cart.objects.filter(user=user)
        serializer_class = CartSerializer(queryset, many=True)
        return Response(serializer_class.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        
        user = request.user
        menu_item_id = request.data.get('menu_item_id')
        
        if not menu_item_id:
            return Response({"message": "menu_item_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        cart_data = {
            'user': user.id,
            'menuitem_id': menu_item.id,
            'quantity': request.data.get('quantity', 1),
            'unit_price': menu_item.price,
            'price': menu_item.price,
        }
        serializer = CartSerializer(data=cart_data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Menu item added to cart", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        user = request.user
        Cart.objects.filter(user=user).delete()
        return Response({"message": "All menu items removed from cart"}, status=status.HTTP_200_OK)

# Order management
class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
    
        user = request.user

        if IsManager().has_permission(request, self):
            queryset = Order.objects.all().prefetch_related('orderitem_set__menuitem')
        elif IsDelivery_crew().has_permission(request, self):
            queryset = Order.objects.filter(delivery_crew=user).prefetch_related('orderitem_set__menuitem')
        else:
            queryset = Order.objects.filter(user=user).prefetch_related('orderitem_set__menuitem')

        serializer_class = OrderSerializer(queryset, many=True)
        return Response(serializer_class.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        
        user = request.user
        current_cart_items = Cart.objects.filter(user=user)
        
        if not current_cart_items:
            return Response({"message": "cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user, total = 0, status = 0)
        order_items = []
        total_price = 0
        for cart_item in current_cart_items:

            try:
                order_item = OrderItem.objects.get(order=order, menuitem=cart_item.menuitem)
                order_item.quantity += cart_item.quantity
                order_item.price += cart_item.quantity * cart_item.menuitem.price
                order_item.save()
            except OrderItem.DoesNotExist:
                order_item = OrderItem(
                    order=order,
                    menuitem=cart_item.menuitem,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.menuitem.price,
                    price=cart_item.quantity * cart_item.menuitem.price
                )
            order_items.append(order_item)
            total_price += order_item.price

        # Save all order items
        OrderItem.objects.bulk_create(order_items)

        # Update order total
        order.total = total_price
        order.save()

        # Clear the user's cart
        current_cart_items.delete()

        order_serializer = OrderSerializer(order)
        return Response({"message": "Order created", "data": order_serializer.data}, status=status.HTTP_201_CREATED)

# Single Order management
class SingleOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
    
        user = request.user
        if IsManager().has_permission(request, self):
            order = get_object_or_404(Order, id=pk)
        elif IsDelivery_crew().has_permission(request, self):
            order = get_object_or_404(Order, id=pk, delivery_crew =user)
        else:
            order = get_object_or_404(Order, id=pk, user=user)
        serializer_class = OrderSerializer(order)
        return Response(serializer_class.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        user = request.user
        if IsManager().has_permission(request, self):
            order = get_object_or_404(Order, id=pk)
            serializer = OrderSerializer(order, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Order updated", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def patch(self, request, pk, *args, **kwargs):
        user = request.user
        if IsManager().has_permission(request, self):
            order = get_object_or_404(Order, id=pk)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Order partially updated", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if IsDelivery_crew().has_permission(request, self):
            order = get_object_or_404(Order, id=pk)
            order_status = request.data.get("status")
            if order_status is not None:
                serializer = OrderSerializer(order, data={"status": order_status}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Order status partially updated", "data": serializer.data}, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "status field is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk, *args, **kwargs):
        user = request.user
        if IsManager().has_permission(request, self):
            order = get_object_or_404(Order, id=pk)
            order.delete()
            return Response({"message": "Order deleted"}, status=status.HTTP_200_OK)
        return Response({"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)






