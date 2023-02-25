from networks.harmony import Harmony
import json
import time
from datetime import datetime
import requests
from requests.exceptions import HTTPError
from pyhmy import staking
from solana.rpc.api import Client as Solana_Client
from typing import Any

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

def is_float(element: Any) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False

def atto_to_one(attonumber):
    return int(attonumber / (10 ** 18))

def solana_nb_converter(number):
    return int(number / (10 ** 9))

def uumee_to_umee(uumee):
    return int(uumee / (10 ** 6))

def uaxl_to_axl(uaxl):
    return int(uaxl / (10 ** 6))

def ubld_to_bld(ubld):
    return int(ubld / (10 ** 6))

def uakt_to_akt(uakt):
    return int(uakt / (10 ** 6))

def micro_to_none(unumber):
    return int(unumber / (10 ** 6))

def atto_to_cqt(atto):
    return int(atto / (10 ** 18))

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

def get_price_from_mexc(ticker1, ticker2):
    #Price from MEXC
    mrkt_url = 'https://www.mexc.com/open/api/v2/market/ticker'
    url      =  f"{mrkt_url}?symbol={ticker1}_{ticker2}"
    ticker_info = http_json_call(url)
    return ticker_info["data"][0]["last"]

def create_stakingreward_assets(network_name, slug_name, balanceTokenTotal,balanceUsdTotal,usersTotal,feeTotal,address):
    # update staking-reward data
    print(f"adding staking reward data for {network_name}")
    json_data={
        "name":network_name,
        "slug":slug_name,
        "balanceTokenTotal":balanceTokenTotal,
        "balanceUsdTotal":balanceUsdTotal,
        "usersTotal":usersTotal,
        "feeTotal":feeTotal,
        "nodes":[
            {
                "address":address,
                "fee":feeTotal,
                "slashes":[],
                "users":usersTotal,
                "balanceUsd":balanceUsdTotal,
                "balanceToken":balanceTokenTotal,
            }
        ]}
    return json_data

def create_stakingreward_node(valaddress, valfee, users, tokenamount, tokenprice):
    node={
        "address":valaddress,
        "fee":valfee,
        "slashes":[],
        "users":users,
        "balanceUsd":tokenamount * tokenprice,
        "balanceToken":tokenamount
    }
    return node
    
def create_avax_stakingreward_assets(datas):
    nodes=[]
    total_delegation=0

    test=datas["networks"][2]['Validators']

    for pops_validator in datas["networks"][2]['Validators']:
        address=pops_validator["Address"]
        fee=pops_validator["Fees"]
        user=pops_validator["delegators"]
        delegation = float(pops_validator["Delegation"][:len(pops_validator["Delegation"]) - 5])
        total_delegation += delegation

        nodes.append(create_stakingreward_node(address, fee, user,
                                            delegation,float(datas["networks"][2]["price"])))


    # update staking-reward data
    print(f"adding staking reward data for AVAX")
    json_data={
        "name":"Avalanche",
        "slug":"avalanche",
        "balanceTokenTotal": total_delegation,
        "balanceUsdTotal": total_delegation * float(datas["networks"][2]["price"]),
        "usersTotal":datas["networks"][2]["delegators"],
        "feeTotal":datas["networks"][2]['Fees'],
        "nodes":nodes
        }
    return json_data

def create_solana_stakingreward_assets(all_vote_account, datas):
    total_delegation = 0
    total_commission = 0
    total_pops_validator = 0
    total_users = 0

    #manual entry of the number of delegators for now
    sol_delegators=[138,146,97,104]

    nodes=[]

    for pops_validator in datas["networks"][1]['Validators']:
        val = [vote_account for vote_account in all_vote_account if vote_account['votePubkey'] == pops_validator['Address']]
        #print(val)
        if len(val) > 0:
            val = val[0]
            total_delegation += val['activatedStake']
            total_commission += val['commission']
            total_users += sol_delegators[total_pops_validator]
            node={
                    "address":pops_validator['Address'],
                    "fee":val['commission'],
                    "slashes":[],
                    "users":sol_delegators[total_pops_validator],
                    "balanceUsd":solana_nb_converter(val['activatedStake']) * float(datas["networks"][1]["price"]),
                    "balanceToken":solana_nb_converter(val['activatedStake'])
                }
            nodes.append(node)
            total_pops_validator += 1

    datas["networks"][1]['Total_delegation'] = f"{solana_nb_converter(total_delegation)} SOL"
    datas["networks"][1]['Fees'] = total_commission / total_pops_validator
    datas["networks"][1]['delegators'] = total_users
    # update staking-reward data
    print(f"adding staking reward data for Solana")
    json_data={
        "name":"Solana",
        "slug":"solana",
        "balanceTokenTotal":solana_nb_converter(total_delegation),
        "balanceUsdTotal":solana_nb_converter(total_delegation) * float(datas["networks"][1]["price"]),
        "usersTotal":total_users,
        "feeTotal":datas["networks"][1]['Fees'],
        "nodes":nodes
        }
    return json_data


Solana_http_client = Solana_Client("https://api.mainnet-beta.solana.com")

while 1:
    #load the updated data 
    now = datetime.now()
    try:
        with open('data.json') as json_file:
            datas = json.load(json_file)

        # for staking reward
        staking_data={}
        staking_data["name"] = "P-OPS Team"
        staking_data["users"] = 0
        staking_data["supportedAssets"] = []

        # updating price from coingecko API
        allprice = cg.get_price(ids='harmony, solana, avalanche-2, the-graph, stafi, akash-network, umee, covalent, agoric, axelar, point-network, forta, arable-protocol, aleph-zero', vs_currencies='usd')
        print (allprice)
        datas["networks"][0]["price"] = str(allprice['harmony']['usd'])
        datas["networks"][1]["price"] = str(allprice['solana']['usd'])
        datas["networks"][2]["price"] = str(allprice['avalanche-2']['usd'])
        datas["networks"][3]["price"] = str(allprice['the-graph']['usd'])
        datas["networks"][4]["price"] = str(allprice['stafi']['usd'])
        datas["networks"][5]["price"] = str(allprice['akash-network']['usd'])
        datas["networks"][6]["price"] = str(allprice['agoric']['usd'])
        datas["networks"][7]["price"] = str(allprice['axelar']['usd'])
        datas["networks"][8]["price"] = str(allprice['umee']['usd'])
        datas["networks"][9]["price"] = str(allprice['covalent']['usd'])
        #datas["networks"][10]["price"] = str(get_price_from_mexc('POINT','USDT'))
        datas["networks"][10]["price"] = str(allprice['point-network']['usd'])
        datas["networks"][11]["price"] = str(allprice['forta']['usd'])
        datas["networks"][12]["price"] = str(allprice['arable-protocol']['usd'])
        datas["networks"][13]["price"] = str(allprice['aleph-zero']['usd'])
        datas["networks"][14]["price"] = 0

        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        
        #########################################################################
        ###################### updating harmony related data#####################
        try:
            hmy_validator = staking.get_validator_information("one1kf42rl6yg2avkjsu34ch2jn8yjs64ycn4n9wdj", "https://api.s0.t.hmny.io")
            if hmy_validator['epos-status'] == "currently elected":
                # fees/rate update
                datas["networks"][0]['Fees'] = f"{float('%.2f' % float(hmy_validator['validator']['rate']))*100}"
                datas["networks"][0]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(hmy_validator['validator']['rate']))*100}"

                # number of delegators
                datas["networks"][0]['delegators'] = len(hmy_validator['validator']['delegations'])

                # update APY
                datas["networks"][0]['APY'] = '%.2f' % (float(hmy_validator['lifetime']['apr']) * 100)

                # name update 
                datas["networks"][0]['Validators'][0]['Name'] = hmy_validator['validator']['name']

                #total delegation update
                datas["networks"][0]['Total_delegation'] = f"{atto_to_one(hmy_validator['total-delegation'])} ONE"
                datas["networks"][0]['Validators'][0]['Delegation'] = f"{atto_to_one(hmy_validator['total-delegation'])} ONE"

                # Update $$$
                datas["networks"][0]["balanceUsdTotal"] = atto_to_one(hmy_validator['total-delegation']) * float(datas["networks"][0]["price"])

                # create staking reward assets
                json_asset=create_stakingreward_assets("Harmony", "harmony", atto_to_one(hmy_validator['total-delegation']),
                                datas["networks"][0]["balanceUsdTotal"],datas["networks"][0]['delegators'],float(datas["networks"][0]['Fees']) / 100,
                                "one1kf42rl6yg2avkjsu34ch2jn8yjs64ycn4n9wdj")
                staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Harmony data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update harmony data")
            print(e)

        ###########################################################################
        ###################### updating umee data #####################
        try:
            # update delegator numbers
            validator_delegations = http_json_call("http://val01.umee.m.pops.one:1317/cosmos/staking/v1beta1/validators/umeevaloper14w3wm9wxvrfpr28keaswlwxvpjkyxnnsjcq4c6/delegations")
            datas["networks"][8]['delegators'] = len(validator_delegations["delegation_responses"])

            umee_stats = http_json_call("http://val01.umee.m.pops.one:1317/cosmos/staking/v1beta1/validators/umeevaloper14w3wm9wxvrfpr28keaswlwxvpjkyxnnsjcq4c6")
            # fees/rate update
            datas["networks"][8]['Fees'] = f"{float('%.2f' % float(umee_stats['validator']['commission']['commission_rates']['rate']))*100}"
            datas["networks"][8]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(umee_stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            inflation_stats = http_json_call("http://val01.umee.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            datas["networks"][8]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)

            # name update
            datas["networks"][8]['Validators'][0]['Name'] = umee_stats['validator']['description']['moniker']

            #total delegation update
            datas["networks"][8]['Total_delegation'] = f"{uumee_to_umee(int(umee_stats['validator']['tokens']))} Umee"
            datas["networks"][8]['Validators'][0]['Delegation'] = f"{uumee_to_umee(int(umee_stats['validator']['tokens']))} Umee"

            # Update $$$
            datas["networks"][8]["balanceUsdTotal"] = uumee_to_umee(int(umee_stats['validator']['tokens'])) * float(datas["networks"][8]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Umee", "umee", uumee_to_umee(int(umee_stats['validator']['tokens'])),
                            datas["networks"][8]["balanceUsdTotal"], datas["networks"][8]['delegators'],
                            float(datas["networks"][8]['Fees']) / 100, "umeevaloper14w3wm9wxvrfpr28keaswlwxvpjkyxnnsjcq4c6")
            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Umee data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update umee data")
            print(e)
        ###########################################################################
        ###################### updating Axelar data #####################
        try:
            # update delegator numbers
            validator_delegations = http_json_call("http:///rpc02-axl-m.pops.one:1317/cosmos/staking/v1beta1/validators/axelarvaloper1gswfh889avkccdt5adqvglel9ttjglhdl0atqr/delegations")
            datas["networks"][7]['delegators'] = len(validator_delegations["delegation_responses"])

            axl_stats = http_json_call("http://rpc02-axl-m.pops.one:1317/cosmos/staking/v1beta1/validators/axelarvaloper1gswfh889avkccdt5adqvglel9ttjglhdl0atqr")
            # fees/rate update
            datas["networks"][7]['Fees'] = f"{float('%.2f' % float(axl_stats['validator']['commission']['commission_rates']['rate']))*100}"
            datas["networks"][7]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(axl_stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            inflation_stats = http_json_call("http://rpc02-axl-m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            datas["networks"][7]['APY'] = '18.6' #'%.2f' % (float(inflation_stats['inflation']) * 100)

            # name update
            datas["networks"][7]['Validators'][0]['Name'] = axl_stats['validator']['description']['moniker']

            #total delegation update
            datas["networks"][7]['Total_delegation'] = f"{uaxl_to_axl(int(axl_stats['validator']['tokens']))} AXL"
            datas["networks"][7]['Validators'][0]['Delegation'] = f"{uaxl_to_axl(int(axl_stats['validator']['tokens']))} AXL"

            # Update $$$
            datas["networks"][7]["balanceUsdTotal"] = uaxl_to_axl(int(axl_stats['validator']['tokens'])) * float(datas["networks"][7]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Axelar", "axelar", uaxl_to_axl(int(axl_stats['validator']['tokens'])),
                            datas["networks"][7]["balanceUsdTotal"], datas["networks"][7]['delegators'],
                            float(datas["networks"][7]['Fees']) / 100, "axelarvaloper1gswfh889avkccdt5adqvglel9ttjglhdl0atqr")
            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("AXL data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Axelar data")
            print(e)
        ###########################################################################
        ###################### updating Agoric data #####################
        try:
            # update delegator numbers
            validator_delegations = http_json_call("http://val01.bld.m.pops.one:1317/cosmos/staking/v1beta1/validators/agoricvaloper1c5vckuk54tapkzc3d0j9hegqpvgcz24jj3uzfv/delegations")
            datas["networks"][6]['delegators'] = len(validator_delegations["delegation_responses"])

            bld_stats = http_json_call("http://val01.bld.m.pops.one:1317/cosmos/staking/v1beta1/validators/agoricvaloper1c5vckuk54tapkzc3d0j9hegqpvgcz24jj3uzfv")
            # fees/rate update
            datas["networks"][6]['Fees'] = f"{float('%.2f' % float(bld_stats['validator']['commission']['commission_rates']['rate']))*100}"
            datas["networks"][6]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(bld_stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            inflation_stats = http_json_call("http://val01.bld.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            datas["networks"][6]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)

            # name update
            datas["networks"][6]['Validators'][0]['Name'] = bld_stats['validator']['description']['moniker']

            #total delegation update
            datas["networks"][6]['Total_delegation'] = f"{ubld_to_bld(int(bld_stats['validator']['tokens']))} BLD"
            datas["networks"][6]['Validators'][0]['Delegation'] = f"{ubld_to_bld(int(bld_stats['validator']['tokens']))} BLD"

            # Update $$$
            datas["networks"][6]["balanceUsdTotal"] = ubld_to_bld(int(bld_stats['validator']['tokens'])) * float(datas["networks"][6]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Agoric", "agoric", ubld_to_bld(int(bld_stats['validator']['tokens'])),
                            datas["networks"][6]["balanceUsdTotal"], len(validator_delegations["delegation_responses"]),
                            float(datas["networks"][6]['Fees']) / 100, "agoricvaloper1c5vckuk54tapkzc3d0j9hegqpvgcz24jj3uzfv")
            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Agoric data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Agoric data")
            print(e)    
        ###########################################################################
        ###################### updating Akash data #####################
        # try:
        #     stats = http_json_call("http://val01.akt.m.pops.one:1317/staking/validators/akashvaloper1sqrcxk0zxx6uwpjl5ylug2pd467vyxzt4sqze7")
        #     # fees/rate update
        #     datas["networks"][5]['Fees'] = f"{float('%.2f' % float(stats['result']['commission']['commission_rates']['rate']))*100}"
        #     datas["networks"][5]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(stats['result']['commission']['commission_rates']['rate']))*100}"

        #     # update APY
        #     inflation_stats = http_json_call("http://val01.akt.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
        #     datas["networks"][5]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)

        #     # name update
        #     datas["networks"][5]['Validators'][0]['Name'] = stats['result']['description']['moniker']

        #     #total delegation update
        #     datas["networks"][5]['Total_delegation'] = f"{uakt_to_akt(int(stats['result']['tokens']))} AKT"
        #     datas["networks"][5]['Validators'][0]['Delegation'] = f"{uakt_to_akt(int(stats['result']['tokens']))} AKT"

        #     with open('data.json', 'w') as outfile:
        #         json.dump(datas, outfile)
        #     print ("Akash data updated")
        # except Exception as e:
        #     nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
        #     print(f"{nowstring} : issue trying to update Akash data")
        #     print(e)
        ###########################################################################
        ###################### updating Covalent data #####################
        try:
            stats = http_json_call("https://api.covalenthq.com/v1/1284/apr/0/?&key=ckey_b46fe0785ae24d95a1f7abff850")
            # fees/rate update
            validator_fee=f"{float('%.2f' % float(stats['data']['items'][0]['commissionRate']))/10**16}"
            datas["networks"][9]['Fees'] = validator_fee
            datas["networks"][9]['Validators'][0]['Fees'] = validator_fee
            # update APY
            datas["networks"][9]['APY'] = '%.2f' % (float(stats['data']['items'][0]['apr']))

            #total delegation update 
            self_delegation=stats['data']['items'][0]['validatorMetadata']["staked"]
            delegation_received=stats['data']['items'][0]['validatorMetadata']["delegated"]
        
            total_delegation=atto_to_cqt(int(self_delegation)+int(delegation_received))

            datas["networks"][9]['Total_delegation'] = f"{total_delegation} CQT"
            datas["networks"][9]['Validators'][0]['Delegation'] = f"{total_delegation} CQT"

            # Update $$$
            datas["networks"][9]["balanceUsdTotal"] = total_delegation * float(datas["networks"][9]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Covalent", "covalent", total_delegation,
                            datas["networks"][9]["balanceUsdTotal"],12,float(datas["networks"][9]['Fees']) / 100,
                            "0x92668ba72601aae3fef3a7aae425489780ecdce2")
            staking_data["supportedAssets"].append(json_asset)


            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Covalent data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update CQT data")
            print(e)
        #########################################################################
        ###################### updating solana related data#####################
        try:
            all_vote_account = Solana_http_client.get_vote_accounts()["result"]["current"]
            #print (all_vote_account)

            total_delegation = 0
            total_apy = 0
            total_commission = 0
            total_pops_validator = 0

            for pops_validator in datas["networks"][1]['Validators']:
                val = [vote_account for vote_account in all_vote_account if vote_account['votePubkey'] == pops_validator['Address']]
                #print(val)
                if len(val) > 0:
                    #print(val[0])
                    val = val[0]
                    total_delegation += val['activatedStake']
                    pops_validator['Delegation'] = f"{solana_nb_converter(val['activatedStake'])} SOL"
                    total_commission += val['commission']
                    total_pops_validator += 1

            datas["networks"][1]['Total_delegation'] = f"{solana_nb_converter(total_delegation)} SOL"
            datas["networks"][1]['Fees'] = total_commission / total_pops_validator

            # Update $$$
            datas["networks"][1]["balanceUsdTotal"]= solana_nb_converter(total_delegation) * float(datas["networks"][1]["price"])

            # create staking reward assets
            json_asset=create_solana_stakingreward_assets(all_vote_account, datas)
            staking_data["supportedAssets"].append(json_asset)

            # # missing APY collection for now leaving it as static data
            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Solana data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Solana data")
            print(e)
        ###########################################################################
        ###################### updating Point data #####################
        try:
            # update delegator number
            validator_delegations = http_json_call("http://val01.point.m.pops.one:1317/cosmos/staking/v1beta1/validators/pointvaloper10w02hm23zy08w7ycx70xtn7j59yfjl8kypl5p0/delegations")
            datas["networks"][10]['delegators'] = len(validator_delegations["delegation_responses"])

            stats = http_json_call("http://val01.point.m.pops.one:1317/cosmos/staking/v1beta1/validators/pointvaloper10w02hm23zy08w7ycx70xtn7j59yfjl8kypl5p0")
            # fees/rate update
            datas["networks"][10]['Fees'] = f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"
            datas["networks"][10]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            #inflation_stats = http_json_call("http://val01.point.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            #datas["networks"][5]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)
            datas["networks"][10]['APY'] = 1600.00
            # name update
            datas["networks"][10]['Validators'][0]['Name'] = stats['validator']['description']['moniker']

            #total delegation update
            datas["networks"][10]['Total_delegation'] = f"{atto_to_one(int(stats['validator']['tokens']))} POINT"
            datas["networks"][10]['Validators'][0]['Delegation'] = f"{atto_to_one(int(stats['validator']['tokens']))} POINT"

            # Update $$$
            datas["networks"][10]["balanceUsdTotal"]=atto_to_one(int(stats['validator']['tokens'])) * float(datas["networks"][10]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Point", "point", atto_to_one(int(stats['validator']['tokens'])),
                            datas["networks"][10]["balanceUsdTotal"], len(validator_delegations["delegation_responses"]),
                            float(datas["networks"][10]['Fees']) / 100, "pointvaloper10w02hm23zy08w7ycx70xtn7j59yfjl8kypl5p0")
            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Points data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Point Network data")
            print(e)

        #########################################################################
        ###################### updating avax related data#######################
        # Global APY : https://avascan.info/api/v1/statistics
        # validator information : https://avascan.info/api/v1/validators?limit=2000 for fee and total AVAX
        total_delegation = 0
        total_apy = 0
        total_commission = 0
        total_pops_validator = 0
        total_delegators=0

        avax_stats = http_json_call("https://avascan.info/api/v1/statistics")
        total_apy = avax_stats['stakingReward']
        all_network_validator = avax_stats['totalValidator']

        all_validator_account = http_json_call(f"https://avascan.info/api/v1/validators?limit={all_network_validator}")["results"]
        for pops_validator in datas["networks"][2]['Validators']:
            val = [validator for validator in all_validator_account if validator['id'] == pops_validator['Address']][0]
            total_delegation += val['weight'] / 10**9 #self=delegation
            total_delegation += val['delegatedWeights'] #delegation
            pops_validator['Delegation'] = f"{val['weight'] / 10**9 + val['delegatedWeights']} AVAX"
            pops_validator['delegators'] = val['delegations']
            total_delegators += val['delegations']
            pops_validator['Fees'] = f"{float('%.2f' % float(val['delegationFee']))*100}"
            total_commission += val['delegationFee']
            total_pops_validator += 1

        # Update $$$
        datas["networks"][2]["balanceUsdTotal"] = total_delegation * float(datas["networks"][2]["price"])

        datas["networks"][2]['Total_delegation'] = f"{total_delegation} AVAX"
        datas["networks"][2]['Fees'] = total_commission / total_pops_validator
        datas["networks"][2]['delegators'] = total_delegators
        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        print ("AVAX data updated")

        # create staking reward assets
        json_asset=create_avax_stakingreward_assets(datas)
        staking_data["supportedAssets"].append(json_asset)

        ###########################################################################
        ###################### updating Arable data #####################
        try:
            # update delegator number
            validator_delegations = http_json_call("http://val01.acre.m.pops.one:1317/cosmos/staking/v1beta1/validators/acrevaloper1aev5mdduh578z5z894kk2cauxqntjfj6w7yq9g/delegations")
            datas["networks"][12]['delegators'] = len(validator_delegations["delegation_responses"])

            stats = http_json_call("http://val01.acre.m.pops.one:1317/cosmos/staking/v1beta1/validators/acrevaloper1aev5mdduh578z5z894kk2cauxqntjfj6w7yq9g")
            # fees/rate update
            datas["networks"][12]['Fees'] = f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"
            datas["networks"][12]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            #inflation_stats = http_json_call("http://val01.acre.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            #datas["networks"][12]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)
            datas["networks"][12]['APY'] = 18
            # name update
            datas["networks"][12]['Validators'][0]['Name'] = stats['validator']['description']['moniker']

            #total delegation update
            datas["networks"][12]['Total_delegation'] = f"{atto_to_one(int(stats['validator']['tokens']))} ACRE"
            datas["networks"][12]['Validators'][0]['Delegation'] = f"{atto_to_one(int(stats['validator']['tokens']))} ACRE"

            # Update $$$
            datas["networks"][12]["balanceUsdTotal"]=atto_to_one(int(stats['validator']['tokens'])) * float(datas["networks"][12]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Arable", "arable-protocol", atto_to_one(int(stats['validator']['tokens'])),
                            datas["networks"][12]["balanceUsdTotal"], len(validator_delegations["delegation_responses"]),
                            float(datas["networks"][12]['Fees']) / 100, "acrevaloper1aev5mdduh578z5z894kk2cauxqntjfj6w7yq9g")
            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Arable data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Arable Protocol data")
            print(e)

        ###########################################################################
        ###################### updating Quicksilver data #####################
        try:
            # update delegator number
            validator_delegations = http_json_call("http://val01.qck.m.pops.one:1327/cosmos/staking/v1beta1/validators/quickvaloper19c276ue7a2hcrt5afpgsy2rstq9gkg7frjpxyw/delegations")
            datas["networks"][14]['delegators'] = len(validator_delegations["delegation_responses"])

            stats = http_json_call("http://val01.qck.m.pops.one:1327/cosmos/staking/v1beta1/validators/quickvaloper19c276ue7a2hcrt5afpgsy2rstq9gkg7frjpxyw")
            # fees/rate update
            datas["networks"][14]['Fees'] = f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"
            datas["networks"][14]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            #inflation_stats = http_json_call("http://val01.acre.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            #datas["networks"][12]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)
            datas["networks"][14]['APY'] = 18
            # name update
            datas["networks"][14]['Validators'][0]['Name'] = stats['validator']['description']['moniker']

            #total delegation update
            datas["networks"][14]['Total_delegation'] = f"{micro_to_none(int(stats['validator']['tokens']))} QCK"
            datas["networks"][14]['Validators'][0]['Delegation'] = f"{micro_to_none(int(stats['validator']['tokens']))} QCK"

            # Update $$$
            datas["networks"][14]["balanceUsdTotal"]=micro_to_none(int(stats['validator']['tokens'])) * float(datas["networks"][12]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("Quicksilver", "quicksilver", micro_to_none(int(stats['validator']['tokens'])),
                            datas["networks"][14]["balanceUsdTotal"], len(validator_delegations["delegation_responses"]),
                            float(datas["networks"][14]['Fees']) / 100, "quickvaloper19c276ue7a2hcrt5afpgsy2rstq9gkg7frjpxyw")
            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Quicksilver data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Quicsilver data")
            print(e)

        ###########################################################################
        ###################### updating Aleph Zero data #####################
        try:
            # statically define
            #datas["networks"][13]['Delegators'] = 3

            #stats = http_json_call("http://val01.acre.m.pops.one:1317/cosmos/staking/v1beta1/validators/acrevaloper1aev5mdduh578z5z894kk2cauxqntjfj6w7yq9g")
            # fees/rate update
            #datas["networks"][13]['Fees'] = "2" #f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"
            #datas["networks"][13]['Validators'][0]['Fees'] =  "2" #f"{float('%.2f' % float(stats['validator']['commission']['commission_rates']['rate']))*100}"

            # update APY
            #inflation_stats = http_json_call("http://val01.acre.m.pops.one:1317/cosmos/mint/v1beta1/inflation")
            #datas["networks"][12]['APY'] = '%.2f' % (float(inflation_stats['inflation']) * 100)
            #datas["networks"][13]['APY'] = 18
            # name update
            datas["networks"][13]['Validators'][0]['Name'] = "P-OPS Team" #stats['validator']['description']['moniker']

            #total delegation update
            #datas["networks"][13]['Total_delegation'] = "100119.6" #f"{atto_to_one(int(stats['validator']['tokens']))} ACRE"
            #datas["networks"][13]['Validators'][0]['Delegation'] = "100119.6 Azero" #{atto_to_one(int(stats['validator']['tokens']))} ACRE"

            # Update $$$
            datas["networks"][13]["balanceUsdTotal"]= datas["networks"][13]["Total_token"] * float(datas["networks"][13]["price"])

            # create staking reward assets
            json_asset=create_stakingreward_assets("AlephZero", "aleph-zero", datas["networks"][13]["Total_token"],
                            datas["networks"][13]["balanceUsdTotal"], datas["networks"][13]['Delegators'],
                            float(datas["networks"][13]['Fees']) / 100, "5FboCt65vq5on8GBFnHpMy4oWtCsukFPCK8fbHL4gbsyny5t")

            staking_data["supportedAssets"].append(json_asset)

            with open('data.json', 'w') as outfile:
                json.dump(datas, outfile)
            print ("Aleph Zero data updated")
        except Exception as e:
            nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
            print(f"{nowstring} : issue trying to update Aleph data")
            print(e)

        ###########################################################################
        ###################### updating the graph related data#####################
        # get the name : curl -X GET https://api.oracleminer.com/graph/ens/0x1a99dd7d916117a523f3ce6510dcfd6bceab11e7
        # get indexer info : curl -X GET https://api.oracleminer.com/graph/indexer/0x1a99dd7d916117a523f3ce6510dcfd6bceab11e7

        # calculate total delegation $$$
        all_networks_total_delegation = 0
        for network in datas["networks"]:            
            if network["price"] != "NA" and is_float(network["price"]):
                print(network["Total_delegation"])
                total_network_delegation = float(network["Total_delegation"].split()[0])
                dollar_total_network_delegation = float(network["price"]) * total_network_delegation
                all_networks_total_delegation += dollar_total_network_delegation
                print (f"{network['Name']} = $ {dollar_total_network_delegation} with {total_network_delegation} @ {network['price']}")
        datas["global"]["networks_total_delegation"] = all_networks_total_delegation
        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        print (f"total network delegation updated : ${all_networks_total_delegation} ")

        #finalize staking-reward
        total_user=0
        for asset in staking_data["supportedAssets"]:
            total_user = total_user + asset["usersTotal"]
        staking_data["users"] = total_user
        staking_data["balanceUsd"] = all_networks_total_delegation
        with open('staking.json', 'w') as outfile:
            json.dump(staking_data, outfile)

    except Exception as e:
        nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
        print(f"{nowstring} : An exception occurred, but let's continue and wait for the next 1 min call")
        print(e)
    time.sleep(60)
