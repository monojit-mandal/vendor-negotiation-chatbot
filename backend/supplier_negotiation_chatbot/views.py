from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import (Material,Supplier,Negotiation,Conversation,ConversationDetail)
from .serializer import ConversationDetailSerializer
from rest_framework import viewsets
from rest_framework.decorators import action

# @api_view(['GET'])
# def get_student(request):
#     return Response(
#         StudentSerializer(
#             {
#                 'first_name':'Monojit',
#                 'last_name':'Mandal',
#                 'address': 'Kolkata',
#                 'roll_number': 23,
#                 'mobile': 1111111
#             }
#         ).data
#     )
# class StudentViewSet(viewsets.ModelViewSet):
#     """
#     A ViewSet for viewing and editing student instances.
#     """
#     queryset = Students.objects.all()
#     serializer_class = StudentSerializer

#     @action(detail=False, methods=['get'])
#     def filter_by_name_m(self, request, *args, **kwargs):
#         """
#         Custom action to filter students whose names start with 'M'.
#         """
#         filtered_students = self.queryset.filter(first_name__startswith='S')
#         serializer = self.get_serializer(filtered_students, many=True)
#         return Response(serializer.data)

class ConversationDetailViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing student instances.
    """
    queryset = ConversationDetail.objects.all()
    serializer_class = ConversationDetail