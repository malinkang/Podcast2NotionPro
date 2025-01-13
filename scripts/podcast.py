import argparse
import json
import os
import pendulum
from retrying import retry
import requests
from notion_helper import NotionHelper
import utils
from dotenv import load_dotenv

load_dotenv()

from config import (
    movie_properties_type_dict,
    book_properties_type_dict,
    TAG_ICON_URL,
    TZ,
)
from utils import get_icon


headers = {
    "host": "api.xiaoyuzhoufm.com",
    "applicationid": "app.podcast.cosmos",
    "x-jike-refresh-token": os.getenv("REFRESH_TOKEN").strip(),
    "x-jike-device-id": "5070e349-ba04-4c7b-a32e-13eb0fed01e7",
}


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def refresh_token():
    url = "https://api.xiaoyuzhoufm.com/app_auth_tokens.refresh"
    resp = requests.post(url, headers=headers)
    if resp.ok:
        token = resp.json().get("x-jike-access-token")
        headers["x-jike-access-token"] = token


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def get_podcast():
    results = []
    url = "https://api.xiaoyuzhoufm.com/v1/subscription/list"
    data = {
        "limit": 25,
        "sortBy": "subscribedAt",
        "sortOrder": "desc",
    }
    loadMoreKey = ""
    while loadMoreKey is not None:
        if loadMoreKey:
            data["loadMoreKey"] = loadMoreKey
        resp = requests.post(url, json=data, headers=headers)
        if resp.ok:
            loadMoreKey = resp.json().get("loadMoreKey")
            results.extend(resp.json().get("data"))
        else:
            refresh_token()
            raise Exception(f"Error {data} {resp.text}")
    return results


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def get_mileage(rank="TOTAL"):
    results = []
    url = "https://api.xiaoyuzhoufm.com/v1/mileage/list"
    data = {"rank": rank}
    loadMoreKey = ""
    while loadMoreKey is not None:
        if loadMoreKey:
            data["loadMoreKey"] = loadMoreKey
        resp = requests.post(url, json=data, headers=headers)
        if resp.ok:
            loadMoreKey = resp.json().get("loadMoreKey")
            for item in resp.json().get("data"):
                podcast = item.get("podcast")
                podcast["playedSeconds"] = item.get("playedSeconds", 0)
                results.append(podcast)
        else:
            refresh_token()
            raise Exception(f"Error {data} {resp.text}")
    return results


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def get_episode(pid, timestamp):
    results = []
    url = "https://api.xiaoyuzhoufm.com/v1/episode/list"
    data = {
        "limit": 25,
        "pid": pid,
    }
    loadMoreKey = ""
    while loadMoreKey is not None:
        if loadMoreKey:
            data["loadMoreKey"] = loadMoreKey
        resp = requests.post(url, json=data, headers=headers)
        if resp.ok:
            loadMoreKey = resp.json().get("loadMoreKey")
            d = resp.json().get("data")
            for item in d:
                pubDate = pendulum.parse(item.get("pubDate")).in_tz("UTC").int_timestamp
                if pubDate <= timestamp:
                    return results
                item["pubDate"] = pubDate
                results.append(item)
        else:
            refresh_token()
            raise Exception(f"Error {data} {resp.text}")
    return results


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def get_history():
    results = []
    url = "https://api.xiaoyuzhoufm.com/v1/episode-played/list-history"
    data = {
        "limit": 25,
    }
    loadMoreKey = ""
    while loadMoreKey is not None:
        if loadMoreKey:
            data["loadMoreKey"] = loadMoreKey
        resp = requests.post(url, json=data, headers=headers)
        if resp.ok:
            loadMoreKey = resp.json().get("loadMoreKey")
            d = resp.json().get("data")
            for item in d:
                episode = item.get("episode")
                pubDate = (
                    pendulum.parse(episode.get("pubDate")).in_tz("UTC").int_timestamp
                )
                episode["pubDate"] = pubDate
                results.append(episode)
        else:
            refresh_token()
            raise Exception(f"Error {data} {resp.text}")
    return results


def merge_podcast(list1, list2):
    results = []
    results.extend(list1)
    d = {x.get("pid"): x for x in list1}
    for item in list2:
        if item.get("pid") not in d:
            results.append(item)
    return results



def insert_podcast():
    list1 = get_mileage()
    list2 = get_podcast()
    results = merge_podcast(list1, list2)
    notion_podcasts = notion_helper.get_all_podcast()
    dict = {}
    for index, result in enumerate(results):
        podcast = {}
        podcast["播客"] = result.get("title")
        podcast["Brief"] = result.get("brief")
        pid = result.get("pid")
        podcast["Pid"] = pid
        podcast["收听时长"] = result.get("playedSeconds", 0)
        podcast["Description"] = result.get("description")
        podcast["链接"] = f"https://www.xiaoyuzhoufm.com/podcast/{result.get('pid')}"
        if result.get("latestEpisodePubDate"):
            podcast["最后更新时间"] = (
                pendulum.parse(result.get("latestEpisodePubDate"))
                .replace(second=0)
                .in_tz("UTC")
                .int_timestamp
            )
        cover = result.get("image").get("picUrl")

        page_id = None
        if pid in notion_podcasts:
            old_podcast = notion_podcasts.get(pid)
            page_id = old_podcast.get("page_id")
            dict[pid] = (page_id, cover)
            if (
                old_podcast.get("最后更新时间") == podcast.get("最后更新时间")
                and old_podcast.get("收听时长") == podcast.get("收听时长")
            ):
                continue
        print(
            f"正在同步 = {result.get('title')}，共{len(results)}个播客，当前是第{index+1}个"
        )
        podcast["全部"] = [
            notion_helper.get_relation_id(
                "全部", notion_helper.all_database_id, TAG_ICON_URL
            )
        ]
        podcast["作者"] = [
            notion_helper.get_relation_id(
                x.get("nickname"),
                notion_helper.author_database_id,
                x.get("avatar").get("picture").get("picUrl"),
            )
            for x in result.get("podcasters")
        ]
        properties = utils.get_properties(podcast, movie_properties_type_dict)
        parent = {
            "database_id": notion_helper.podcast_database_id,
            "type": "database_id",
        }
        if page_id:
            notion_helper.update_page(page_id=page_id, properties=properties)
        else:
            page_id = notion_helper.create_page(
                parent=parent, properties=properties, icon=get_icon(cover)
            ).get("id")
        dict[pid] = (page_id, cover)
    return dict


def get_monthly_wrapped(year, month, id):
    url = "https://api.xiaoyuzhoufm.com/v1/monthly-wrapped/get"
    data = {"uid": get_profile(), "year": year, "month": month}
    resp = requests.get(url, params=data, headers=headers)
    playedDays = 0
    playedSeconds = 0
    if resp.ok:
        data = resp.json().get("data")
        if data:
            playedDays = data.get("playedDays")
            playedSeconds = data.get("playedSeconds")
        properties = {
            "收听时长": {"number": playedSeconds},
            "收听天数": {"number": playedDays},
        }
        notion_helper.update_page(id, properties)


def get_month_from_notion():
    filter = {
        "and": [
            {"property": "收听时长", "number": {"is_empty": True}},
            {
                "property": "日期",
                "date": {"before": pendulum.now(tz=TZ).replace(day=1).to_date_string()},
            },
        ]
    }
    return notion_helper.query(
        database_id=notion_helper.month_database_id, filter=filter
    )


def update_month_data():
    for result in get_month_from_notion().get("results"):
        title = utils.get_property_value(result.get("properties").get("标题"))
        if not title:
            continue
        id = result.get("id")
        year = int(title[0:4])
        month = int(title[5 : title.index("月")])
        get_monthly_wrapped(year, month, id)


def insert_episode(episodes, d):
    episodes.sort(key=lambda x: x["pubDate"])
    notion_episodes = notion_helper.get_all_episode()
    for index, result in enumerate(episodes):

        pid = result.get("pid")
        if pid not in d:
            continue
        page_id = None
        eid = result.get("eid")
        episode = {}
        episode["标题"] = result.get("title")
        episode["Description"] = result.get("description")
        episode["时间戳"] = result.get("pubDate")
        episode["发布时间"] = result.get("pubDate")
        episode["音频"] = result.get("media").get("source").get("url")
        episode["Eid"] = eid
        episode["时长"] = result.get("duration")
        episode["喜欢"] = result.get("isPicked")
        episode["收听进度"] = result.get("progress")
        episode["Podcast"] = [d.get(pid)[0]]
        episode["链接"] = f"hhttps://www.xiaoyuzhoufm.com/episode/{result.get('eid')}"
        status = "未听"
        if result.get("isFinished"):
            episode["收听进度"] = result.get("duration")
            status = "听过"
        elif result.get("isPlayed"):
            status = "在听"
        episode["状态"] = status
        if result.get("playedAt"):
            episode["日期"] = (
                pendulum.parse(result.get("playedAt"))
                .replace(second=0)
                .in_tz("UTC")
                .int_timestamp
            )
        page_id = None
        if eid in notion_episodes:
            old_episode = notion_episodes.get(eid)
            # 如果是听过将老的日期赋值为老的日期
            if old_episode.get("状态") == "听过":
                episode["日期"] = old_episode.get("日期")
            if (
                old_episode.get("状态") == episode.get("状态")
                and old_episode.get("喜欢") == episode.get("喜欢")
                and old_episode.get("收听进度") == episode.get("收听进度")
                and old_episode.get("日期") == episode.get("日期")
            ):
                continue
            page_id = old_episode.get("page_id")
        print(
            f"正在同步 = {result.get('title')}，共{len(episodes)}个Episode，当前是第{index+1}个"
        )
        episode["全部"] = [
            notion_helper.get_relation_id(
                "全部", notion_helper.all_database_id, TAG_ICON_URL
            )
        ]
        properties = utils.get_properties(episode, book_properties_type_dict)
        notion_helper.get_all_relation(properties=properties)
        if episode.get("日期"):
            notion_helper.get_date_relation(
                properties=properties,
                date=pendulum.from_timestamp(episode.get("日期"), tz="Asia/Shanghai"),
            )
        parent = {
            "database_id": notion_helper.episode_database_id,
            "type": "database_id",
        }
        if page_id:
            notion_helper.update_page(page_id=page_id, properties=properties)
        else:
            notion_helper.create_page(
                parent=parent, properties=properties, icon=get_icon(d.get(pid)[1])
            )


def get_progress(eids):
    """获取播放进度"""
    url = "https://api.xiaoyuzhoufm.com/v1/playback-progress/list"
    data = {"eids": eids}
    resp = requests.post(url, json=data, headers=headers)
    if resp.ok:
        return resp.json().get("data")


def get_profile():
    url = "https://api.xiaoyuzhoufm.com/v1/profile/get"
    resp = requests.get(url, headers=headers)
    if resp.ok:
        return resp.json().get("data").get("uid")


if __name__ == "__main__":
    notion_helper = NotionHelper()
    refresh_token()
    d = insert_podcast()
    episodes = get_history()
    eids = [x.get("eid") for x in episodes]
    progress = get_progress(eids)
    progress = {x.get("eid"): x for x in progress}
    for episode in episodes:
        if episode["eid"] in progress:
            episode["progress"] = progress.get(episode["eid"]).get("progress")
            episode["playedAt"] = progress.get(episode["eid"]).get("playedAt")
    insert_episode(episodes, d)
    update_month_data()
