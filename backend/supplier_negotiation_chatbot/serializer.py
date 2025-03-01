from rest_framework import serializers
from .models import (Material,Supplier,Negotiation,Conversation,ConversationDetail)

# class StudentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Students
#         fields = '__all__'

class MaterialSerializer(serializers.ModelSerializer):

    class Meta:
        model = Material
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = '__all__'

class NegotiationSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Negotiation
        fields = '__all__'
 
 
class ConversationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationDetail
        fields = ['sender', 'message', 'timestamp']
 
class ConversationSerializer(serializers.ModelSerializer):
    conversation_details = ConversationDetailSerializer(many=True, read_only=True)
 
    class Meta:
        model = Conversation
        fields = ['id', 'created_at', 'conversation_details']

# class ConversationDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ConversationDetail
#         fields = '__all__'