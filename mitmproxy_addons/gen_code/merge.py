import pathlib
import os.path
import json
import re
import time
import pprint
from urllib.parse import urlparse
import logging
import itertools
import collections
import importlib
import traceback

from jinja2 import Template
from jinja2 import Environment, FileSystemLoader


def import_module(path: pathlib.Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(path.stem,str(path))
    session_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(session_module)
    return session_module

def get_data(session_module, var_name):
    old_data = dict()
    try:
        old_data = getattr(session_module, var_name)
    except Exception as e:
        # traceback.print_exc()
        pass
    return old_data

def remove_unnecessary_headers(headers):
    h = {
        ':authority', 'accept', 'accept-language', 'accept-encoding', 
        'connection', 'content-encoding', 'content-length', 'content-type', 'cache-control', 
        'host', 'pragma', 'proxy-connection',
    }
    for key in h:
        try:
            headers.pop(key.upper(), None)
            headers.pop(key.lower(), None)
            headers.pop(key.title(), None)
        except:
            pass

def remove_unnecessary_and_print_missing(exist_values, all_values):
    p_keys_all = set()
    for k, v in all_values.items():
        for kk, vv in v.items():
            p_keys_all |= set(vv)

    p_keys_exist = set(exist_values.keys())

    # 删除多余的值
    no_need_keys = p_keys_exist - p_keys_all
    for k in no_need_keys:
        del exist_values[k]

    # 打印缺失的值
    pprint.pprint('缺失：')
    pprint.pprint(p_keys_all - p_keys_exist)

def missing(p_keys_exist, p_keys_all) -> set:
    return set(p_keys_all - p_keys_exist)

def add_missing(from_values, to_values):
    p_keys_exist = set(from_values.keys())
    p_keys_all = set(to_values.keys())

    miss = missing(p_keys_all, p_keys_exist)
    for k in miss:
        to_values[k] = from_values[k]

def add_missing_level2(from_values, to_values):
    p_keys_exist = set(from_values.keys())
    p_keys_all = set(to_values.keys())

    common = p_keys_all & p_keys_exist
    for k in common:
        add_missing(from_values[k], to_values[k])

def update_values_level2(from_values, to_values):
    p_keys_exist = set(from_values.keys())
    p_keys_all = set(to_values.keys())    

    common = p_keys_all & p_keys_exist
    for k in common:
        to_values[k].update(from_values[k])
    

env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))

def gen_file_from_jinja2(tfile, gfile, **kwargs):
    t = env.get_template(tfile)
    ss = t.render(**kwargs)
    with open(gfile, mode='w') as ff:
        ff.write(ss)

class AppSession():
    keys = [
        'header_values', 'fn_url', 'api_ok', 
        'params_keys', 'bodys_keys', 
        'param_values', 'body_values', 
        'params_as_all', 'bodys_as_all',
        'params_encry', 'bodys_encry', 
    ]

    keys_level2 = [
        'params_keys', 'bodys_keys', 
        'params_encry', 'bodys_encry', 
    ]

    keys_u_level2 = [
        'params_keys', 'bodys_keys',  
    ]

    keys_u_level1 = [
        'header_values', 'fn_url', 'param_values', 'body_values',        
    ]

    keys_a_diff = [
        'fn_url', 'params_keys', 'bodys_keys', 'api_ok'
    ]

    keys_a_level2_diff = [
        'params_keys', 'bodys_keys',
    ]

    def __init__(self, path):
        self.file = path
        if self.file.exists():
            self.session_module = import_module(path)
            self.session_id = get_data(self.session_module, 'session_id')
            self.api_ok = get_data(self.session_module, 'api_ok')
            self.header_values = get_data(self.session_module, 'header_values')
            self.fn_url = get_data(self.session_module, 'fn_url')
            self.params_keys = get_data(self.session_module, 'params_keys')
            self.bodys_keys = get_data(self.session_module, 'bodys_keys')
            self.param_values = get_data(self.session_module, 'param_values')
            self.body_values = get_data(self.session_module, 'body_values')
            self.params_as_all = get_data(self.session_module, 'params_as_all')
            self.bodys_as_all = get_data(self.session_module, 'bodys_as_all')
            self.params_encry = get_data(self.session_module, 'params_encry')
            self.bodys_encry = get_data(self.session_module, 'bodys_encry')
            self.session_data = get_data(self.session_module, 'session_data')
        pass

    def format(self):
        remove_unnecessary_headers(self.header_values)
        remove_unnecessary_and_print_missing(self.param_values, self.params_keys)
        remove_unnecessary_and_print_missing(self.body_values, self.bodys_keys)

    def delelte(self):
        '''
        fn_url中没有对应的URL时，删除params_keys, bodys_keys中对应的值
        '''
        u = {}
        for _, url in self.fn_url.items():
            o = urlparse(url)
            s = u.setdefault(o.netloc, set())
            s.add(o.path)

        uks = set(u.keys())
        for field in [self.params_keys, self.bodys_keys]:
            fks = set(field.keys())

            no_need_keys = fks - uks
            for k in no_need_keys:
                del field[k]

            common = fks & uks
            for netloc in common:
                pks = set(field[netloc].keys())
                hks = set(u[netloc]) 
                no_need_keys = pks - hks
                for k in no_need_keys:
                    del field[netloc][k]   



    def save_as_file(self, name='', inplace=False):
        var_dict = dict()
        var_dict['session_id'] = f'{self.session_id!r}'

        var_dict['header_values'] = json.dumps(self.header_values, indent=2, sort_keys=True)
        var_dict['fn_url'] = json.dumps(self.fn_url, indent=2, sort_keys=True)
        var_dict['params_keys'] = json.dumps(self.params_keys, indent=2, sort_keys=True)
        var_dict['bodys_keys'] = json.dumps(self.bodys_keys, indent=2, sort_keys=True)
        var_dict['param_values'] = json.dumps(self.param_values, indent=2, sort_keys=True)
        var_dict['body_values'] = json.dumps(self.body_values, indent=2, sort_keys=True)
        var_dict['params_as_all'] = json.dumps(self.params_as_all, indent=2, sort_keys=True)
        var_dict['bodys_as_all'] = json.dumps(self.bodys_as_all, indent=2, sort_keys=True)
        var_dict['params_encry'] = json.dumps(self.params_encry, indent=2, sort_keys=True)
        var_dict['bodys_encry'] = json.dumps(self.bodys_encry, indent=2, sort_keys=True)
        var_dict['api_ok'] = json.dumps(self.api_ok, indent=2, sort_keys=True)


        tfile = f'session_xxx.j2.py'
        if inplace:
            gfile = self.file
        else:
            gfile = self.file.parent/f'session_{self.session_id}_{name}.py' 
        gen_file_from_jinja2(tfile, gfile, seq=var_dict)
        pass

class MergerSession():
    def __init__(self, from_session: AppSession, to_seession: AppSession):
        self.from_session = from_session
        self.to_seession = to_seession

    def merge(self, o=('a','u')):
        '''
        cuda:create, update, delete, append
        '''
        if 'u' in o:
            self.update_values()

        if 'a' in o:
            self.add_missing()



    def save_as_file(self, inplace=False):
        self.to_seession.save_as_file('merge', inplace=inplace)

    def add_missing(self):
        if self.to_seession.file.exists():
            if self.to_seession.file.name == self.from_session.file.name:
                level_1_keys, level_2_keys = AppSession.keys, AppSession.keys_level2
            else:
                level_1_keys, level_2_keys = AppSession.keys_a_diff, AppSession.keys_a_level2_diff

            self._add_missing(level_1_keys, level_2_keys)
        else:
            self.to_seession = AppSession(self.from_session.file)
            self.to_seession.file = pathlib.Path(re.sub('/api/', '/dev/', str(self.from_session.file)))
            pass

    def _add_missing(self, level_1_keys, level_2_keys):
        for k in level_1_keys:
            from_v = getattr(self.from_session, k)
            to_v = getattr(self.to_seession, k)
            add_missing(from_v, to_v)

        for k in level_2_keys:
            from_v = getattr(self.from_session, k)
            to_v = getattr(self.to_seession, k)
            add_missing_level2(from_v, to_v)

    def update_values(self):
        for k in AppSession.keys_u_level1:
            from_v = getattr(self.from_session, k)
            to_v = getattr(self.to_seession, k)
            to_v.update(from_v)

        for k in AppSession.keys_u_level2:
            from_v = getattr(self.from_session, k)
            to_v = getattr(self.to_seession, k)
            update_values_level2(from_v, to_v)
            


def main_merge_all(api_dir: str, dev_dir: str):
    '''
    场景：目录级内所有对应session合并
    '''

    api_dir = pathlib.Path(api_dir)
    dev_dir = pathlib.Path(dev_dir)

    r = re.compile(r'session_[a-zA-Z]+\.py')
    target = api_dir.glob(r'*/session_huawei.py')
    target = [item for item in target if r.match(item.name)] 
    for item in sorted(target):
        part_path = item.relative_to(api_dir)
        to_file: pathlib.Path = dev_dir / part_path
        if to_file.exists():
            print(part_path)
            from_session = AppSession(item)
            to_seession = AppSession(to_file)

            merge_tool = MergerSession(from_session, to_seession)
            merge_tool.merge()
            merge_tool.save_as_file() 


def main_merge_new_added_apis(from_path: str):
    '''
    场景：有新增的接口录入时
    操作：1. 合并到同名的session, 2. 并合并非同名session
    '''

    # 1：同名session从api同步到dev
    sessions = helper_gen_from_and_to_appsessions(from_path)

    merge_tool = MergerSession(*sessions)
    merge_tool.merge()
    merge_tool.save_as_file(inplace=True)


    # 2. 并合并非同名session并
    main_merge_to_other_session(from_path)
    pass

def main_merge_to_other_session(from_path: str):
    '''
    场景：从一个session合并到其它session
    操作：只合并键，比如urls,params_keys,body_keys，不能合并值 
    '''

    from_file = pathlib.Path(from_path)
    name = from_file.name 

    if '/dev/' in from_path:
        folder = from_file.parent

    if '/api/' in from_path:
        temp = re.sub('/api/', '/dev/', from_path)
        folder = pathlib.Path(temp).parent 

    print(folder, name)

    from_session = AppSession(from_file)

    r = re.compile(r'session_[a-zA-Z]+\.py')
    target = folder.glob(r'session_*.py')
    target = [item for item in target if r.match(item.name)] 
    target = [item for item in target if not from_file.samefile(item)] 
    for item in sorted(target):
        print(f'{name} -> {item.name}')        
        to_seession = AppSession(item)

        merge_tool = MergerSession(from_session, to_seession)
        merge_tool.merge(o=('a'))
        merge_tool.save_as_file(inplace=True)    


def helper_gen_from_and_to_appsessions(from_or_to_path: str):
    if '/api/' in from_or_to_path:
        fp = from_or_to_path
        tp = re.sub('/api/', '/dev/', from_or_to_path)
    else:
        tp = from_or_to_path    
        fp = re.sub('/dev/', '/api/', from_or_to_path)
    
        
    from_file = pathlib.Path(fp)
    from_session = AppSession(from_file)

    to_file = pathlib.Path(tp)
    to_seession = AppSession(to_file)    

    return from_session, to_seession



if __name__ == "__main__":

    # 场景：删除
    from_path = pathlib.Path('/Users/zhoujie/Documents/heroku/jason903/auto_app/qu-tou-tiao/session_xsy.py') 
    from_session = AppSession(from_path)
    from_session.delelte()
    from_session.save_as_file()
    exit()


    # 场景：全部合并
    # api_dir = '/Users/zhoujie/Desktop/api'
    # dev_dir = '/Users/zhoujie/Desktop/dev'
    # main_merge_all(api_dir, dev_dir)
    # exit()

    # 方法一
    # from_file = pathlib.Path(f'/Users/zhoujie/Desktop/api/qu-tou-tiao/session_csh.py')
    # from_session = AppSession(from_file)

    # to_file = pathlib.Path(f'/Users/zhoujie/Desktop/dev/qu-tou-tiao/session_csh.py')
    # to_seession = AppSession(to_file)
    # merge_tool = MergerSession(*sessions)

    from_path = '/Users/zhoujie/Desktop/api/qu-tou-tiao/session_xiaomi.py'

    # 场景：同名session从api同步到dev
    sessions = helper_gen_from_and_to_appsessions(from_path)

    merge_tool = MergerSession(*sessions)
    merge_tool.merge()
    merge_tool.save_as_file(inplace=True)


    # 场景：不同session之间合并
    # from_path = '/Users/zhoujie/Desktop/dev/qu-tou-tiao/session_huawei.py' 
    main_merge_to_other_session(from_path)

    print('done!!!')



    pass
