import requests
import json
import re
import ssl
import asyncio

from websockets import client

from tokens import USER_TOKEN
REGION = 'eu-west-1'
VERSION = '1.1.110'
SAVE = 'slot1'

### All credit for this API work goes to https://github.com/michelsciortino/FZ-Manager

FACTORIO_ZONE_ENDPOINT = 'factorio.zone'

class ServerStatus:
    OFFLINE = 'OFFLINE'
    STARTING = 'STARTING'
    STOPPING = 'STOPPING'
    RUNNING = 'RUNNING'

class FZClient:
    def __init__(self):
        self.user_token = USER_TOKEN
        self.region = REGION
        self.save = SAVE
        self.version = VERSION

        self.socket = None
        self.visit_secret = None
        self.referrer_code = None
        self.regions = {}
        self.versions = {}
        self.slots = {}
        self.saves = {}
        self.mods = []
        self.running = False
        self.launch_id = None
        self.server_address = None
        self.server_status = ServerStatus.OFFLINE
        self.mods_sync = False
        self.saves_sync = False
        

    async def connect(self):
        ssl_context = ssl.SSLContext()
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.check_hostname = False
        self.socket = await client.connect(
            f'wss://{FACTORIO_ZONE_ENDPOINT}/ws',
            ping_interval=30,
            ping_timeout=10,
            ssl=ssl_context
        )
        while True:
            message = await self.socket.recv()
            data = json.loads(message)
            match data['type']:
                case 'visit':
                    self.visit_secret = data['secret']
                    await self.login()
                case 'options':
                    match data['name']:
                        case 'regions':
                            self.regions = data['options']
                        case 'versions':
                            self.versions = data['options']
                        case 'saves':
                            self.saves = data['options']
                            self.saves_sync = True
                case 'mods':
                    self.mods = data['mods']
                    self.mods_sync = True
                case 'idle':
                    self.running = False
                    self.launch_id = None
                    self.server_status = ServerStatus.OFFLINE
                    self.server_address = None
                case "starting":
                    self.running = True
                    self.launch_id = data.get('launchId')
                    self.server_status = ServerStatus.STARTING
                case "stopping":
                    self.running = True
                    self.launch_id = data.get('launchId')
                    self.server_status = ServerStatus.STOPPING
                case 'running':
                    self.running = True
                    self.launch_id = data.get('launchId')
                    self.server_address = data.get('socket')
                    self.server_status = ServerStatus.RUNNING
                case 'slot':
                    self.slots[data['slot']] = data

    async def wait_sync(self):
        while not self.mods_sync or not self.saves_sync:
            await asyncio.sleep(1)

    async def login(self):
        resp = requests.post(
            url=f'https://{FACTORIO_ZONE_ENDPOINT}/api/user/login',
            data={
                'userToken': self.user_token,
                'visitSecret': self.visit_secret,
                'reconnected': False
            })
        
        if resp.ok:
            body = resp.json()
            self.user_token = body['userToken']
        else:
            raise Exception(f'Error logging in: {resp.text}')

    async def start_instance(self):
        resp = requests.post(
            url=f'https://{FACTORIO_ZONE_ENDPOINT}/api/instance/start',
            data={
                'visitSecret': self.visit_secret,
                'region': self.region,
                'version': self.version,
                'save': self.save
            })
        
        if resp.status_code != 200:
            raise Exception(f'Error starting instance: {resp.text}')
        self.launch_id = resp.json()['launchId']

    async def stop_instance(self):
        resp = requests.post(
            url=f'https://{FACTORIO_ZONE_ENDPOINT}/api/instance/stop',
            data={
                'visitSecret': self.visit_secret,
                'launchId': self.launch_id
            }
        )

        if resp.status_code != 200:
            raise Exception(f'Error stopping instance: {resp.text}')
    
    async def get_instance_status(self) -> ServerStatus:
        return self.server_status