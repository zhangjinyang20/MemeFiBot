import argparse
import asyncio
import glob
import json
import os

from better_proxy import Proxy
from pyrogram import Client

from bot.config import settings
from bot.core.registrator import register_sessions
from bot.core.tapper import run_tapper
from bot.utils import logger

start_text = """

░█▀▄▀█ █▀▀ █▀▄▀█ █▀▀ ░█▀▀▀  ▀  ░█▀▀█ █▀▀█ ▀▀█▀▀ 
░█░█░█ █▀▀ █ ▀ █ █▀▀ ░█▀▀▀ ▀█▀ ░█▀▀▄ █  █   █ 
░█  ░█ ▀▀▀ ▀   ▀ ▀▀▀ ░█    ▀▀▀ ░█▄▄█ ▀▀▀▀   ▀

Select an action:

    1. Create session
    2. Run clicker
"""


def get_session_names() -> list[str]:
    session_names = glob.glob('sessions/*.session')
    session_names = [os.path.splitext(os.path.basename(file))[0] for file in session_names]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file='bot/config/proxies.txt', encoding='utf-8-sig') as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir='sessions/',
        plugins=dict(root='bot/plugins')
    ) for session_name in session_names]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, help='Action to perform')

    logger.info(f"Detected {len(get_session_names())} sessions")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ['1', '2']:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)


def get_pro() -> dict:
    with open('bot/config/proxies.json', 'r') as file:
        data = json.load(file)
    return data


def get_proxie(di) -> str:
    if settings.USE_PROXY_FROM_FILE:
        return Proxy.from_str(proxy=di).as_url


async def run_tasks(tg_clients: list[Client]):
    pro = get_pro()
    tasks = []
    for tg_client in tg_clients:
        tasks.append(asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=get_proxie(pro[tg_client.name.strip()]),
            )
        ))
    await asyncio.gather(*tasks)
