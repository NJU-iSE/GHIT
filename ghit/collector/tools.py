import time

import pandas as pd
import re
import os
from nltk.corpus import stopwords
from typing import List
import requests
import json
import csv
import yaml
from jinja2 import Template
from ghit.utils.logging import COL_LOG, ClE_LOG, COU_LOG


nltk_stopwords = set(stopwords.words('english'))


class Collector:
    def __init__(self, access_token, repos_name: str = None, query=None, url="https://api.github.com/graphql", headers=None,
                 **kwargs):
        if headers is None:
            self.headers = {
                "Authorization": f"Bearer {access_token}"
            }
        else:
            self.headers = headers
        # 定义查询字符串
        self.repos_name = repos_name
        self.url = url
        self.query = query
        # print(self.query)

    def get_one_page_issues(self, file_path):
        data, total_issue_count = get_response_data(self.url, self.query, self.headers, None)
        with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Title", "Body", "CreaDate", "Tags", "State", "Reactions",
                             "Comments", 'Link'])  # 添加 "Reactions" 和 "Comments" 列

            issues = data["data"]["repository"]["issues"]
            all_issues = issues["nodes"]
            write_to_file(all_issues, self.repos_name, writer)
        return self

    def get_whole_issues(self, file_path):
        start_col_time = time.time()
        with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Title", "Body", "CreaDate", "Tags", "State", "Reactions",
                             "Comments", 'Link'])  # 添加 "Reactions" 和 "Comments" 列

            # issues = self.data["data"]["repository"]["issues"]
            # all_issues = issues["nodes"]
            # has_next_page = issues["pageInfo"]["hasNextPage"]
            # end_cursor = issues["pageInfo"]["endCursor"]

            issue_number = 0
            end_cursor = None
            while issue_number == 0 or has_next_page:
                data, total_issue_count = get_response_data(self.url, self.query, self.headers, end_cursor)
                issue_number += 100
                issues = data["data"]["repository"]["issues"]
                all_issues = issues["nodes"]
                has_next_page = issues["pageInfo"]["hasNextPage"]
                end_cursor = issues["pageInfo"]["endCursor"]
                write_to_file(all_issues, self.repos_name, writer)
                if issue_number < total_issue_count:
                    collect_rate = issue_number / total_issue_count
                else:
                    collect_rate = 1
                current_col_time = time.time()
                col_time = current_col_time - start_col_time
                COL_LOG.info(f"ghit have collected and wrote {issue_number} issues into csv! {collect_rate:.2%} completed! {col_time:.2}ms")
        return self

    def get_open_issues(self, file_path):
        raise NotImplemented

    def get_close_issues(self, file_path):
        raise NotImplemented


class Cleaner:
    def __init__(self, from_file: str = None):
        # current_path = os.getcwd()
        self.file = from_file

    def clear(self, to_file: str = None):  # need file name
        import pandas as pd

        # 读取CSV文件
        df = pd.read_csv(self.file)

        # 保留满足条件的行
        date_condition = (df['CreaDate'].str.startswith(('2020', '2021', '2022', '2023')))  # TODO: date range selection
        tags_filter_condition = df['Tags'].str.contains('high priority', case=False, na=False)  # TODO: must-contained label type selection
        bug_report = df['Body'].str.contains('bug|Bug', case=False, na=False)
        bug_entries = df[date_condition & tags_filter_condition & bug_report]

        # tags_priority_condition = bug_entries['Tags'].str.contains('good first issue|high priority', case=False,
        #                                                            na=False)
        # filtered_df = bug_entries[tags_priority_condition]
        filtered_df = bug_entries

        # 保存更改后的文件
        filtered_df.to_csv(f'{to_file}', index=False)


class Counter:
    def __init__(self, file: str):
        self.file = file

    def prio_rank(self, col_weights: dict[str, float], top_n: int = None) -> pd.DataFrame:  # need file name
        df = pd.read_csv(self.file)  # 读取csv文件
        total_weight = sum(col_weights.values())  # compute the sum of all weights
        sort_key_df = pd.DataFrame()
        for col in df.columns:
            if col in col_weights:
                sort_key_df[col] = df[col] * col_weights[col]
        sort_key_df['sort_key'] = sort_key_df.sum(axis=1) / total_weight
        assert sort_key_df.__len__() != 0, f"cols in col_weights are not contained in file: {self.file}"
        df_sorted = df.iloc[sort_key_df['sort_key'].sort_values(ascending=False).index]

        if top_n is not None:
            df_sorted = df_sorted.head(top_n)

        return df_sorted

# def get_query_from_config(**kwargs):
#     with open('ghit/collector/config.yaml', 'r') as file:
#         config_data = yaml.load(file, Loader=yaml.FullLoader)
#
#     # 更新 includeFields 的值
#     include_fields = config_data['query']['includeFields']
#     include_fields.update(kwargs)
#
#     template = Template(config_data['query']['body'])
#     rendered_query = template.render(includeFields=include_fields)
#     return rendered_query


def process_text(text):
    if isinstance(text, float):
        return ''
    # text = text.lower()
    # replace "error" as "bug"
    # text = text.replace('error', 'bug')
    text = text.replace('na', 'nan')

    # delete the words containing "http"
    text = re.sub(r'http\S+', '', text)

    # delete one word
    text = re.sub(r'\b\w\b', '', text)

    # delete the specific words
    with open('stopwords.txt', 'r', encoding='utf-8') as f:
        words_to_remove = [line.strip() for line in f.readlines()]
    # words_pattern = '|'.join([re.escape(word) for word in words_to_remove])
    # words_pattern = r'\b(?:' + words_pattern + r')\b|\w*(' + words_pattern + r')\w*'
    words_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b'

    # use re to match the strings or substring is space
    text = re.sub(words_pattern, ' ', text, flags=re.IGNORECASE)

    text_list = text.split(" ")

    text_list = [x for x in text_list if x][:300]

    # remove the stopwords
    text_list = [word for word in text_list if word not in nltk_stopwords]

    text = " ".join(text_list)

    return text.strip()


def merge(intput_text: str):
    intput_text = intput_text.replace('.', ' ')
    str_list = intput_text.split(" ")
    str_list = [x for x in str_list if x][:300]
    output = " ".join(str_list)
    return output


def write_to_file(all_issues, repos_name, writer):
    for issue in all_issues:
        # for item in issue:
        #     print(item)
        # print(issue['number'])
        # print("https://github.com/pytorch/pytorch"+f"/issues/{issue['number']}")
        # exit()
        title = issue['title']
        body = issue['body']
        body = body.replace('"', ' ')  # 消除引号部分
        body = re.sub(r'@\w+', '', body)
        body = re.sub(r'```[\s\S]*?```', ' ', body)
        body = re.sub(r'[^a-zA-Z\s.]', ' ', body)
        title = re.sub(r'[^a-zA-Z\s]', ' ', title)
        body = body.replace('\n', ' ').strip()  # 消除回车符并去除首尾空格
        body = body.replace('`', ' ')
        body = body.replace('"', ' ')
        body = body.replace("'", ' ')
        text_list = body.split()
        # 使用列表推导式来过滤掉包含斜杠字符"/"的子字符串
        text_list = [text for text in text_list if '/' or '\\' not in text]
        # 将过滤后的子字符串重新连接成一个文本
        body = ' '.join(text_list)
        title = merge(title)
        body = merge(body)
        # body = f'"{body}"'
        created_at = issue['createdAt']
        state = issue['state']
        labels = ", ".join(label['name'] for label in issue['labels']['nodes'])
        reactions_count = issue['reactions']['totalCount']  # 获取点赞数
        comments_count = issue['comments']['totalCount']  # 获取评论数
        repo_url = "https://github.com/" + repos_name
        issue_id = issue['number']
        issue_link = f"{repo_url}/issues/{issue_id}"
        writer.writerow([title, body, created_at, labels, state, reactions_count,
                         comments_count, issue_link])  # 写入新的列 "Reactions" 和 "Comments"


def get_response_data(url, query, headers, cursor):
    response = requests.post(url, json={"query": query, "variables": {"cursor": cursor}}, headers=headers)
    assert response.status_code == 200, f"{response}"  # set the assertion
    data = response.json()
    total_issues_count = data["data"]["repository"]["issues"]["totalCount"]
    return data, total_issues_count