
import json
import logging
import re
import sys
import traceback
from urllib.parse import urlparse

import requests

class CommonUser(object):
    def __init__(self, session_data: dict): 
        self.headers = session_data['header_values']
        self.params_keys = session_data['params_keys']
        self.bodys_keys = session_data['bodys_keys']
        self.urls = session_data['fn_url']
        self.params = session_data['param_values']
        self.bodys = session_data['body_values']
        self.params_as_all = session_data['params_as_all']
        self.bodys_as_all = session_data['bodys_as_all']
        self.params_encry = session_data['params_encry']
        self.bodys_encry = session_data['bodys_encry']
        self.session_id = session_data['session_id']
        self.api_ok = session_data['api_ok']
        self.urlparsed = dict()
        self.api_errors = dict()
        self.exc_info = []
        self.messages = []
        self.session = requests.Session()
        self.session.headers = self._header()


    def _header(self):
        return {
            'User-Agent': self.headers['User-Agent'],
            'user-agent': self.headers['user-agent'],
            # 'Cookie':self.headers['Cookie'],
        }

    def __urlparsed(self, url):
        if self.urlparsed.get(url):
            host, path = self.urlparsed[url]
        else:
            parse_result = urlparse(url)
            host = parse_result.netloc
            path = parse_result.path
            self.urlparsed[url] = host, path
        return host, path

    def __parse(self, url, res, p):
        result = res.text
        j = ""
        try:
            j = json.loads(result)
            app_ok_codes = self.api_ok['app_ok']# dict(str,list)

            response_key = 'nil'
            for k in app_ok_codes:
                if not j.get(k, 9999999) == 9999999:
                    response_key = k
                    break

            response_code = j.get(response_key, 9999999)

            codes_app = app_ok_codes.get(response_key, [])

            if response_code in codes_app:
                p(j)
                return result

            _, path = self.__urlparsed(url)
            codes_url = self.api_ok.get(path, {}).get(response_key,[])
            if response_code in codes_url:
                p(j)
                return result

            self.api_errors[path] = j
            logging.error(f"\033[1;31m {j} \033[0m")
        except json.JSONDecodeError:
            p(result)
        except :
            logging.error(f"\033[1;31m {j} \033[0m")
        finally:
            print()
        return result

    def _post(self, url, p=logging.warning, **kwargs):
        r"""Sends a POST request.

        :param params: (optional) Dictionary or bytes to be sent in the query
            string for the :class:`Request`.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the
            :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the
            :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: str
        """
        res = self.session.post(url, **kwargs)
        return self.__parse(url, res, p)

    def _get(self, url, p=logging.warning, **kwargs):
        res = self.session.get(url, **kwargs)
        return self.__parse(url, res, p)

    def _params_from(self, url):
        host, path = self.__urlparsed(url)
        params_keys = self.params_keys[host][path]
        return { k:v for k,v in self.params.items() if k in set(params_keys) }

    def _bodys_from(self, url):
        host, path = self.__urlparsed(url)
        params_keys = self.bodys_keys[host][path]
        return { k:v for k,v in self.bodys.items() if k in set(params_keys) }

    def message(self, m):
        self.messages.append(m)



def genRunner(user: CommonUser):
    def xxx(user):
        pass
    r = xxx
    r = yield
    while True:
        try:
            r = yield r(user)
        except StopIteration as e:
            print('StopIteration', e)
        except Exception as e:
            user.exc_info.append(sys.exc_info())
            r = yield sys.exc_info()

def framework_main(run, users):
    '''
    run: Callable, 用户要运行的代码
    users: Iterable[CommonUser]
    '''

    import asyncio

    done, _ = asyncio.run(asyncio.wait([_run_it(run, user) for user in users]))

    _report(done)
    
    
async def _run_it(run, user):
    try:
        logging.info(f"\033[1;31m{' '*20}\033[0m")
        logging.info(f"\033[1;31m{'-'*10} {user.session_id} {'-'*10}\033[0m")

        runner = genRunner(user)
        runner.send(None)

        await run(runner, user)
        
    except :
        traceback.print_exc()    
    finally:
        logging.info(f"\033[1;31m{'^'*10} {user.session_id} {'^'*10}\033[0m")
        logging.info(f"\033[1;31m{' '*20}\033[0m")

    return user

    
def _report(done):
    sessions = []
    api_errors = {}
    exc_info = {}
    messages = {}
        
    for item in done:
        user: CommonUser = item.result()
        sessions.append(user.session_id)
        api_errors[user.session_id] = user.api_errors
        exc_info[user.session_id] = user.exc_info
        messages[user.session_id] = user.messages

    for session, v in api_errors.items():
        if len(v):
            logging.info(f"\033[1;31m {session} - 有如下问题: \033[0m")
            for url, message in v.items():
                logging.info(f"\033[1;31m\t{url} - {message}\033[0m")
                print()
    print()

    for session, v in exc_info.items():
        if len(v):
            logging.info(f"\033[1;31m {session} - 有如下异常: \033[0m")
            for info in v:
                traceback.print_exception(*info, limit=None, file=None, chain=True)
                print()
    print()

    for session, v in sorted(messages.items()):
        if len(v):
            logging.info(f"\033[1;31m {session} - 有如下消息: \033[0m")
            for message in v:
                logging.info(f"\t{message}")
                print()

    logging.info(f"共运行: \033[1;31m {len(sessions)} - {sessions}\033[0m")    






