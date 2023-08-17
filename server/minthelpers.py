# Helpers for minting
from pycardano import *

# Helper to properly calculate Cardano minUTXO requirement
def modifiedMinLovelace(context, address, nft):
    helper = min_lovelace(context=context, output=TransactionOutput(address,Value(0, nft)))
    result = min_lovelace(context=context, output=TransactionOutput(address,Value(helper, nft)))
    return result

# Helper to build transaction outputs
def assetTxOutputs(buyerAddr, policy_id, chain_context):
    assetsToMint = {}
    assetsToMint[b"placeholderAsset"] = 1
    
    assets = MultiAsset.from_primitive(
        {
            policy_id.payload : assetsToMint
        }
    )

    # Build these 2 outputs and return them
    min_val_coins = modifiedMinLovelace(chain_context, buyerAddr, assets)
    assetsOutput = TransactionOutput(buyerAddr, Value(min_val_coins, assets))
    return assets, assetsOutput

# Helper to build minting transaction
def build_mint_tx(buyerAddr, fromWallet, proceedsAddr, policy_id, chain_context, assetMetadata, native_scripts):
    # Parse address of buyer
    buyerAddress = Address.decode(buyerAddr)

    # Call helper to build outputs
    assets, assetsOutput = assetTxOutputs(buyerAddress, policy_id, chain_context)

    # Re-add the metadata to be minted
    auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(assetMetadata)))

    # Build transaction with builder
    try:
        builder = TransactionBuilder(chain_context)
        builder._estimate_fee = lambda : 300000
        builder.add_input_address(fromWallet['addr'])
        builder.mint = assets
        builder.native_scripts = native_scripts
        builder.auxiliary_data = auxiliary_data
        builder.add_output(assetsOutput)
        tx_body = builder.build(change_address=Address.decode(proceedsAddr))
        return Transaction(tx_body, TransactionWitnessSet())
    except Exception as e:
        print(e)
        return None

# Helper to sign asset minting transaction
def sign_mint_tx(tx, fromWallet, mintWallet, chain_context, assetMetadata, native_scripts):
    # Add the auxiliary metadata
    auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(assetMetadata)))
    tx.auxiliary_data = auxiliary_data

    # Add sending wallet signature
    fromSignature = fromWallet['skey'].sign(tx.transaction_body.hash())
    fromVkWitnesses = [VerificationKeyWitness(fromWallet['vkey'], fromSignature)]
    fromWitness = TransactionWitnessSet(vkey_witnesses=fromVkWitnesses).vkey_witnesses[0]

    # Add minting wallet signature
    mintSignature = mintWallet['skey'].sign(tx.transaction_body.hash())
    mintVkWitnesses = [VerificationKeyWitness(mintWallet['vkey'], mintSignature)]
    mintWitness = TransactionWitnessSet(vkey_witnesses=mintVkWitnesses).vkey_witnesses[0]

    # Add both signatures
    witnesses = TransactionWitnessSet(vkey_witnesses=[fromWitness, mintWitness],
        native_scripts=native_scripts)
    tx.transaction_witness_set = witnesses
    tx_id = tx.transaction_body.hash().hex()

    # Now submit to blockchain
    try:
        chain_context.submit_tx(tx.to_cbor())
        return tx_id
    except Exception as e:
        print(e)
        return None

