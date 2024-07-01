from rest_framework import permissions

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is a manager
        return request.user.groups.filter(name='Manager').exists()

class IsDelivery_crew(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is part of the Delivery crew group
        return request.user.groups.filter(name='Delivery crew').exists()
