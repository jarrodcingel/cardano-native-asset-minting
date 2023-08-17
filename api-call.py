# Running this file will test the minting platform and mint a sample asset
import requests
from pycardano import *

# Helper to build transaction for ease of user
def buildTxForFrontend(buyerAddr, sendToAddr, feeLovelace, context):
    builder = TransactionBuilder(context)
    builder.add_input_address(Address.decode(buyerAddr))
    builder.add_output(TransactionOutput(
        Address.decode(sendToAddr),
        feeLovelace
    ))
    tx_body = builder.build(change_address=Address.decode(buyerAddr))
    return Transaction(tx_body, TransactionWitnessSet())

# Helper to test minting with sample asset configuration
def simulateMintAsset(context):
    assetConfig = { 'serialNo' : '123',
                    'ipfsHash' : '[YOUR_IPFS_HASH_HERE]',
                    'ipfsHashThumb' : '[YOUR_IPFS_HASH_THUMP_HERE]',
                    'data' : { 'Attribute 1' : 'Value 1', 
                              'Attribute 2' : 'Value 2'}
                   }
    buyerAddr = '[YOUR_BUYER_ADDR_HERE]'
    reqBody = {
        'assetConfig' : assetConfig
    }

    # Send a request to the minter
    minterUrl = 'http://127.0.0.1:8000/reserve-address'
    response = {}

    try:
        response = requests.post(minterUrl, json=reqBody)

        # If we make it here, then we should have valid response and can build tx
        sendToAddr = response.json()['address']['readableAddress']
        feeLovelace = response.json()['address']['pendingLovelace']
        tx = buildTxForFrontend(buyerAddr, sendToAddr, feeLovelace, context)
        
        # Return the cbor version of the tx for the frontend to encode, along with other helpful items
        cbor_hex = tx.to_cbor()
        response = {
            'tx' : cbor_hex,
            'sendToAddr' : sendToAddr,
            'feeLovelace' : feeLovelace,
            'message' : 'Success - transaction attached for frontend decoding'
        }
    except:
        # This means some problem occurred, likely that all addresses in use
        response = {
            'tx' : None,
            'sendToAddr' : None,
            'feeLovelace' : None,
            'message' : 'Asset minting is currently at capacity... please wait a few minutes and try again'
        }
    
    return response

# Test method, first sign into BF
BLOCKFROST_ID = 'YOUR_BF_KEY_HERE' # Populate this with your own key
NETWORK_STRING = 'preprod'
chain_context = BlockFrostChainContext(
        project_id=BLOCKFROST_ID,
        base_url="https://cardano-" + NETWORK_STRING + ".blockfrost.io/api"
        )
print(simulateMintAsset(chain_context))
