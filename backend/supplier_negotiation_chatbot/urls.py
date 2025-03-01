# from django.urls import path
# from .views import get_student

# urlpatterns = [
#     path('students/',get_student,name = 'get_student'),
# ]
from rest_framework import routers,urlpatterns
from .views import ConversationDetailViewSet
from rest_framework.routers import DefaultRouter
from django.urls import path
from django.urls.conf import include
 
router=DefaultRouter(trailing_slash=False)
 
router.register("conversation",ConversationDetailViewSet,'conversation') 
 
urlpatterns = [
    path("",include(router.urls))
]