data = {
    "exchange": "ftx",
    "symbol": "ETH",
    "action": "BUY",
    "test": False,
    "target": "SPOT",
    "quantity": 20,
    "price": 3000,
    "leverage": 1,
    "order_type": "LIMIT",
    "stop_loss_type": "LIMIT",
    "take_profit_type": "LIMIT",
    "stop_loss": 0.1,
    "take_profit": 0.1,
    "margin": 0,
    "duplicate": False,
    "subaccount": "test-1",
    "api_key": "zLOfPdLfyscFzkD8nf56QgQDGVwDnqlkDfgwXAdC",
    "api_secret": "h_wbJHudb0gIKUguQL3EN4X65AGIGy9J9QFgUt3B",
}
response = requests.post("http://0.0.0.0:8000/", json=data)
print(response.json())