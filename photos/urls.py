from django.urls import path
from . import views

app_name = 'photo'
urlpatterns = [
    path('login/', views.login, name="login"),
    path('accounts/login/', views.login),
    path('logout/', views.logout, name="logout"),
    path('register/', views.register, name="register"),

    path('', views.gallery, name='gallery'),
    path('photo/view/<pk>/', views.view_photo, name='view'),
    path('photo/add/', views.add_photo, name='add'),
    path('photo/update/<pk>/', views.update_photo, name='set_public'),
    path('photo/delete/<pk>/', views.delete_photo, name='del_photo'),
    # # path('del/category/<pk>', views.del_category, name='del_category'),
]
