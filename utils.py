from dataclasses import dataclass
from typing import List
from enum import Enum

class PaymentTerm(Enum):
    NET10 = 10
    NET30 = 30
    NET60 = 60

class Incoterms(Enum):
    DDP = 1
    FOB = 2

@dataclass
class ContractOffer:
    price_per_unit:float = None
    quantity:float = None
    bundling_unit:float = None
    bundling_amount:float = None
    bundling_discount:float = None
    payment_term:PaymentTerm = PaymentTerm.NET30
    payment_term_offer:PaymentTerm = None
    payment_term_markup:float = None
    delivery_timeline:float = None
    contract_period:int = None
    contract_inflation_by_year:List[float] = None
    rebates_threshold_unit:float = None
    rebates_discount:float = None
    warranty:float = None
    incoterms:Incoterms = None

@dataclass
class ContractActual:
    price_per_unit:float = None
    quantity:float = None
    bundling_ind:bool = None
    payment_term:PaymentTerm = PaymentTerm.NET30
    delivery_timeline:float = None
    contract_period:int = None
    warranty:float = None
    incoterms:Incoterms = None

    def cost_without_offer(self,offer:ContractOffer):
        quantity = self.quantity if self.quantity != None else offer.quantity
        return offer.price_per_unit*quantity
    
    def cost_with_bundling(self,offer:ContractOffer):
        cost = self.cost_without_offer(offer)
        if offer.bundling_amount != None:
            return (cost + offer.bundling_amount)*(1-offer.bundling_discount/100)
        else:
            return cost
    
    def is_bundling_required(self,offer:ContractOffer):
        cost = self.cost_without_offer(offer)
        cost_with_bundling = self.cost_with_bundling(offer)
        return (cost_with_bundling <= cost)
    
    def min_cost_bundling(self,offer:ContractOffer):
        if self.is_bundling_required(offer) == True:
            return self.cost_with_bundling(offer)
        else:
            return self.cost_without_offer(offer)
    
    def cost_with_payment_term(self,offer:ContractOffer):
        cost = self.min_cost_bundling(offer)
        print('Cost after bundling: ',cost)
        cost_orig = (
            cost - 
            cost*(6/100)*(offer.payment_term.value/365)
        )
        cost_disc = cost_orig
        if offer.payment_term_offer != None:
            cost_disc = (
                cost*(1 + offer.payment_term_markup/100) - 
                cost*(6/100)*((offer.payment_term_offer.value - offer.payment_term.value)/365)
            )
        if cost_disc <= cost_orig:
            return (offer.payment_term_offer,cost_disc)
        else:
            return (offer.payment_term,cost_orig)
    
    def is_payment_term_required(self,offer):
        cost = self.min_cost_bundling(offer)
        cost_pt = self.cost_with_payment_term(offer)[1]
        return cost_pt <= cost
    
    def min_cost_bundling_payment_term(self,offer):
        if self.is_payment_term_required(offer) == True:
            return self.cost_with_payment_term(offer)[1]
        else:
            return self.min_cost_bundling(offer)
    
    def cost_after_rebate(self,offer):
        cost = self.min_cost_bundling_payment_term(offer)
        print('Cost after bundling and payment term',cost)
        if self.quantity != None:
            if self.quantity >= offer.rebates_threshold_unit:
                return cost*(1 - offer.rebates_discount/100)
        return cost
    
    def calculate_TCO_yearly(self,offer):
        cost = self.cost_after_rebate(offer)
        print('Cost after rebate',cost)
        tco_by_year = []
        for inflation in offer.contract_inflation_by_year:
            cost = cost*(1 + inflation/100)
            tco_by_year.append(cost)
        cost = sum(tco_by_year)/len(tco_by_year)
        return cost

    # def calculate_TCO_and_optimize_contract(self,offer:ContractOffer) -> float:
    #     if self.quantity == None:
    #         quantity = offer.quantity
    #     else:
    #         quantity = self.quantity
    #     cost = offer.price_per_unit*quantity
    #     cost_bundling = (cost + offer.bundling_amount)*(1-offer.bundling_discount/100)
    #     if cost_bundling <= cost:
    #         self.bundling_ind = True
    #         tco = cost_bundling
    #     else:
    #         self.bundling_ind = False
    #         tco = cost_bundling
    #     if offer.payment_term_offer != None:
    #         cost_pt = (
    #             tco*(1 + offer.payment_term_markup/100) - 
    #             tco*(6/100)*((offer.payment_term_offer.value - offer.payment_term.value)/365)
    #         )
    #         if cost_pt <= tco:
    #             tco = cost_pt
    #             self.payment_term = PaymentTerm.NET60
    #     if self.quantity >= offer.rebates_threshold_unit:
    #         tco = tco*(1 - offer.rebates_discount/100)
    #     tco_by_year = []
    #     for inflation in offer.contract_inflation_by_year:
    #         tco = tco*(1 + inflation/100)
    #         tco_by_year.append(tco)
    #     tco = sum(tco_by_year)/len(tco_by_year)
    #     return tco
    
    def check_delivery_timeline(self,offer:ContractOffer):
        return self.delivery_timeline <= offer.delivery_timeline
    
    def check_warranty(self,offer:ContractOffer):
        return self.warranty <= offer.warranty
    
    def check_incoterm(self,offer:ContractOffer):
        return self.incoterms == offer.incoterms