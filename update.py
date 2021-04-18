from networks.harmony import Harmony
import json
import time
from pyhmy import staking

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

def atto_to_one(attonumber):
    return int(attonumber / (10 ** 18))

while 1:
    #load the updated data 
    with open('data.json') as json_file:
        datas = json.load(json_file)

    # updating price from coingecko API
    allprice = cg.get_price(ids='harmony, solana, avalanche-2, the-graph, stafi', vs_currencies='usd')
    print (allprice)
    datas[0]["price"] = str(allprice['harmony']['usd'])
    datas[1]["price"] = str(allprice['solana']['usd'])
    datas[2]["price"] = str(allprice['avalanche-2']['usd'])
    datas[3]["price"] = str(allprice['the-graph']['usd'])
    datas[4]["price"] = str(allprice['stafi']['usd'])

    #########################################################################
    ###################### updating harmony related data#####################
    hmy_validator = staking.get_validator_information("one1kf42rl6yg2avkjsu34ch2jn8yjs64ycn4n9wdj", "https://api.s0.t.hmny.io")
    if hmy_validator['epos-status'] == "currently elected":
        # fees/rate update
        datas[0]['Fees'] = f"{float('%.2f' % float(hmy_validator['validator']['rate']))*100}"
        datas[0]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(hmy_validator['validator']['rate']))*100}"

        # update APY
        datas[0]['APY'] = '%.2f' % (float(hmy_validator['lifetime']['apr']) * 100)

        # name update 
        datas[0]['Validators'][0]['Name'] = hmy_validator['validator']['name']

        #total delegation update
        datas[0]['Total_delegation'] = f"{atto_to_one(hmy_validator['total-delegation'])} ONE"
        datas[0]['Validators'][0]['"Delegation'] = f"{atto_to_one(hmy_validator['total-delegation'])} ONE"

    with open('data.json', 'w') as outfile:
        json.dump(datas, outfile)

    time.sleep(60)