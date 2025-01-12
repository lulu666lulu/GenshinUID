from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv
from .draw_event_img import get_event_img, get_all_event_img
from ..utils.draw_image_tools.send_image_tool import convert_img


@sv.scheduled_job('cron', hour='2')
async def draw_event():
    await get_all_event_img()


@sv.on_fullmatch('活动列表')
async def send_events(bot: HoshinoBot, ev: CQEvent):
    img = await get_event_img('EVENT')
    im = await convert_img(img)
    await bot.send(ev, im)


@sv.on_fullmatch('卡池列表')
async def send_gachas(bot: HoshinoBot, ev: CQEvent):
    img = await get_event_img('GACHA')
    im = await convert_img(img)
    await bot.send(ev, im)
