import argparse
import os
from utils import get_embed
from notion_helper import NotionHelper
def get_file():
    # 设置文件夹路径
    folder_path = './OUT_FOLDER'

    # 检查文件夹是否存在
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        entries = os.listdir(folder_path)
        
        file_name = entries[0] if entries else None
        return file_name
    else:
        print("OUT_FOLDER does not exist.")
        return None
    
def main():
    image_file = get_file()
    if image_file:
        image_url = f"https://raw.githubusercontent.com/{os.getenv('REPOSITORY')}/{os.getenv('REF').split('/')[-1]}/OUT_FOLDER/{image_file}"
        heatmap_url = f"https://heatmap.malinkang.com/?image={image_url}"
        if notion_helper.heatmap_block_id:
            response = notion_helper.update_heatmap(
                block_id=notion_helper.heatmap_block_id, url=heatmap_url
            )
        else:
            response = notion_helper.append_blocks(
                block_id=notion_helper.page_id, children=[get_embed(heatmap_url)]
            )
notion_helper = NotionHelper()
if __name__ == "__main__":
   main()
