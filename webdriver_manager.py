# webdriver_manager.py
from selenium import webdriver
import os
import logging
from config import Config
from proxy_manager import ProxyManager

class WebDriverManager:
    proxy_manager = ProxyManager()

    @staticmethod
    def create_proxy_plugin(proxy_config):
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            }
        }
        """

        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy_config['host']}",
                    port: parseInt("{proxy_config['port']}")
                }}
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_config['username']}",
                    password: "{proxy_config['password']}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """

        plugin_dir = 'proxy_auth_plugin'
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)

        with open(f'{plugin_dir}/manifest.json', 'w') as f:
            f.write(manifest_json)

        with open(f'{plugin_dir}/background.js', 'w') as f:
            f.write(background_js)

        return os.path.abspath(plugin_dir)

    @staticmethod
    def get_driver():
        proxy_config = WebDriverManager.proxy_manager.get_next_proxy()
        options = webdriver.ChromeOptions()
        plugin_path = WebDriverManager.create_proxy_plugin(proxy_config)
        
        options.add_argument(f'--load-extension={plugin_path}')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-notifications')
        
        driver = webdriver.Chrome(options=options)
        proxy_string = f"{proxy_config['host']}:{proxy_config['port']}"
        
        logging.info(f'WebDriver setup complete with proxy: {proxy_string}')
        return driver, proxy_string