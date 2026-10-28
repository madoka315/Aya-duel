import asyncio
from io import BytesIO

from PIL import Image

import hoshino
from hoshino import R, log, aiorequests

from . import data
from .roster import UNKNOWN

logger = log.new_logger('pcr_duel.chara', hoshino.config.DEBUG)

try:
    gadget_equip = R.img('priconne/gadget/equip.png').open()
    gadget_star = R.img('priconne/gadget/star.png').open()
    gadget_star_dis = R.img('priconne/gadget/star_disabled.png').open()
    gadget_star_pink = R.img('priconne/gadget/star_pink.png').open()
    unknown_chara_icon = R.img(f'priconne/unit/icon_unit_{UNKNOWN}31.png').open()
except Exception as e:
    logger.exception(e)


def gen_team_pic(team, size=64, star_slot_verbose=True):
    num = len(team)
    des = Image.new('RGBA', (num*size, size), (255, 255, 255, 255))
    for i, chara in enumerate(team):
        src = chara.render_icon(size, star_slot_verbose)
        des.paste(src, (i * size, 0), src)
    return des


async def download_chara_icon(id_, star):
    url = f'https://redive.estertion.win/icon/unit/{id_}{star}1.webp'
    save_path = R.img(f'priconne/unit/icon_unit_{id_}{star}1.png').path
    logger.info(f'Downloading chara icon from {url}')
    try:
        rsp = await aiorequests.get(url, stream=True, timeout=5)
        if 200 == rsp.status_code:
            img = Image.open(BytesIO(await rsp.content))
            img.save(save_path)
            logger.info(f'Saved to {save_path}')
        else:
            logger.error(f'Failed to download {url}. HTTP {rsp.status_code}')
    except Exception as e:
        logger.error(f'Failed to download {url}. {type(e)}')
        logger.exception(e)


def _schedule_download(id_):
    """缺失头像时后台补图，绝不阻塞事件循环"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    async def _dl():
        await asyncio.gather(
            download_chara_icon(id_, 6),
            download_chara_icon(id_, 3),
            download_chara_icon(id_, 1),
        )
    loop.create_task(_dl())


class Chara:

    def __init__(self, id_, star=0, equip=0):
        self.id = id_
        self.star = star
        self.equip = equip

    @property
    def name(self):
        return data.CHARA_NAME[self.id][0] if self.id in data.CHARA_NAME else data.CHARA_NAME[UNKNOWN][0]

    @property
    def icon(self):
        star = '3' if 1 <= self.star <= 5 else '6'
        res = R.img(f'priconne/unit/icon_unit_{self.id}{star}1.png')
        if not res.exist:
            res = R.img(f'priconne/unit/icon_unit_{self.id}31.png')
        if not res.exist:
            res = R.img(f'priconne/unit/icon_unit_{self.id}11.png')
        if not res.exist:
            _schedule_download(self.id)
            res = R.img(f'priconne/unit/icon_unit_{UNKNOWN}31.png')
        return res

    def render_icon(self, size, star_slot_verbose=True) -> Image:
        try:
            pic = self.icon.open().convert('RGBA').resize((size, size), Image.LANCZOS)
        except FileNotFoundError:
            logger.error(f'File not found: {self.icon.path}')
            pic = unknown_chara_icon.convert('RGBA').resize((size, size), Image.LANCZOS)

        l = size // 6
        star_lap = round(l * 0.15)
        margin_x = (size - 6*l) // 2
        margin_y = round(size * 0.05)
        if self.star:
            for i in range(5 if star_slot_verbose else min(self.star, 5)):
                a = i*(l-star_lap) + margin_x
                b = size - l - margin_y
                s = gadget_star if self.star > i else gadget_star_dis
                s = s.resize((l, l), Image.LANCZOS)
                pic.paste(s, (a, b, a+l, b+l), s)
            if 6 == self.star:
                a = 5*(l-star_lap) + margin_x
                b = size - l - margin_y
                s = gadget_star_pink
                s = s.resize((l, l), Image.LANCZOS)
                pic.paste(s, (a, b, a+l, b+l), s)
        if self.equip:
            l = round(l * 1.5)
            a = margin_x
            b = margin_x
            s = gadget_equip.resize((l, l), Image.LANCZOS)
            pic.paste(s, (a, b, a+l, b+l), s)
        return pic
