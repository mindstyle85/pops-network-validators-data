from marshmallow import post_load
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

#from .transaction import Transaction, TransactionSchema
from .network_list import NetworkList
from .networks import Networks

class Harmony(Networks):
    def __init__(self, information, price, fees, apy, total_delegation):
        super(Harmony, self).__init__(NetworkList.HARMONY, information, price, fees, apy, total_delegation)

    def __repr__(self):
        return '<Harmony(ID={self.ID}, name={self.name}, information={self.information}, price={self.price}, fees={self.fees}, apy={self.apy}, total_delegation={self.total_delegation})>'.format(self=self)

    def getprice(self):
        Harmony.price = cg.get_price(ids='harmony', vs_currencies='usd')
        print (Harmony.price)
        self.price = Harmony.price['harmony']['usd']
        return self.price


# class HarmonySchema(NetworkSchema):
#     @post_load
#     def make_income(self, data):
#         return Harmony(**data)