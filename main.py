from web3 import Web3
import json

from termcolor import cprint
import time
import random
from config import *


min_amount = Web3.to_wei(MIN_AMOUNT, 'ether')

arbitrum_rpc_url = ARB_RPC
optimism_rpc_url = OP_RPC

arbitrum_w3 = Web3(Web3.HTTPProvider(arbitrum_rpc_url))
optimism_w3 = Web3(Web3.HTTPProvider(optimism_rpc_url))

arbitrum_address  = arbitrum_w3.to_checksum_address('0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614')
optimism_address  = optimism_w3.to_checksum_address('0xB0D502E938ed5f4df2E681fE6E419ff29631d62b')

arbitrum_eth_address = arbitrum_w3.to_checksum_address('0xbf22f0f184bCcbeA268dF387a49fF5238dD23E40')
optimism_eth_address = optimism_w3.to_checksum_address('0xB49c4e680174E331CB0A7fF3Ab58afC9738d5F8b')

abi = json.load(open('router_abi.json'))
eth_abi = json.load(open('router_eth_abi.json'))

arbitrum_router_contract = arbitrum_w3.eth.contract(address=arbitrum_address, abi=abi)
optimism_router_contract = optimism_w3.eth.contract(address=optimism_address, abi=abi)

arbitrum_router_eth_contract = arbitrum_w3.eth.contract(address=arbitrum_eth_address, abi=eth_abi)
optimism_router_eth_contract = optimism_w3.eth.contract(address=optimism_eth_address, abi=eth_abi)

def get_balance_eth_arbitrum(privatekey):
    
    try:
        account = arbitrum_w3.eth.account.from_key(privatekey)
        address = account.address
        return arbitrum_w3.eth.get_balance(address)
    
    except Exception as error:
        cprint(f'\n>>> Failed to receive ETH balance in Arbitrum | {error}', 'red')
        return None

def get_balance_eth_optimism(privatekey):
    
    try:
        account = optimism_w3.eth.account.from_key(privatekey)
        address = account.address
        return optimism_w3.eth.get_balance(address)
    
    except Exception as error:
        cprint(f'\n>>> Failed to receive ETH balance in Optimism | {error}', 'red')
        return None

def swap(mode, privatekey, amount):
    
    try:
        amount_gwei = round(Web3.from_wei(amount,'ether'), 4)

        if mode == "ARB_OPT":
            w3 = arbitrum_w3
            router_contract = arbitrum_router_contract
            dstChainId = 111
            router_eth_contract = arbitrum_router_eth_contract
            text_transaction_waitting = f'Waitting ETH transaction Arbitrum --> Optimism amount {amount_gwei}'
            transaction_link = "Stargate bridge ETH | https://arbiscan.io/tx/" 
        else:
            w3 = optimism_w3
            router_contract = optimism_router_contract
            dstChainId = 110
            router_eth_contract = optimism_router_eth_contract
            text_transaction_waitting = f'Waitting ETH transaction Optimism --> Arbitrum amount {amount_gwei}'
            transaction_link = "Stargate bridge ETH | https://optimistic.etherscan.io/tx/"         

        address = w3.eth.account.from_key(privatekey).address
        nonce = w3.eth.get_transaction_count(address)
        gas_price = w3.eth.gas_price
        fees = router_contract.functions.quoteLayerZeroFee(dstChainId,
                                                           1,
                                                           address,
                                                           "0x",
                                                           [0, 0, address]
                                                           ).call()
        fee = fees[0]

        amountOutMin = amount - (amount * 5) // 1000

        swap_txn = router_eth_contract.functions.swapETH(
            dstChainId, address, address, amount, amountOutMin
        ).build_transaction({
            'from': address,
            'value': amount + fee,
            'gas': 2000000,
            'gasPrice': gas_price,
            'nonce': nonce,
        })

        signed_swap_txn = w3.eth.account.sign_transaction(swap_txn, privatekey)
        swap_txn_hash = w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        
        print(text_transaction_waitting)

        time.sleep(20)

        cprint(transaction_link + swap_txn_hash.hex(), "green")    

    except Exception as error:
        cprint(f'\n>>> Stargate bridge | {error}', 'red')

if __name__ == '__main__':

    with open("private_keys.txt", "r") as f:
        keys_list = [row.strip() for row in f]
    
    random.shuffle(keys_list)

    for privatekey in keys_list:
        cprint(f'\n=============== start: {privatekey} ===============', 'yellow')

        arbitrum_balance = get_balance_eth_arbitrum(privatekey)
        optimism_balance = get_balance_eth_optimism(privatekey)

        if arbitrum_balance == None or optimism_balance == None:
            continue
        
        if arbitrum_balance > optimism_balance:
            if arbitrum_balance <= min_amount:
                cprint(f'\n>>> ETH in the Arbitrum network is less than {MIN_AMOUNT}', 'red')
                continue
        
            mode = "ARB_OPT"
            amount = arbitrum_balance - min_amount        
        else:
            if optimism_balance <= min_amount:
                cprint(f'\n>>> ETH in the Optimism network is less than {MIN_AMOUNT}', 'red')
                continue

            mode = "OPT_ARB"
            amount = optimism_balance - min_amount

        swap(mode, privatekey, amount)

        time.sleep(random.randint(SLEEP_TIME_MIN, SLEEP_TIME_MAX))