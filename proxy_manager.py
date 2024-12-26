# proxy_manager.py
import logging
from config import Config

class ProxyManager:
    def __init__(self):
        # List of proxy IPs that use the same port, username, and password
        self.proxy_ips = [
            "proxy1.proxy.com",
            "proxy2.proxy.com",
            "proxy3.proxy.com",
            "proxy4.proxy.com",
            "proxy5.proxy.com",
            # Add more proxy IPs here
        ]
        self.current_index = 0
        logging.info('ProxyManager initialized')

    def get_next_proxy(self):
        """Get next proxy from the rotation"""
        if not self.proxy_ips:
            raise Exception("No proxy IPs configured")
        
        proxy = {
            'host': self.proxy_ips[self.current_index],
            'port': Config.PROXY_PORT,
            'username': Config.PROXY_USERNAME,
            'password': Config.PROXY_PASSWORD
        }
        
        # Rotate to next proxy
        self.current_index = (self.current_index + 1) % len(self.proxy_ips)
        
        logging.info(f'Selected proxy: {proxy["host"]}:{proxy["port"]}')
        return proxy