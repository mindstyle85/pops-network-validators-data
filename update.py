from networks.harmony import Harmony
import json
import time

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

while 1:
    #load the updated data 
    with open('data.json') as json_file:
        datas = json.load(json_file)

    harmony = Harmony("information", "price", "fees", "apy", "total_delegation")
    harmony_price = harmony.getprice()
    print(repr(harmony))

    datas[0]["price"] = str(harmony_price)

    allprice = cg.get_price(ids='harmony, solana, avalanche-2, the-graph, stafi ', vs_currencies='usd')
    print (allprice)
    datas[0]["price"] = str(allprice['harmony']['usd'])
    datas[1]["price"] = str(allprice['solana']['usd'])
    datas[2]["price"] = str(allprice['avalanche-2']['usd'])
    datas[3]["price"] = str(allprice['the-graph']['usd'])
    datas[4]["price"] = str(allprice['stafi']['usd'])

    with open('data.json', 'w') as outfile:
        json.dump(datas, outfile)

    time.sleep(60)