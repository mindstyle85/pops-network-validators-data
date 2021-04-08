from networks.harmony import Harmony
import json

#load the updated data 
with open('data.json') as json_file:
    datas = json.load(json_file)

harmony = Harmony("information", "price", "fees", "apy", "total_delegation")
harmony_price = harmony.getprice()
print(repr(harmony))

datas[0]["price"] = str(harmony_price)

with open('data-changed.json', 'w') as outfile:
    json.dump(datas, outfile)