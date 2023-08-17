from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import os
import json
from pycardano import *

from .serializers import UserSerializer, GroupSerializer, AssetAddressSerializer
from .models import AssetAddress
from .tasks import periodic_mint_and_cleanup

# Helpers to populate default policy id
module_dir = os.path.dirname(__file__)
psk = PaymentSigningKey.load(os.path.join(module_dir, "minter.skey"))
pvk = PaymentVerificationKey.from_signing_key(psk)
pub_key_policy = ScriptPubkey(pvk.hash()) 
policy = ScriptAll([pub_key_policy])
policy_id = policy.hash()

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

# View all AssetAddresses
class AssetAddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AssetAddresses to be viewed or edited.
    """
    queryset = AssetAddress.objects.all()
    serializer_class = AssetAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Enable visual delete
    def destroy(self, request, pk=None, *args, **kwargs):
        return super(AssetAddressViewSet, self).destroy(request, pk, *args, **kwargs)

# Create a new wallet in the database
def create_address(request):
    addr = AssetAddress()
    key_pair = PaymentKeyPair.generate()
    addr.cborHex = key_pair.signing_key.to_cbor()
    addr.readableAddress = Address(PaymentVerificationKey.from_signing_key(key_pair.signing_key).hash(), 
                                   network=settings.NETWORK)
    addr.save()

    serializer = AssetAddressSerializer(addr, context={'request': request})
    return JsonResponse({"address": serializer.data}, status=200)

# Get new address for minting and mark it
csrf_exempt
def old_reserve_address(request):
    addr = AssetAddress.objects.filter(status="free").first()
    if addr is not None:
        addr.status = "minting"
        addr.lastUpdate = timezone.now()
        addr.pendingLovelace = settings.TOKEN_PRICE_LOVELACE
        addr.save()

    serializer = AssetAddressSerializer(addr, context={'request': request})
    return JsonResponse({"address": serializer.data}, status=200)

# Helper to create metadata for asset
def getMetaData(serialNo, ipfsHash, ipfsHashThumb, data):
    meta = {
        721: { 
            policy_id.payload.hex(): {
                "placeholderAsset": {
                    "name": "Placeholder Asset "+str(serialNo),
                    "description": "...",
                    "image": "ipfs://"+ipfsHashThumb,
                    "mediaType": "image/png",
                    "files": [
                        {
                            "name": "Placeholder Asset "+str(serialNo),
                            "mediaType": "image/png",
                            "src": "ipfs://"+ipfsHash,
                        }
                    ],
                    "data": {
                        "configuration": data
                    }
                }
            }
        }
    }
    return meta


# Reserves the token
@csrf_exempt
def reserve_address(request):
    # Get our request parameters & generate metadata
    assetConfig = json.loads(request.body)['assetConfig']
    assetMetadata = getMetaData(assetConfig['serialNo'],
                                assetConfig['ipfsHash'],
                                assetConfig['ipfsHashThumb'],
                                assetConfig['data']
                                )

    # Grab a free address if we have one, and assign metadata
    addr = AssetAddress.objects.filter(status="free").first()
    if addr is not None:
        addr.status = "minting"
        addr.lastUpdate = timezone.now()
        addr.pendingLovelace = settings.TOKEN_PRICE_LOVELACE
        addr.metadataToMint = assetMetadata
        addr.save()

    serializer = AssetAddressSerializer(addr, context={'request': request})
    return JsonResponse({"address": serializer.data}, status=200)

# Call celery async cask
def start_task(request):
    periodic_mint_and_cleanup.delay()
    return JsonResponse({"message": "Task started"}, status=200)

