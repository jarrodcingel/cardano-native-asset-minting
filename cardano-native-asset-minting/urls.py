from django.urls import include, path
from rest_framework import routers
from server import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'addresses', views.AssetAddressViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('create-address', views.create_address, name='create-address'),
    path('reserve-address', views.reserve_address, name='reserve-address'),
    path('start-task', views.start_task, name='start-task')
]