# cardano-native-asset-minting
Minting system for Cardano native assets

# Installation & Setup

Clone repo and execute the following commands in the root folder:

1. Install redis (used as broker for celery, to allow communication between minting processes and the server). The following works on Mac:
    
        $ brew install redis

2.  Create and activate virtual environment:

        $ python -m venv .
        $ source /venv/bin/activate

3. Install python dependencies

        $ pip install -r requirements.txt

4. Create new PostgreSQL database to use for storage (assumes PostgreSQL is already installed)

5. Open `settings.py` and replace the contents of the `DATABASES` variable with the info for the database you just created

6. Still in `settings.py`, update the batch of variables below `DEBUG` with your own parameters & information where applicable (e.g. your own blockfrost project ID, your own address to send proceeds, etc. Items that need updated are clearly denoted in brackets of the form `[YOUR_ITEM_HERE]`)

7. Replace `server/minter.skey` with the secret key of an address you control; do not commit this to version control

8. Set up the database & models (replace superuser with your own info):

        $ python manage.py makemigrations
        $ python manage.py migrate
        $ python manage.py createsuperuser --email [YOUR_EMAIL_HERE] --username admin

# Starting Minting Platform

You will need 4 different terminals to properly run everything needed for the minting platform (instructions for each terminal below):

1. Start the backend server:

        $ python manage.py runserver

2. Start redis:

        $ redis-server

3. Start celery worker that handles the minting on the blockchain:

        $ celery -A assetminter worker -l info

4. Start celery beat that handles repeatedly dispatching the worker above:

        $ celery -A assetminter beat -l info

# Using Minting Platform

1. Visit http://127.0.0.1:8000/ in your browser and log in as the superuser you created above. This isn't strictly necessary, but will help you see what's going on as the minting platform runs (click into the "addresses" section and periodically refresh)

2. Visit http://127.0.0.1:8000/create-address to create a new minting address. You need at least 1 for the minting to run properly. Each visit to this page will generate an additional new address (start with 2 or 3).

3. To reserve an address for minting, visit http://127.0.0.1:8000/reserve-address. In order to mint a token, you need to send the specified amount of lovelace to the specified address within the time limit configured in `settings.py`. This defaults to 5 ADA. In the future, this can be easily modified to accept unique metadata for each call (default metadata stored in `server/models.py` and should be updated for your specific metadata)

4. You should be able to copy the code (after updating for your token attributes and use case appropriately) in `api-call.py` to integrate with your existing processes, including any upstream pipeline for dynamic metadata