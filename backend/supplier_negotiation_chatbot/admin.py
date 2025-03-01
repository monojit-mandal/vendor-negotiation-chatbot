from django.contrib import admin
from .models import (Material,Supplier,Negotiation,Conversation,ConversationDetail) 
  
# Register your models here.
admin.site.register(Material)  
admin.site.register(Supplier)  
admin.site.register(Negotiation)  
admin.site.register(Conversation)  
admin.site.register(ConversationDetail)