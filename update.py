import json
import time
import os
from datetime import datetime
import requests
from requests.exceptions import HTTPError
from pyhmy import staking
from typing import Any
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv('CMC_API_KEY')
SOLANA_RPC = os.getenv('SOLANA_RPC')

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

def atto_to_cqt(atto):
    return int(atto / (10 ** 18))

def micro_to_none(number):
    return int(number / (10 ** 6))

def nano_to_none(number):
    return int(number / (10 ** 9))

def atto_to_none(atto):
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
        return json.loads(r.content)

def http_post_request(method, params, url):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "jsonrpc": "2.0",
        "method": f"{method}",
        "params": params,
        "id": 1,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Error sending JSON RPC request")
  
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

# chainname ie umee
# apiurl ie http://val01.umee.m.pops.one:1317
# valoper ie umeevaloper14w3wm9wxvrfpr28keaswlwxvpjkyxnnsjcq4c6
# datas the json that contains all pops datas
# dataindex, the index representing the element of the chain, ie 8 for umee
# funcconvert is a func object
# stakingrewardslugname depends on staking reward slug name (ie umee for Umee)
# list of assets can be seen here https://api-beta.stakingrewards.com/v1/list/assets
# datas is the pops API data
# registry is the cosmos registry obtained from https://chains.cosmos.directory/
def update_tendermint_chain(chainname, apiurl, valoper, dataindex, denom, funcconvert, stakingrewardslugname, datas, registry):
    cosmosdirectorynotworking = ["axelar", "point"]

    print (f"{chainname} updates ...")
    try:
        # update delegator numbers
        validator_delegations = http_json_call(f"{apiurl}/cosmos/staking/v1beta1/validators/{valoper}/delegations")
        datas["networks"][dataindex]['delegators'] = len(validator_delegations["delegation_responses"])

        network_stats = http_json_call(f"{apiurl}/cosmos/staking/v1beta1/validators/{valoper}")
        # fees/rate update
        valfee=float('%.2f' % float(network_stats['validator']['commission']['commission_rates']['rate']))*100
        datas["networks"][dataindex]['Fees'] = f"{valfee}"
        datas["networks"][dataindex]['Validators'][0]['Fees'] =  f"{valfee}"

        # update APY
        chaininfo=next(chain for chain in registry["chains"] if chain["name"] == chainname.lower())
        #print (chaininfo)
        # skipped chain use the static data on data.json for the APR
        if chainname.lower() not in cosmosdirectorynotworking and "calculated_apr" in chaininfo["params"]:
            apr = chaininfo["params"]["calculated_apr"]
            valapr='%.2f' % (100 * apr * ((1 - valfee / 100)))
            datas["networks"][dataindex]['APY'] = valapr
            print(f"{chainname} valapr is {valapr} with validator fee of {valfee} and calculated_apr of {apr}")

        # name update
        datas["networks"][dataindex]['Validators'][0]['Name'] = network_stats['validator']['description']['moniker']

        #total delegation update
        datas["networks"][dataindex]['Total_delegation'] = f"{funcconvert(int(network_stats['validator']['tokens']))} {denom}"
        datas["networks"][dataindex]['Validators'][0]['Delegation'] = f"{funcconvert(int(network_stats['validator']['tokens']))} {denom}"

        # Update $$$
        datas["networks"][dataindex]["balanceUsdTotal"] = funcconvert(int(network_stats['validator']['tokens'])) * float(datas["networks"][dataindex]["price"])

        # create staking reward assets
        json_asset=create_stakingreward_assets(chainname, stakingrewardslugname, funcconvert(int(network_stats['validator']['tokens'])),
                        datas["networks"][dataindex]["balanceUsdTotal"], datas["networks"][dataindex]['delegators'],
                        float(datas["networks"][dataindex]['Fees']) / 100, valoper)
        staking_data["supportedAssets"].append(json_asset)

        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)
        print (f"{chainname} data updated")
    except Exception as e:
        nowstring = now.strftime("%d/%m/%Y, %H:%M:%S")
        print(f"{nowstring} : issue trying to update {chainname} data")
        print(e)

def update_sui():
    dataindex=17
    denom="SUI"
    chainname="Sui"
    stakingrewardslugname="sui"
    suirpc="https://sui-rpc-mainnet.testnet-pride.com"
    validator_address = '0xd1dbb08191b4ae8e227935669c1862ba75a41cd7df5970002eafb2f365c32ed8'

    print (f"Sui updates ...")
    
    # query validator informations
    response=http_post_request("suix_getLatestSuiSystemState",[], suirpc)
    activevalidators=response['result']['activeValidators']   
    validator = [v for v in activevalidators if v.get('suiAddress') == validator_address][0]

    # query validator apys
    response=http_post_request("suix_getValidatorsApy",[], suirpc)
    apys=response['result']['apys']   
    apy = [v for v in apys if v.get('address') == validator_address][0]
    
    # update delegator numbers
    datas["networks"][dataindex]['delegators'] = 1

    # name update
    datas["networks"][dataindex]['Validators'][0]['Name'] = validator['name']

    # update APY
    datas["networks"][dataindex]['APY'] = '%.2f' % (float(apy['apy']) * 100)

    # fees update
    datas["networks"][dataindex]['Fees'] = f"{float('%.2f' % float(validator['commissionRate'])) / 100}"
    datas["networks"][dataindex]['Validators'][0]['Fees'] =  f"{float('%.2f' % float(validator['commissionRate'])) / 100}"

    #total delegation update stakingPoolSuiBalance 
    datas["networks"][dataindex]['Total_delegation'] = f"{nano_to_none(int(validator['stakingPoolSuiBalance']))} {denom}"
    datas["networks"][dataindex]['Validators'][0]['Delegation'] = f"{nano_to_none(int(validator['stakingPoolSuiBalance']))} {denom}"

    # Update $$$
    datas["networks"][dataindex]["balanceUsdTotal"] = nano_to_none(int(validator['stakingPoolSuiBalance'])) * float(datas["networks"][dataindex]["price"])

    # create staking reward assets
    json_asset=create_stakingreward_assets(chainname, stakingrewardslugname, nano_to_none(int(validator['stakingPoolSuiBalance'])),
                    datas["networks"][dataindex]["balanceUsdTotal"], datas["networks"][dataindex]['delegators'],
                    float(datas["networks"][dataindex]['Fees']) / 100, validator_address)
    staking_data["supportedAssets"].append(json_asset)

def get_solana_votes():
    try:
        url = SOLANA_RPC
        
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getVoteAccounts",
        }
        r = requests.post(url, json=data)
    except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
    else:
        content = json.loads(r.content)
        return content

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

        # updating price from API
        coinlist="harmony,solana,avalanche,the-graph,stafi,akash-network,umee,covalent,agoric,axelar,point-network,forta,arable-protocol,aleph-zero,aura-network,sui"
        #uptick / quicksilver not supporter on CMC
        url=f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?slug={coinlist}&CMC_PRO_API_KEY={CMC_API_KEY}"
        allprice=http_json_call(url)

        i=0
        for network in datas["networks"]:
            cmcid=network["cmc_id"]
            if cmcid != 0:
                price=float('%.3f' % allprice["data"][str(cmcid)]["quote"]["USD"]["price"])
                print(f"name={network['Name']} cmcid={cmcid} price={price}")
                network["price"] = price
            i = i + 1

        with open('data.json', 'w') as outfile:
            json.dump(datas, outfile)


        # Obtain cosmos registry data (ie we need it for APR calculation)
        registry=http_json_call("https://chains.cosmos.directory/")
        

        #########################################################################
        ###################### updating solana related data#####################
        try:
            all_vote_account = get_solana_votes()['result']['current']
            #print (all_vote_account)

            total_delegation = 0
            total_apy = 0
            total_commission = 0
            total_pops_validator = 0

            for pops_validator in datas["networks"][1]['Validators']:
                val = [vote_account for vote_account in all_vote_account if vote_account['votePubkey'] == pops_validator['Address']]
                #print(val)
                if len(val) > 0:
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
        ###################### updating Umee related data #####################
        apiurl="http://val02-umee-m.pops.one:1317"
        valoper="umeevaloper14w3wm9wxvrfpr28keaswlwxvpjkyxnnsjcq4c6"
        dataindex=8
        funcconvert=micro_to_none
        stakingrewardslugname="umee"
        update_tendermint_chain("Umee", apiurl, valoper, dataindex, "UMEE", funcconvert, stakingrewardslugname, datas, registry)

        ###########################################################################
        ###################### updating Axelar related data #####################
        apiurl="http://rpc02-axl-m.pops.one:1317"
        valoper="axelarvaloper1gswfh889avkccdt5adqvglel9ttjglhdl0atqr"
        dataindex=7
        funcconvert=micro_to_none
        stakingrewardslugname="axelar"
        update_tendermint_chain("Axelar", apiurl, valoper, dataindex, "AXL", funcconvert, stakingrewardslugname, datas, registry)

        ###########################################################################
        ###################### updating Agoric related data #####################
        apiurl="http://val02-bld-m.pops.one:1317"
        valoper="agoricvaloper1c5vckuk54tapkzc3d0j9hegqpvgcz24jj3uzfv"
        dataindex=6
        funcconvert=micro_to_none
        stakingrewardslugname="agoric"
        update_tendermint_chain("Agoric", apiurl, valoper, dataindex, "BLD", funcconvert, stakingrewardslugname, datas, registry)

        ###########################################################################
        ###################### updating Akash related data #####################
        #apiurl="http://val01.akt.m.pops.one:1317"
        #valoper="akashvaloper1sqrcxk0zxx6uwpjl5ylug2pd467vyxzt4sqze7"
        #dataindex=5
        #funcconvert=micro_to_none
        #stakingrewardslugname="akash" # temporary as slug is not yet in https://api-beta.stakingrewards.com/v1/list/assets
        #update_tendermint_chain("Akash", apiurl, valoper, dataindex, "AKT", funcconvert, stakingrewardslugname, datas)  
 
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

        ###########################################################################
        ###################### updating Point related data #####################
        apiurl="http://val01.point.m.pops.one:1317"
        valoper="pointvaloper10w02hm23zy08w7ycx70xtn7j59yfjl8kypl5p0"
        dataindex=10
        funcconvert=atto_to_none
        stakingrewardslugname="point"
        update_tendermint_chain("Point", apiurl, valoper, dataindex, "POINT", funcconvert, stakingrewardslugname, datas, registry)

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
        ###################### updating Arable related data #####################
        apiurl="http://val01.acre.m.pops.one:1317"
        valoper="acrevaloper1aev5mdduh578z5z894kk2cauxqntjfj6w7yq9g"
        dataindex=12
        funcconvert=atto_to_none
        stakingrewardslugname="arable-protocol"
        update_tendermint_chain("Acrechain", apiurl, valoper, dataindex, "ACRE", funcconvert, stakingrewardslugname, datas, registry)

        ###########################################################################
        ###################### updating the Quicksilver related data #####################
        apiurl="http://val01.qck.m.pops.one:1327"
        valoper="quickvaloper19c276ue7a2hcrt5afpgsy2rstq9gkg7frjpxyw"
        dataindex=14
        funcconvert=micro_to_none
        stakingrewardslugname="quicksilver" # temporary as slug is not yet in https://api-beta.stakingrewards.com/v1/list/assets
        update_tendermint_chain("Quicksilver", apiurl, valoper, dataindex, "QCK", funcconvert, stakingrewardslugname, datas, registry)

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
        ###################### updating the aura related data #####################
        apiurl="https://aura.api.kjnodes.com"
        valoper="auravaloper1hmmlyt7mchy6t49z0hmacsem3pyljpzhv9leat"
        dataindex=15
        funcconvert=micro_to_none
        stakingrewardslugname="aura-network" # temporary as slug is not yet in https://api-beta.stakingrewards.com/v1/list/assets
        update_tendermint_chain("Aura", apiurl, valoper, dataindex, "Aura", funcconvert, stakingrewardslugname, datas, registry)

        ###########################################################################
        ###################### updating the uptick related data ###################
        apiurl="https://uptick.api.kjnodes.com"
        valoper="uptickvaloper1q8gmvc05t0yq2eg0g3plkcqlhy97mvk0533f2v"
        dataindex=16
        funcconvert=atto_to_none
        stakingrewardslugname="uptick" # temporary as slug is not yet in https://api-beta.stakingrewards.com/v1/list/assets
        update_tendermint_chain("Uptick", apiurl, valoper, dataindex, "Uptick", funcconvert, stakingrewardslugname, datas, registry)

        #####################################################################
        ###################### updating the sui data ########################
        update_sui()

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
        print(f"{nowstring} : An exception occurred, but let's continue and wait for the next 10 min call")
        print(e)
    time.sleep(600)
