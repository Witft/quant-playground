import requests

def mock_get(url, *args, **kwargs):
    headers = kwargs.get('headers', {})
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    })
    kwargs['headers'] = headers
    
    # 强制不使用代理
    kwargs['proxies'] = {
        'http': None,
        'https': None
    }
    
    return original_get(url, *args, **kwargs)

original_get = requests.get
original_session_get = requests.Session.get

def mock_session_get(self, url, **kwargs):
    # 强制不使用代理
    kwargs['proxies'] = {
        'http': None,
        'https': None
    }
    headers = kwargs.get('headers', {})
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    kwargs['headers'] = headers
    return original_session_get(self, url, **kwargs)

requests.get = mock_get
requests.Session.get = mock_session_get
