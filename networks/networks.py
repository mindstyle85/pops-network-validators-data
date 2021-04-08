from marshmallow import Schema, fields
import datetime as dt

class Networks():
    'Common Class for all networks'

    networkCount = 0

    def __init__(self, name, information, price, fees, apy, total_delegation):
        self.ID = Networks.networkCount + 1
        self.name = name
        self.information = information
        self.price = price
        self.fees = fees
        self.apy = apy
        self.total_delegation = total_delegation
        self.created_at = dt.datetime.now()

        Networks.networkCount += 1

    def getnetworkCount(self):
        return Networks.networkCount

    def __repr__(self):
        return '<Networks(ID={self.ID}, name={self.name}, information={self.information}, price={self.price}, fees={self.fees}, apy={self.apy}, total_delegation={self.total_delegation})>'.format(self=self)

    def setPrice(self, price):
        Networks.price = price


# class NetworkSchema(Schema):
#     ID = fields.Str()
#     name = fields.Str()
#     information = fields.Str()
#     price = fields.Str()
#     fees = fields.Str()
#     apy = fields.Str()
#     total_delegation = fields.Str()