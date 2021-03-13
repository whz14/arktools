from utils import op_master_needed
from configparser import ConfigParser
import re


def get_owned_material():
    cfg = ConfigParser()
    cfg.optionxform = lambda option: option
    cfg.read('data/owned.ini', encoding='utf8')
    owned_mt = {}
    for k in cfg['DEFAULT']:
        owned_mt[k] = cfg['DEFAULT'].getint(k)
    return owned_mt


def get_opskills():
    cfg = ConfigParser()
    cfg.optionxform = lambda option: option
    cfg.read('data/master_rank.ini', encoding='utf8')
    op_skills = {}
    for operator in cfg:
        if operator == 'DEFAULT':
            continue
        tmp = dict(cfg[operator])
        op_skills[operator] = {int(re.findall(r'\d+', skill)[0]): eval(rank) for skill, rank in tmp.items()}
    return op_skills


if __name__ == '__main__':
    owned = get_owned_material()
    opsk = get_opskills()
    needed, left = op_master_needed(opsk, owned)
    print('还需刷取材料（以蓝材料计）')
    for k, v in needed.items():
        print(k, ': ', v)
    print('结束后还剩材料（以蓝材料计）')
    for k, v in left.items():
        print(k, ': ', v)
