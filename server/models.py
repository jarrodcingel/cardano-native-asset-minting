import os
from django.db import models
from pycardano import *

# Helpers to populate default policy id
module_dir = os.path.dirname(__file__)
psk = PaymentSigningKey.load(os.path.join(module_dir, "minter.skey"))
pvk = PaymentVerificationKey.from_signing_key(psk)
pub_key_policy = ScriptPubkey(pvk.hash()) 
policy = ScriptAll([pub_key_policy])
policy_id = policy.hash()

# Address to mint from
class AssetAddress(models.Model):
    cborHex = models.CharField(max_length=200)
    readableAddress = models.CharField(max_length=200)
    status = models.CharField(
        max_length=16,
        choices=[('free', 'free'), 
                ('minting', 'minting'), 
                ('failed', 'failed'),
                ('done', 'done'),
                ],
        default='free'
    )
    lastUpdate = models.DateTimeField(auto_now_add=True, blank=True)
    pendingLovelace = models.IntegerField(default=0)

    # Store metadata as field in address so it can be updated as needed
    def metadata_default():
        mintingMetadata = {
            721: { 
                policy_id.payload.hex(): {
                    "placeholderAsset": {
                        "name": "Placeholder Asset",
                        "description": "An example Cardano native asset",
                        "image": "ipfs://[YOUR_IPFS_HASH_HERE]",
                        "mediaType": "image/png",
                        "files": [
                        {
                            "mediaType": "image/png",
                            "name": "Placeholder Asset",
                            "src": "ipfs://[YOUR_IPFS_HASH_HERE]"
                        }
                        ]
                    }
                }
            }
        }
        return mintingMetadata
    
    metadataToMint = models.JSONField("MetadataToMint", default=metadata_default)