import requests
from bs4 import BeautifulSoup
import json
import re
import datetime

with open("./configs.json", "r", encoding="utf-8") as f:
    config = json.load(f)

url = config["url"]
amount = config["latest"]
headers = {"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"}
score_rating = {"力荐": 5, "很差": 1, "较差": 2, "推荐": 4, "还行": 3}


def topM_url(URL, top):
    target_list = []
    for i in range(top//25 if top//25 else 1):  # 向上取整
        target_list.append(URL+'?'+'start={}'.format(i*25)+"&filter=")

    return target_list


def movie_url_generate(URL):
    target_list = []
    reply = requests.get(URL, headers=headers)
    if reply.status_code != 200:
        return False

    soup = BeautifulSoup(reply.text, "html.parser")
    soup = soup.find("ol", {"class": "grid_view"})
    movie_top250 = soup.find_all("li")
    for movie in movie_top250:
        movie_url = movie.find("a")["href"]
        target_list.append(movie_url)

    return target_list


def movie_info(URL):  # 返回一个不署名的字典，comment部分只有空list
    target_dict = {}
    reply = requests.get(URL, headers=headers)
    if reply.status_code != 200:
        return False
    '''
    movie_id !
    movie_rating !
    movie_title !
    movie_ReleaseTime !
    movie_directors multiple !
    movie_actors    mul !
    movie_type  mul !
    movie_brief !
    movie_CommentNum !
    comment_list    !
    '''
    soup = BeautifulSoup(reply.text, "html.parser")
    target_dict["movie_id"] = list(URL.split('/'))[-2]  # 豆瓣本站的ID，非IMDb

    js_content = soup.find("script", {"type": "application/ld+json"}).get_text()
    target_dict["movie_title"] = re.search(r'"name":\s+"(.+)"', js_content).group(1)
    target_dict["movie_rating"] = re.search(r'"ratingValue":\s+"(\S+)"', js_content).group(1)
    target_dict["movie_ReleaseTime"] = soup.find("span", {"class": "year"}).get_text()[1:-1]

    target_dict["movie_directors"] = list(map(lambda x: x["content"], soup.find_all("meta", {"property": "video:director"})))
    target_dict["movie_actors"] = list(map(lambda x: x["content"], soup.find_all("meta", {"property": "video:actor"})))
    target_dict["movie_types"] = list(map(lambda x: x.get_text(), soup.find_all("span", {"property": "v:genre"})))

    if soup.find("span", {"class": "all hidden"}) is None:
        target_dict["movie_brief"] = soup.find("span", {"property": "v:summary"}).get_text()

    else:
        target_dict["movie_brief"] = soup.find("span", {"class": "all hidden"}).get_text()

    target_dict["movie_CommentNum"] = soup.find("span", {"property": "v:votes"}).get_text()
    target_dict["comment_list"] = []

    return target_dict


def comment_url_generate(URL, amount):  # 返回获取某一个电影的评论所需的所有网页
    target_list = []
    URL = URL + "comments" + "?sort=time"
    for i in range(amount//20 if amount//20 else 1):  # 向上取整
        target_list.append(URL+"&start={}".format(i*20))

    return target_list


def comment_info(URLs):  # 获取某一个电影所有所需的评论
    target_list = []

    for url in URLs:
        temp_list = []
        reply = requests.get(url, headers=headers)
        if reply.status_code != 200:
            return False
        soup = BeautifulSoup(reply.text, "html.parser")
        comments = soup.find_all("div", {"class": "comment"})
        for comment in comments:
            temp_dict = {}
            '''
            comment_cid //
            comment_timestamp
            comment_rating //
            comment_content
            '''
            temp_dict["comment_cid"] = comment.find("a", {"href": "javascript:;"})["data-id"]

            try:
                temp_dict["comment_rating"] = score_rating[
                    comment.find("span", {"class": "allstar50 rating"})["title"]]
            except TypeError:
                try:
                    temp_dict["comment_rating"] = score_rating[
                        comment.find("span", {"class": "allstar40 rating"})["title"]]
                except TypeError:
                    try:
                        temp_dict["comment_rating"] = score_rating[
                            comment.find("span", {"class": "allstar30 rating"})["title"]]
                    except TypeError:
                        try:
                            temp_dict["comment_rating"] = score_rating[
                                comment.find("span", {"class": "allstar20 rating"})["title"]]
                        except TypeError:
                            try:
                                temp_dict["comment_rating"] = score_rating[
                                    comment.find("span", {"class": "allstar10 rating"})["title"]]
                            except TypeError:
                                temp_dict["comment_rating"] = None

            temp_dict["comment_content"] = comment.find("span", {"class": "short"}).get_text()
            temp_dict["comment_timestamp"] = int(
                datetime.datetime.strptime(comment.find("span", {"class": "comment-time"})["title"],
                                           "20%y-%m-%d %H:%M:%S").timestamp())

            temp_list.append(temp_dict)

        target_list += temp_list

    return target_list


def __main__(url, top, amount):
    movies = []
    topM_movie_list = topM_url(url, top)
    for pages in topM_movie_list:
        movies += movie_url_generate(pages)

    movies_info = []
    cnt = 0
    for movie in movies:
        temp_dict = movie_info(movie)
        comment_pages = comment_url_generate(movie, amount)
        temp_dict["comment_list"] = comment_info(comment_pages)

        movies_info.append(temp_dict)
        cnt += 1
        print("movie*{}".format(cnt))

    with open("./results/movie_info.json", "w", encoding="utf-8") as f:
        json.dump(movies_info, f, ensure_ascii=False, indent=2)

__main__(config["url"], 250, 100)