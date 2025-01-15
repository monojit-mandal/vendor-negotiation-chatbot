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