# from django.db import models
# from .utils import print_hello

# # Create your models here.
# class Students(models.Model):  
#     first_name = models.CharField(max_length=200)  
#     last_name = models.CharField(max_length=200)  
#     address = models.CharField(max_length=200)  
#     roll_number = models.IntegerField()  
#     mobile = models.CharField(max_length=10)  
  
#     def __str__(self):
#         return self.first_name + " " + self.last_name
    
#     def save(self, *args, **kwargs):
#         # Print "hello" when saving the model
#         # print("hello")
#         print_hello()
#         super().save(*args, **kwargs) 

from django.db import models
# from .utils import print_hello

# # Material table with various negotiation levers
# class Material(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField(blank=True, null=True)

#     unit = models.CharField(max_length=50, blank=True, null=True)  # e.g. kg, box, etc.
 
#     # Base levers for negotiation
#     base_price = models.DecimalField(
#         max_digits=10, decimal_places=2, default=0)  # Base price for material
#     available_quantity = models.DecimalField(
#         max_digits=10, decimal_places=2, default=0)  # Base available quantity
 
#     # Additional levers
#     incoterms_choices = [
#         ('EXW', 'EXW'),
#         ('FCA', 'FCA'),
#         ('FAS', 'FAS'),
#         ('FOB', 'FOB'),
#         ('CFR', 'CFR'),
#         ('CIF', 'CIF'),
#         ('CPT', 'CPT'),
#         ('CIP', 'CIP'),
#         ('DAP', 'DAP'),
#         ('DPU', 'DPU'),
#         ('DDP', 'DDP'),
#     ]
#     incoterms = models.CharField(
#         max_length=10, choices=incoterms_choices, default='EXW')
 
#     payment_terms_choices = [
#         ('30_days', '30 days'),
#         ('60_days', '60 days'),
#         ('90_days', '90 days'),
#         ('L/C', 'Letter of Credit'),
#     ]
#     payment_terms = models.CharField(
#         max_length=10, choices=payment_terms_choices, default='30_days')
 
#     delivery_time_choices = [
#         ('1_week', '1 week'),
#         ('2_weeks', '2 weeks'),
#         ('1_month', '1 month'),
#         ('2_months', '2 months'),
#     ]
#     delivery_time = models.CharField(
#         max_length=10, choices=delivery_time_choices, default='2_weeks')
 
#     discount_percentage = models.DecimalField(
#         max_digits=5, decimal_places=2, default=0)  # Discount on price
 
#     shipping_cost_choices = [
#         ('buyer', 'Buyer'),
#         ('supplier', 'Supplier'),
#         ('shared', 'Shared'),
#     ]
#     shipping_cost = models.CharField(
#         max_length=10, choices=shipping_cost_choices, default='buyer')
 
#     warranty_terms = models.TextField(blank=True, null=True)  # Warranty terms (e.g., "1-year warranty")
#     return_policy = models.TextField(blank=True, null=True)  # Return policy
#     quality_specifications = models.TextField(blank=True, null=True)  # Quality specifications or standards
#     volume_discount_threshold = models.DecimalField(
#         max_digits=10, decimal_places=2, default=0)  # Volume discount threshold
#     volume_discount_percentage = models.DecimalField(
#         max_digits=5, decimal_places=2, default=0)  # Volume discount percentage
#     taxes_and_customs = models.TextField(blank=True, null=True)  # Who bears responsibility for taxes and customs
 
#     after_sales_support = models.TextField(blank=True, null=True)  # After-sales support conditions
 
#     def __str__(self):
#         return self.name
 
 
# # Supplier table
# class Supplier(models.Model):
#     name = models.CharField(max_length=200)
#     contact_info = models.TextField(blank=True, null=True)
#     address = models.TextField(blank=True, null=True)
#     email = models.EmailField(blank=True, null=True)
#     material = models.ForeignKey(Material, on_delete=models.CASCADE)
 
#     def __str__(self):
#         return self.name
   
# # Negotiation table (when negotiation starts for a material-supplier pair)
# class Negotiation(models.Model):
#     supplier = models.CharField(max_length=50,blank=True, null=True)
#     material=models.CharField(max_length=50,blank=True, null=True)
#     start_date = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(
#         max_length=50, 
#         choices=[
#             ('pending', 'Pending'), 
#             ('active', 'Active'), 
#             ('closed', 'Closed')
#         ], 
#         default='pending'
#     )
#     negotiated_price = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2, 
#         blank=True, 
#         null=True)
#     negotiated_quantity = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2, 
#         blank=True, 
#         null=True
#     )
#     negotiated_bundling_quantity_discount_threshold = models.DecimalField(
#         max_digits=10, decimal_places=2, blank=True, null=True)
#     negotiated_bundling_price_discount_threshold = models.DecimalField(
#         max_digits=10, decimal_places=2, blank=True, null=True)
#     negotiated_bundling_discount_percentage = models.DecimalField(
#         max_digits=5, decimal_places=2, blank=True, null=True)
#     negotiated_payment_terms = models.CharField(
#         max_length=10, 
#         choices=Material.payment_terms_choices, 
#         blank=True, 
#         null=True
#     )
#     negotiated_delivery_time = models.CharField(
#         max_length=10, 
#         choices=Material.delivery_time_choices, 
#         blank=True, 
#         null=True
#     )
#     negotiated_contract_length = models.DecimalField(
#         max_digits=2,decimal_places=0,blank=True,null = True)
#     negotiated_contract_inflation = models.DecimalField(
#         max_digits=2,decimal_places=0,blank=True,null = True)
#     # negotiated_warranty_terms = models.TextField(blank=True, null=True)
#     negotiated_rebate_threshold = models.DecimalField(
#         max_digits=10,decimal_places=2,blank=True,null=True
#     )
#     negotiated_rebate_discount = models.DecimalField(
#         max_digits=2,decimal_places=0,blank=True,null=True
#     )
#     negotiated_warranty_period = models.DecimalField(
#         max_digits=2,decimal_places=0,blank=True,null=True
#     )
#     negotiated_incoterms = models.CharField(
#         max_length=10, 
#         choices=Material.incoterms_choices, 
#         blank=True, 
#         null=True
#     )
 
#     def __str__(self):
#         return f'Negotiation with {self.supplier_material.supplier.name} for {self.supplier_material.material.name}'
 
 
# # Conversation table (stores the negotiation's conversation)
# class Conversation(models.Model):
#     negotiation = models.OneToOneField(Negotiation, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
 
#     def __str__(self):
#         return f'Conversation for negotiation {self.negotiation.id}'
 
 
# # ConversationDetail table (stores individual messages in the conversation)
# class ConversationDetail(models.Model):
#     conversation = models.ForeignKey(
#         Conversation, 
#         related_name="conversation_details", 
#         on_delete=models.CASCADE
#     )
#     sender = models.CharField(max_length=200)  # Can be "buyer" or "supplier"
#     message = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)
 
#     def __str__(self):
#         return f'Message from {self.sender} at {self.timestamp}'
    
#     def save(self, *args, **kwargs):
#         super().save(*args, **kwargs) 

# Material table with various negotiation levers
class Material(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50, blank=True, null=True)  # e.g. kg, box, etc.
 
    # Base levers for negotiation
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Base price for material
    available_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Base available quantity
 
    # Additional levers
    incoterms_choices = [
        ('EXW', 'EXW'),
        ('FOB', 'FOB'),
        ('CIF', 'CIF'),
        ('CFR', 'CFR'),
    ]
    incoterms = models.CharField(max_length=10, choices=incoterms_choices, default='EXW')
 
    payment_terms_choices = [
        ('30_days', '30 days'),
        ('60_days', '60 days'),
        ('90_days', '90 days'),
        ('L/C', 'Letter of Credit'),
    ]
    payment_terms = models.CharField(max_length=10, choices=payment_terms_choices, default='30_days')
 
    delivery_time_choices = [
        ('1_week', '1 week'),
        ('2_weeks', '2 weeks'),
        ('1_month', '1 month'),
        ('2_months', '2 months'),
    ]
    delivery_time = models.CharField(max_length=10, choices=delivery_time_choices, default='2_weeks')
 
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Discount on price
 
    shipping_cost_choices = [
        ('buyer', 'Buyer'),
        ('supplier', 'Supplier'),
        ('shared', 'Shared'),
    ]
    shipping_cost = models.CharField(max_length=10, choices=shipping_cost_choices, default='buyer')
 
    warranty_terms = models.TextField(blank=True, null=True)  # Warranty terms (e.g., "1-year warranty")
    return_policy = models.TextField(blank=True, null=True)  # Return policy
    quality_specifications = models.TextField(blank=True, null=True)  # Quality specifications or standards
    volume_discount_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Volume discount threshold
    volume_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Volume discount percentage
    taxes_and_customs = models.TextField(blank=True, null=True)  # Who bears responsibility for taxes and customs
 
    after_sales_support = models.TextField(blank=True, null=True)  # After-sales support conditions
 
    def __str__(self):
        return self.name
 
 
# Supplier table
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_info = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
 
    def __str__(self):
        return self.name
   
# Negotiation table (when negotiation starts for a material-supplier pair)
class Negotiation(models.Model):
    supplier = models.CharField(max_length=50,blank=True, null=True)
    material=models.CharField(max_length=50,blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('active', 'Active'), ('closed', 'Closed')], default='pending')
    terms = models.TextField(blank=True, null=True)
 
    # Negotiation-specific values for each lever
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    negotiated_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    negotiated_payment_terms = models.CharField(max_length=10, choices=Material.payment_terms_choices, blank=True, null=True)
    negotiated_incoterms = models.CharField(max_length=10, choices=Material.incoterms_choices, blank=True, null=True)
    negotiated_delivery_time = models.CharField(max_length=10, choices=Material.delivery_time_choices, blank=True, null=True)
    negotiated_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    negotiated_shipping_cost = models.CharField(max_length=10, choices=Material.shipping_cost_choices, blank=True, null=True)
    negotiated_warranty_terms = models.TextField(blank=True, null=True)
    negotiated_return_policy = models.TextField(blank=True, null=True)
    negotiated_quality_specifications = models.TextField(blank=True, null=True)
    negotiated_volume_discount_threshold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    negotiated_volume_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    negotiated_taxes_and_customs = models.TextField(blank=True, null=True)
    negotiated_after_sales_support = models.TextField(blank=True, null=True)
 
    def __str__(self):
        return f'Negotiation with {self.supplier_material.supplier.name} for {self.supplier_material.material.name}'
 
 
# Conversation table (stores the negotiation's conversation)
class Conversation(models.Model):
    negotiation = models.OneToOneField(Negotiation, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f'Conversation for negotiation {self.negotiation.id}'
 
 
# ConversationDetail table (stores individual messages in the conversation)
class ConversationDetail(models.Model):
    conversation = models.ForeignKey(Conversation, related_name="conversation_details", on_delete=models.CASCADE)
    sender = models.CharField(max_length=200)  # Can be "buyer" or "supplier"
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f'Message from {self.sender} at {self.timestamp}'