import utils
import requests
import json

with open("configs.json", "r", encoding="utf-8") as f:
    config = json.load(f)

if not utils.__main__(config["url"], config["top"],config["latest"]):
    exit(-1)

# 上传服务器

res = requests.post(config["host"] + ':' + config["port"], files={"2023090916019": open("./results/movie_info.json", "r")})

if res.status_code != 200:
    exit(-1)