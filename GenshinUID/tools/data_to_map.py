import sys
import json
import asyncio
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).parents[5]))
sys.path.append(str(Path(__file__).parents[2]))

__package__ = 'GenshinUID.tools'
from gsuid_core.utils.api.ambr.request import (  # noqa: E402
    get_ambr_monster_data,
    get_ambr_monster_list,
)

from ..version import Genshin_version  # noqa: E402
from ..utils.ambr_to_minigg import convert_ambr_to_minigg  # noqa: E402

R_PATH = Path(__file__).parents[0]
MAP_PATH = Path(__file__).parents[1] / 'utils' / 'map' / 'data'
DATA_PATH = R_PATH / 'gs_data'
WEAPON_TYPE = {
    'WEAPON_POLE': '长柄武器',
    'WEAPON_BOW': '弓',
    'WEAPON_SWORD_ONE_HAND': '单手剑',
    'WEAPON_CLAYMORE': '双手剑',
    'WEAPON_CATALYST': '法器',
}

version = Genshin_version
raw_data = {}

avatarName2Element_fileName = f'avatarName2Element_mapping_{version}.json'
weaponHash2Name_fileName = f'weaponHash2Name_mapping_{version}.json'
weaponHash2Type_fileName = f'weaponHash2Type_mapping_{version}.json'
skillId2Name_fileName = f'skillId2Name_mapping_{version}.json'
talentId2Name_fileName = f'talentId2Name_mapping_{version}.json'
avatarId2Name_fileName = f'avatarId2Name_mapping_{version}.json'
enName2Id_fileName = f'enName2AvatarID_mapping_{version}.json'
avatarId2Star_fileName = f'avatarId2Star_mapping_{version}.json'
avatarName2Weapon_fileName = f'avatarName2Weapon_mapping_{version}.json'

monster2entry_fileName = f'monster2entry_mapping_{version}.json'

artifact2attr_fileName = f'artifact2attr_mapping_{version}.json'
icon2Name_fileName = f'icon2Name_mapping_{version}.json'


BETA_CHAR = {
    '10000078': '艾尔海森',
    '10000077': '瑶瑶',
    '10000079': '迪希雅',
    '10000080': '米卡',
    '10000081': '卡维',
    '10000082': '白术',
    '10000061': '绮良良',
    '10000083': '琳妮特',
    '10000084': '林尼',
    '10000085': '菲米尼',
    '10000086': '莱欧斯利',
    '10000087': '那维莱特',
    '10000088': '夏洛蒂',
    '10000089': '芙宁娜',
}


async def monster2map():
    monster_list = await get_ambr_monster_list()
    result = {}
    if monster_list:
        for monster_main_id in monster_list['items']:
            if not monster_main_id.startswith('28'):
                data = await get_ambr_monster_data(monster_main_id)
                if data:
                    for entry_id in data['entries']:
                        entry: dict = data['entries'][entry_id]  # type: ignore
                        entry['name'] = data['name']
                        entry['route'] = data['route']
                        entry['icon'] = data['icon']
                        result[entry_id] = entry
    with open(MAP_PATH / monster2entry_fileName, 'w', encoding='UTF-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


async def download_new_file():
    base_url = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master'
    url_list = [
        f'{base_url}/ExcelBinOutput/AvatarExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/WeaponExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/AvatarSkillExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/AvatarTalentExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/ReliquaryExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/DisplayItemExcelConfigData.json',
        f'{base_url}/TextMap/TextMapCHS.json',
    ]

    async with httpx.AsyncClient() as client:
        for url in url_list:
            file_name = url.split('/')[-1]
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                with open(DATA_PATH / file_name, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f'文件已成功下载并保存为{DATA_PATH / file_name}')
            else:
                print(f'下载失败，状态码为{response.status_code}')


async def avatarId2NameJson() -> None:
    with open(
        DATA_PATH / 'AvatarExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        avatar_data = json.load(f)

    temp = {}
    for i in avatar_data:
        temp[str(i['id'])] = raw_data[str(i['nameTextMapHash'])]

    for _id in BETA_CHAR:
        temp[_id] = BETA_CHAR[_id]

    result = {}
    for _id in temp:
        if int(_id) >= 11000000:
            continue
        else:
            result[_id] = temp[_id]

    with open(
        MAP_PATH / avatarId2Name_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(result, file, ensure_ascii=False)


async def avatarName2ElementJson() -> None:
    with open(MAP_PATH / avatarId2Name_fileName, 'r', encoding='UTF-8') as f:
        avatarId2Name = json.load(f)

    temp = {}
    enName2Id_result = {}
    avatarId2Star_result = {}
    avatarName2Weapon_result = {}
    elementMap = {
        '风': 'Anemo',
        '岩': 'Geo',
        '草': 'Dendro',
        '火': 'Pyro',
        '水': 'Hydro',
        '冰': 'Cryo',
        '雷': 'Electro',
    }
    for _id in avatarId2Name:
        print(_id)
        if _id in ['10000005', '10000007'] or int(_id) >= 11000000:
            continue
        name = avatarId2Name[_id]
        data = httpx.get(
            f'https://info.minigg.cn/characters?query={name}'
        ).json()
        if 'retcode' in data:
            data = await convert_ambr_to_minigg(_id)
        if data is not None and 'code' not in data:
            temp[name] = elementMap[data['element']]
            try:
                nameicon = data['images']['namesideicon']  # type: ignore
                enName = nameicon.split('_')[-1]
                enName2Id_result[enName] = _id
                avatarId2Star_result[int(_id)] = str(data['rarity'])
                avatarName2Weapon_result[data['name']] = data['weapontype']
            except:  # noqa: E722
                adata = httpx.get(
                    f'https://api.ambr.top/v2/chs/avatar/{_id}?vh=40F8'
                ).json()
                adata = adata['data']
                enName = adata['route']
                enName2Id_result[enName] = _id
                avatarId2Star_result[int(_id)] = str(adata['rank'])
                avatarName2Weapon_result[data['name']] = WEAPON_TYPE[
                    adata['weaponType']
                ]

    avatarId2Star_result['10000005'] = '5'
    avatarId2Star_result['10000007'] = '5'
    avatarName2Weapon_result['旅行者'] = '单手剑'

    with open(MAP_PATH / enName2Id_fileName, 'w', encoding='UTF-8') as file:
        json.dump(enName2Id_result, file, ensure_ascii=False)

    with open(
        MAP_PATH / avatarId2Star_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(avatarId2Star_result, file, ensure_ascii=False)

    with open(
        MAP_PATH / avatarName2Element_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)

    with open(
        MAP_PATH / avatarName2Weapon_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(avatarName2Weapon_result, file, ensure_ascii=False)


async def weaponHash2NameJson() -> None:
    with open(
        DATA_PATH / 'WeaponExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        weapon_data = json.load(f)
    temp = {
        str(i['nameTextMapHash']): raw_data[str(i['nameTextMapHash'])]
        for i in weapon_data
        if str(i['nameTextMapHash']) in raw_data
    }

    with open(
        MAP_PATH / weaponHash2Name_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)


async def weaponHash2TypeJson() -> None:
    with open(
        DATA_PATH / 'WeaponExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        weapon_data = json.load(f)
    temp = {
        str(i['nameTextMapHash']): WEAPON_TYPE.get(i['weaponType'], '')
        for i in weapon_data
    }

    with open(
        MAP_PATH / weaponHash2Type_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)


async def skillId2NameJson() -> None:
    with open(
        DATA_PATH / 'AvatarSkillExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        skill_data = json.load(f)

    temp = {'Name': {}, 'Icon': {}}
    for i in skill_data:
        if str(i['nameTextMapHash']) in raw_data:
            temp['Name'][str(i['id'])] = raw_data[str(i['nameTextMapHash'])]
            temp['Icon'][str(i['id'])] = i['skillIcon']

    with open(MAP_PATH / skillId2Name_fileName, 'w', encoding='UTF-8') as file:
        json.dump(temp, file, ensure_ascii=False)


async def talentId2NameJson() -> None:
    with open(
        DATA_PATH / 'AvatarTalentExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        talent_data = json.load(f)

    temp = {'Name': {}, 'Icon': {}}
    for i in talent_data:
        temp['Name'][str(i['talentId'])] = raw_data[str(i['nameTextMapHash'])]
        temp['Icon'][str(i['talentId'])] = i['icon']

    with open(
        MAP_PATH / talentId2Name_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)


async def artifact2attrJson() -> None:
    with open(
        DATA_PATH / 'ReliquaryExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        reliquary_data = json.load(f)

    with open(
        DATA_PATH / 'DisplayItemExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        Display_data = json.load(f)

    temp = {}
    for i in reliquary_data:
        temp[str(i['icon'])] = raw_data[str(i['nameTextMapHash'])]

    temp['UI_RelicIcon_10001_1'] = '异国之盏'
    temp['UI_RelicIcon_10001_2'] = '归乡之羽'
    temp['UI_RelicIcon_10001_3'] = '感别之冠'
    temp['UI_RelicIcon_10001_4'] = '故人之心'
    temp['UI_RelicIcon_10001_5'] = '逐光之石'
    with open(MAP_PATH / icon2Name_fileName, 'w', encoding='UTF-8') as file:
        json.dump(temp, file, ensure_ascii=False)

    temp2 = {}
    for i in Display_data:
        if i['icon'].startswith('UI_RelicIcon'):
            temp2[raw_data[str(i['nameTextMapHash'])]] = '_'.join(
                i['icon'].split('_')[:-1]
            )

    temp3 = {}
    for i in temp:
        for k in temp2:
            if i.startswith(temp2[k]):
                temp3[temp[i]] = k

    temp3['异国之盏'] = '行者之心'
    temp3['归乡之羽'] = '行者之心'
    temp3['感别之冠'] = '行者之心'
    temp3['故人之心'] = '行者之心'
    temp3['逐光之石'] = '行者之心'

    with open(
        MAP_PATH / artifact2attr_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp3, file, ensure_ascii=False)


async def main():
    await monster2map()
    '''
    await download_new_file()
    global raw_data
    try:
        with open(DATA_PATH / 'TextMapCHS.json', 'r', encoding='UTF-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        pass
    await avatarId2NameJson()
    await avatarName2ElementJson()
    await weaponHash2NameJson()
    await skillId2NameJson()
    await talentId2NameJson()
    await weaponHash2TypeJson()
    await artifact2attrJson()
    '''


asyncio.run(main())
