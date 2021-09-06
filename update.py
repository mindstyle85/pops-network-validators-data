from networks.harmony import Harmony
import json
import time
from datetime import datetime
import requests
from requests.exceptions import HTTPError
from pyhmy import staking
from solana.rpc.api import Client as Solana_Client

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

def atto_to_one(attonumber):
    return int(attonumber / (10 ** 18))

def solana_nb_converter(number):
    return int(number / (10 ** 9))

def http_json_call(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
    except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
    else:
        content = json.loads(r.content)
        return content

Solana_http_client = Solana_Client("https://api.mainnet-beta.solana.com")

while 1:
    #load the updated data 
    now = datetime.now()
    try:
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

        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        
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

        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        #########################################################################
        ###################### updating solana related data#####################
        
        all_vote_account = Solana_http_client.get_vote_accounts()["result"]["current"]

        total_delegation = 0
        total_apy = 0
        total_commission = 0
        total_pops_validator = 0
        for pops_validator in datas[1]['Validators']:
            val = [vote_account for vote_account in all_vote_acccount if vote_account['votePubkey'] == pops_validator['Address']][0]
            total_delegation += val['activatedStake']
            pops_validator['Delegation'] = f"{solana_nb_converter(val['activatedStake'])} SOL"
            total_commission += val['commission']
            total_pops_validator += 1

        datas[1]['Total_delegation'] = f"{solana_nb_converter(total_delegation)} SOL"
        datas[1]['Fees'] = total_commission / total_pops_validator
        # missing APY collection for now leaving it as static data
        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)

        #########################################################################
        ###################### updating avax related data#######################
        # Global APY : https://avascan.info/api/v1/statistics
        # validator information : https://avascan.info/api/v1/validators?limit=2000 for fee and total AVAX
        total_delegation = 0
        total_apy = 0
        total_commission = 0
        total_pops_validator = 0

        avax_stats = http_json_call("https://avascan.info/api/v1/statistics")
        #print (avax_stats)
        total_apy = avax_stats['stakingReward']
        all_network_validator = avax_stats['totalValidator']

        all_validator_account = http_json_call(f"https://avascan.info/api/v1/validators?limit={all_network_validator}")
        for pops_validator in datas[2]['Validators']:
            val = [validator for validator in all_validator_account if validator['id'] == pops_validator['Address']][0]
            total_delegation += val['activatedStake']
            pops_validator['Delegation'] = f"{solana_nb_converter(val['activatedStake'])} SOL"
            total_commission += val['commission']
            total_pops_validator += 1
        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        ###########################################################################
        ###################### updating the graph related data#####################
        # get the name : curl -X GET https://api.oracleminer.com/graph/ens/0x1a99dd7d916117a523f3ce6510dcfd6bceab11e7
        # get indexer info : curl -X GET https://api.oracleminer.com/graph/indexer/0x1a99dd7d916117a523f3ce6510dcfd6bceab11e7

        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
    except:
        nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
        print(f"{nowstring} : An exception occurred, but let's continue and wait for the next 1 min call")
    time.sleep(60)