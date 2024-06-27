import asyncio
from web3 import Web3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import json
from config import WEB3_PROVIDER_URI, SWAP_CONTRACT_ADDRESS, TELEGRAM_TOKEN, ROUTER_CONTRACT_ADDRESS
from database import get_active_wallets
from telegram import Bot
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)

web3_instance = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
bot = Bot(token=TELEGRAM_TOKEN)

WETH_ADDRESS = '0x40375c92d9faf44d2f9db9bd9ba41a3317a2404f'

with open('swap_contract_abi.json') as f:
    swap_contract_abi = json.load(f)

with open('router_contract_abi.json') as f:
    router_contract_abi = json.load(f)

swap_contract_address = SWAP_CONTRACT_ADDRESS
router_contract_address = ROUTER_CONTRACT_ADDRESS
swap_contract = web3_instance.eth.contract(address=swap_contract_address, abi=swap_contract_abi)
router_contract = web3_instance.eth.contract(address=router_contract_address, abi=router_contract_abi)

sniping_tasks = {}
sniping_task = None

async def handle_event(event):
    print(f'PairCreated event detected: {event}')

    if event['args']['token0'].lower() == WETH_ADDRESS.lower() or event['args']['token1'].lower() == WETH_ADDRESS.lower():
        token_contract_address = None
        if event['args']['token0'].lower() == WETH_ADDRESS.lower():
            token_contract_address = event['args']['token1']
        elif event['args']['token1'].lower() == WETH_ADDRESS.lower():
            token_contract_address = event['args']['token0']
    else:
        return
    
    print(token_contract_address)

    for user_id, task_info in sniping_tasks.items():
        if task_info['token_to_snipe'].lower() == token_contract_address.lower():
            address = task_info['address']
            private_key = task_info['private_key']
            amount_to_spend = task_info['amount_to_spend']
            try:
                before_balance = web3_instance.eth.get_balance(address)
                tx_hash, after_balance = await auto_buy_on_liquidity_addition(web3_instance, address, private_key, amount_to_spend, token_contract_address)
                success = True
            except Exception as e:
                tx_hash = str(e)
                after_balance = before_balance
                success = False
            
            await send_telegram_message(user_id, address, amount_to_spend, success, before_balance, after_balance, tx_hash)

async def auto_buy_on_liquidity_addition(web3_instance, address, private_key, max_spend, token_contract_address):
    nonce = web3_instance.eth.get_transaction_count(address)
    gas_price = web3_instance.eth.gas_price

    path = [web3_instance.to_checksum_address(WETH_ADDRESS), web3_instance.to_checksum_address(token_contract_address)]
    amountIn = web3_instance.to_wei(max_spend, 'ether')
    amountsOut = router_contract.functions.getAmountsOut(amountIn, path).call()
    amountOut = amountsOut[1]
    to = address
    deadline = int(datetime.now().timestamp()) + 60 * 20 

    tx = router_contract.functions.swapETHForExactTokens(
        amountOut,
        path,
        to,
        deadline
    ).build_transaction({
        'from': address,
        'value': web3_instance.to_wei(max_spend, 'ether'),
        'gas': 500_000,
        'gasPrice': gas_price,
        'nonce': nonce,
        'chainId': 1116
    })

    try:
        estimated_gas = web3_instance.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas
        print(f'Estimated gas: {estimated_gas}')
    except Exception as e:
        raise Exception(f"Estimated Gas: {str(e)}")

    signed_tx = web3_instance.eth.account.sign_transaction(tx, private_key)
    
    try:
        tx_hash = web3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise Exception(f"Transaction failed with status {receipt.status}")

        after_balance = web3_instance.eth.get_balance(address)
        return tx_hash.hex(), after_balance
    except Exception as e:
        raise Exception(f"Transaction failed: {str(e)}")

async def send_telegram_message(user_id, address, amount, success, before_balance, after_balance, tx_hash):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = 'Success' if success else 'Fail'
    message = (
        f"Auto-buy Transaction\n"
        f"Wallet Address: {address}\n"
        f"Amount: {amount} CORE\n"
        f"Status: {status}\n"
        f"Transaction Hash: {tx_hash}\n"
        f"Balance Before: {Web3.from_wei(before_balance, 'ether')} CORE\n"
        f"Balance After: {Web3.from_wei(after_balance, 'ether')} CORE\n"
        f"Time: {time}"
    )
    await bot.send_message(
        chat_id=user_id, 
        text=message, parse_mode='Markdown'
    )

    stop_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Stop Liquidity Sniping", callback_data='stop_liquidity_sniping')]
    ])
    await bot.send_message(chat_id=user_id, text="Click the button below to stop liquidity sniping:", reply_markup=stop_markup)

async def event_listener():
    previous_len = 0
    while True:
        event_filter = swap_contract.events.PairCreated.create_filter(fromBlock=0)
        try:
            events = event_filter.get_all_entries()
            current_len = len(events)
            print(f'{current_len} {previous_len}')
            if current_len != previous_len:
                await handle_event(events[current_len-1])
            previous_len = current_len
        except ValueError as error:
            if "filter not found" in str(error).lower():
                print("The filter seems to have expired or is non-existent. Recreating filter...")
                event_filter = swap_contract.events.PairCreated.create_filter(fromBlock=0)
            else:
                print(f"Encountered an error: {error}")
        await asyncio.sleep(1)

async def start_liquidity_sniping_task(user_id, sniping_info):
    global sniping_tasks, sniping_task
    sniping_tasks[user_id] = {
        'token_to_snipe': sniping_info['token_address'],
        'amount_to_spend': sniping_info['amount'],
        'address': sniping_info['address'],
        'private_key': sniping_info['private_key']
    }
    if sniping_task is None:
        sniping_task = asyncio.create_task(event_listener())

async def stop_liquidity_sniping_task(user_id):
    global sniping_tasks, sniping_task
    if user_id in sniping_tasks:
        del sniping_tasks[user_id]
    if not sniping_tasks and sniping_task:
        sniping_task.cancel()
        sniping_task = None
        print("Liquidity sniping stopped.")

__all__ = ["start_liquidity_sniping_task", "stop_liquidity_sniping_task", "sniping_tasks", "event_listener"]
