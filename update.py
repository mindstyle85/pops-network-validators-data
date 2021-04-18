from networks.harmony import Harmony
import json
import time
from pyhmy import staking
from solana.rpc.api import Client as Solana_Client

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

def atto_to_one(attonumber):
    return int(attonumber / (10 ** 18))

def solana_nb_converter(number):
    return int(number / (10 ** 9))

Solana_http_client = Solana_Client("https://api.mainnet-beta.solana.com")

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
        datas[0]['Validators'][0]['Delegation'] = f"{atto_to_one(hmy_validator['total-delegation'])} ONE"

    #########################################################################
    ###################### updating solana related data#####################
    
    all_vote_acccount = Solana_http_client.get_vote_accounts()["result"]["current"]

    total_delegation = 0
    total_apy = 0
    total_commission = 0
    total_validator = 0
    for validator in datas[1]['Validators']:
        val = [vote_acccount for vote_acccount in all_vote_acccount if vote_acccount['votePubkey'] == validator['Address']][0]
        total_delegation += val['activatedStake']
        validator['Delegation'] = f"{solana_nb_converter(val['activatedStake'])} SOL"
        total_commission += val['commission']
        total_validator += 1

    datas[1]['Total_delegation'] = f"{solana_nb_converter(total_delegation)} SOL"
    datas[1]['Fees'] = total_commission / total_validator
    # missing APY collection for now leaving it as static data

    with open('data.json', 'w') as outfile:
        json.dump(datas, outfile)

    time.sleep(60)