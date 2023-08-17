from __future__ import absolute_import, unicode_literals
from time import sleep
from celery import shared_task
import datetime
from pycardano import *
from django.conf import settings
from django.utils import timezone
import os
from .models import AssetAddress
from .minthelpers import *

# Helper to handle mint for set of addresses
def mint_helper(addrs, chain_context, policy_id, native_scripts, minter, initialFailedState=False):
    for addr in addrs:
        sleep(1)

        # Load key from saved cbor
        addr_sk = PaymentSigningKey.from_primitive(bytes.fromhex(addr.cborHex)[2:])
        addr_vk = PaymentVerificationKey.from_signing_key(addr_sk)
        addr_addr = Address(addr_vk.hash(), network=settings.NETWORK)
        fromAddr = {'skey' : addr_sk, 'vkey' : addr_vk, 'addr' : addr_addr}
        print("Onto Address " + str(addr.pk))

        # Get utxos at address - exception means there's nothing there
        minted = False
        failed = initialFailedState
        try:
            utxos = chain_context.utxos(addr.readableAddress)
            receiverTxId = None
            for utxo in utxos:
                # Check if output contains proper lovelace
                if utxo.output.amount.coin == addr.pendingLovelace:
                    receiverTxId = utxo.input.transaction_id
                    break

            # If we have the right utxo, get address (else, return)
            if receiverTxId:
                tx_utxos = chain_context.api.transaction_utxos(receiverTxId)
                receiver_addr = tx_utxos.inputs[0].address

                # Get metadata in the right form
                metadataToMint = { 721 : addr.metadataToMint["721"] }

                # Build the transaction
                tx = build_mint_tx(receiver_addr, 
                                    fromAddr,
                                    settings.PROCEEDS_ADDRESS, 
                                    policy_id,
                                    chain_context, 
                                    metadataToMint,
                                    native_scripts)
                
                # Submit the tx to the chain
                tx_id = sign_mint_tx(tx,
                                    fromAddr,
                                    minter,
                                    chain_context,
                                    metadataToMint,
                                    native_scripts)
                
                # If successful mint, then we can update accordingly
                if tx_id:
                    minted = True
                    failed = False
                else:
                    failed = True
                    minted = False

        except Exception as e:
            print(e)
        
        # Now that mint is done (or attempted), update state
        if not minted and not failed and addr.lastUpdate < timezone.now() - datetime.timedelta(minutes=settings.MINT_TIMEOUT_MINUTES):
            print("Freeing pending address that has been idle for too long without receiving payment")
            addr.status = "free"
            addr.lastUpdate = timezone.now()
            addr.save()
        elif not minted and failed:
            addr.status = "failed"
            addr.lastUpdate = timezone.now()
            addr.save()
        elif minted:
            addr.status = "done"
            addr.lastUpdate = timezone.now()
            addr.save()

# Helper to check pending mints
def check_pending_mints(chain_context, policy_id, native_scripts, minter):
    print('Check pending mints')

    # Iterate through each pending address
    addrs = AssetAddress.objects.filter(status="minting")
    print("Found " + str(len(addrs)) + " addresses with pending mints")
    
    mint_helper(addrs, chain_context, policy_id, native_scripts, minter)

# Helper to clean up completed mints
def cleanup_completed_mints():
    print('Cleaning up completed mints')

    # Iterate through each completed mint
    addrs = AssetAddress.objects.filter(status="done")
    print("Found " + str(len(addrs)) + " addresses with completed mints to clean up")
    for addr in addrs:
        sleep(1)
        if addr.lastUpdate < timezone.now() - datetime.timedelta(seconds=settings.POST_MINT_CLEANUP_WAIT_SECONDS):
            addr.status = "free"
            addr.lastUpdate = timezone.now()
            addr.save()

# Helper to retry failed mints
def retry_failed_mints(chain_context, policy_id, native_scripts, minter):
    print('Retrying failed mints')

    # Iterate through each failed mint
    addrs = AssetAddress.objects.filter(status="failed")
    print("Found " + str(len(addrs)) + " addresses with failed mints to retry")

    # Mint
    mint_helper(addrs, chain_context, policy_id, native_scripts, minter, True)

# Periodically iterate through each minting address, check utxos, and mint
@shared_task(name='periodic_mint_and_cleanup')
def periodic_mint_and_cleanup():

    # Connect to blockfrost
    chain_context = BlockFrostChainContext(
        project_id=settings.BLOCKFROST_ID,
        base_url="https://cardano-" + settings.NETWORK_STRING + ".blockfrost.io/api"
        )
    
    # Load minting wallet
    module_dir = os.path.dirname(__file__)
    psk = PaymentSigningKey.load(os.path.join(module_dir, "minter.skey"))
    pvk = PaymentVerificationKey.from_signing_key(psk)
    minterAddr = Address(pvk.hash(), network=settings.NETWORK)
    minter = { 'skey' : psk, 'vkey' : pvk, 'addr' : minterAddr}

    # Establish native script / auxiliary data for cardano
    pub_key_policy = ScriptPubkey(pvk.hash()) 
    policy = ScriptAll([pub_key_policy])
    policy_id = policy.hash()
    native_scripts = [policy]

    # 1) Check pending mints
    check_pending_mints(chain_context, policy_id, native_scripts, minter)

    # 2) Clean up completed mints
    cleanup_completed_mints()

    # 3) Retry failed mints
    retry_failed_mints(chain_context, policy_id, native_scripts, minter)
