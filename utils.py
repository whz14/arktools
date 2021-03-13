# encoding='utf-8'
import requests
import re
import time
import copy
from bs4 import BeautifulSoup
from collections import defaultdict

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
WIKI_PREFIX = 'http://prts.wiki/w/'
T5_MATERIAL = ['D32钢', '双极纳米片', '聚合剂', '晶体电子单元']
T4_MATERIAL = ['白马醇', '三水锰矿', '五水研磨石', 'RMA70-24', '提纯源岩', '改量装置', '聚酸酯块', '糖聚块', '异铁块',
               '酮阵列', '聚合凝胶', '炽合金块', '晶体电路']
T3_MATERIAL = ['扭转醇', '轻锰矿', '研磨石', 'RMA70-12', '固源岩组', '全新装置', '聚酸酯组', '糖组', '异铁组', '酮凝集组',
               '凝胶', '炽合金', '晶体元件', '技巧概要·卷3']
OWNED = {'D32钢': 6, '双极纳米片': 0, '聚合剂': 4,
         '白马醇': 6, '扭转醇': 0, '三水锰矿': 3, '轻锰矿': 25, '五水研磨石': 8, '研磨石': 25, 'RMA70-24': 17, 'RMA70-12': 0,
         '提纯源岩': 6, '固源岩组': 16, '改量装置': 3, '全新装置': 3, '聚酸酯块': 3, '聚酸酯组': 62, '糖聚块': 4, '糖组': 15,
         '异铁块': 12, '异铁组': 8, '酮阵列': 9, '酮凝集组': 12, '聚合凝胶': 1, '凝胶': 6, '炽合金块': 7, '炽合金': 106,
         '晶体电子单元': 4, '晶体电路': 0, '晶体元件': 25,
         '技巧概要·卷3': 9}
memory = {}


def master_material(op_name):
    """
    given operator's name, return materials his or her skill mastering needs
    :param op_name: name of operator, in Chinese, e.g. '阿米娅', '阿米娅(近卫)'
    :return: list of length 1, 2 or 3
    """
    if op_name in memory:
        return memory[op_name]
    r = requests.get(WIKI_PREFIX + op_name)
    while r.status_code != 200:
        print('http get failed:', r.status_code)
        r = requests.get(WIKI_PREFIX + op_name)
        time.sleep(10)
    soup = BeautifulSoup(r.content, features='html.parser')
    # skill_t is a soup object, `tag`
    skill_t = soup.find_all(text=re.compile('达到精英阶段2后解锁'))[-1].parent.parent.parent
    # a list of lists of soup object, rank_table[rank][skill]
    rank_table = [skill_t.find_all(text=re.compile('等级' + str(x))) for x in range(1, 4)]
    # skill_table[skill][master_rank] is the soup object
    skill_table = [[rank[skill].parent.next_sibling.next_sibling for rank in rank_table]
                   for skill in range(len(rank_table[0]))]
    memory[op_name] = [[{a['title']: int(a.next_sibling.string) for a in rank.find_all('a')}
                        for rank in skill] for skill in skill_table]
    return memory[op_name]


def material_compound(material):
    """
    given a purple or gold material, try to decompose it to blue ones
    :param material: standard name of material in Chinese, e.g. '双极纳米片', '五水研磨石'
    :return:
    """
    if material in T3_MATERIAL:
        return {material: 1}
    if material in memory:
        return memory[material]
    r = requests.get(WIKI_PREFIX + material)
    while r.status_code != 200:
        print('requests get failed', r.status_code)
        time.sleep(10)
        r = requests.get(WIKI_PREFIX + material)
    soup = BeautifulSoup(r.content, features='html.parser')
    table = soup.find(text=re.compile('副产物'))
    lines = table.parent.parent.parent.find_all('tr')
    composition_tag = lines[1]
    re0 = {a['title']: int(a.next_sibling.string) for a in composition_tag.find_all('a')}
    # print('{0} needs {1}'.format(material, re0))
    ret = defaultdict(int)
    for mat, num in re0.items():
        p_ret = material_compound(mat)
        for p_ma, p_num in p_ret.items():
            ret[p_ma] += num * p_num
    memory[material] = ret
    return memory[material]


def op_master_material(op_skills):
    """
    calculate materials needed for operators. will NOT decompose the high lv materials into t3 materials
    :param op_skills:
    :return:
    """
    # left = copy.deepcopy(owned)
    needed = defaultdict(int)
    for operator, skills in op_skills.items():
        # op_ret = defaultdict(int)
        materials = master_material(operator)
        for skill, rank in skills.items():
            if isinstance(rank, int):
                target_rank = rank
                present_rank = 1
            else:
                target_rank, present_rank = rank
            for mat_dict in materials[skill - 1][present_rank: target_rank]:
                for mat, num in mat_dict.items():
                    needed[mat] += num
    return dict(needed)


def op_master_needed(op_skills, owned=None):
    """
    in t3 materials.
    :param op_skills:
    :param owned:
    :return:
    """
    needed = op_master_material(op_skills)
    left = copy.deepcopy(owned)
    if left:
        for m in needed:
            needed[m], left[m] = max(0, needed[m] - owned[m]), max(0, owned[m] - needed[m])
    t3_needed = defaultdict(int)
    for m, n in needed.items():
        t3_mats = material_compound(m)
        for t3m, t3n in t3_mats.items():
            t3_needed[t3m] += n * t3n
    if left:
        for m in t3_needed:
            t3_needed[m] = max(0, t3_needed[m] - left[m])
        return dict(t3_needed), left
    else:
        return dict(t3_needed)


if __name__ == '__main__':
    print('testing utils.py')
    # print(material_compound('晶体电子单元'))
    # print(material_compound('D32钢'))
    # print(material_compound('双极纳米片'))
    # print(material_compound('聚合剂'))
    # print(master_material('白面鸮'))
    # print(master_material('阿米娅'))
    # print(master_material('阿米娅(近卫)'))
    # print(op_master_mater({'能天使': {3: (3, 2)}}))
    # print(op_master_mater({'塞雷娅': {1: (3, 1), 2: (3, 1)}}))
    # print(op_master_mater({'白面鸮': {2: (3, 2)}}))
    # print(op_master_mater({'夜莺': {3: 3}}))
    # print(op_master_mater({'能天使': {3: (3, 2)},
    #                        '塞雷娅': {1: (3, 1), 2: (3, 1)},
    #                        '白面鸮': {2: (3, 2)},
    #                        '夜莺': {3: 3}}))
    # print(op_master_material({'能天使': {3: (3, 2)},
    #                           '塞雷娅': {1: (3, 1), 2: (3, 1)},
    #                           '白面鸮': {2: (3, 1)},
    #                           '夜莺': {3: 3}}))
    # print(op_master_needed({'能天使': {3: (3, 2)},
    #                         '塞雷娅': {1: (3, 1), 2: (3, 1)},
    #                         '白面鸮': {2: (3, 1)},
    #                         '夜莺': {3: 3}}))
    # print(op_master_needed({'能天使': {3: (3, 2)},
    #                         '塞雷娅': {1: (3, 1), 2: (3, 1)},
    #                         '白面鸮': {2: (3, 1)},
    #                         '夜莺': {3: 3}}, OWNED))
    # print(t3_owned)
