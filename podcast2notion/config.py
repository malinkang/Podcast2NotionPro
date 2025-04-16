RICH_TEXT = "rich_text"
URL = "url"
RELATION = "relation"
NUMBER = "number"
DATE = "date"
FILES = "files"
STATUS = "status"
TITLE = "title"
SELECT = "select"
CHECKBOX = "checkbox"
MULTI_SELECT = "multi_select"
TZ = "Asia/Shanghai"
book_properties_type_dict = {
    "标题": TITLE,
    "Description": RICH_TEXT,
    "音频": RICH_TEXT,
    "Eid": RICH_TEXT,
    "链接": URL,
    "通义链接": URL,
    "发布时间": DATE,
    "时长": NUMBER,
    "时间戳": NUMBER,
    "状态": STATUS,
    "Podcast": RELATION,
    "喜欢": CHECKBOX,
    "日期": DATE,
    "收听进度": NUMBER,
}

TAG_ICON_URL = "https://www.notion.so/icons/hourglass_gray.svg"


movie_properties_type_dict = {
    "播客": TITLE,
    "Brief": RICH_TEXT,
    "Description": RICH_TEXT,
    "Pid": RICH_TEXT,
    "作者": RELATION,
    "全部": RELATION,
    "最后更新时间": DATE,
    "链接": URL,
    "收听时长": NUMBER,
    "通义链接": URL,
}
