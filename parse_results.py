from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader


PDFS = [
    ("2026_MCM_Problem_A_Results.pdf", "MCM", "A"),
    ("2026_MCM_Problem_B_Results.pdf", "MCM", "B"),
    ("2026_MCM_Problem_C_Results.pdf", "MCM", "C"),
    ("2026_ICM_Problem_D_Results.pdf", "ICM", "D"),
    ("2026_ICM_Problem_E_Results.pdf", "ICM", "E"),
    ("2026_ICM_Problem_F_Results.pdf", "ICM", "F"),
]

DESIGNATIONS = [
    "Outstanding Winner",
    "Finalist",
    "Meritorious Winner",
    "Honorable Mention",
    "Successful Participant",
    "Unsuccessful Participant",
    "Disqualified",
    "Not Judged",
]

DESIGNATION_PATTERN = (
    r"(Outstanding Winner|Meritorious Winner|Honorable Mention|"
    r"Successful Participant|Unsuccessful(?: Participant|\s*-\s*[A-Z])?|"
    r"Disqualified(?:\s*-\s*[A-Z])?|Not Judged|Finalist)"
)
TEAM_PATTERN = r"26[0-3]\d{4}"

COUNTRY_SUFFIXES = sorted(
    [
        "Hong Kong (SAR) China",
        "Macao (SAR) China",
        "Macau (SAR) China",
        "United Arab Emirates",
        "United Kingdom",
        "Saudi Arabia",
        "South Korea",
        "New Zealand",
        "Puerto Rico",
        "United States",
        "USA",
        "CHINA",
        "China",
        "Australia",
        "Bangladesh",
        "Canada",
        "Singapore",
        "South Africa",
        "Malaysia",
        "Indonesia",
        "Thailand",
        "Vietnam",
        "India",
        "Japan",
        "Kazakhstan",
        "Korea",
        "Germany",
        "Hungary",
        "France",
        "Netherlands",
        "Switzerland",
        "Poland",
        "Brazil",
        "Mexico",
        "Colombia",
        "Peru",
        "Chile",
        "Turkey",
        "Egypt",
        "Pakistan",
        "Philippines",
        "Ireland",
        "Spain",
        "Italy",
        "Russia",
        "Taiwan",
        "Austria",
        "Belgium",
        "Denmark",
        "Norway",
        "Sweden",
        "Finland",
        "Israel",
    ],
    key=len,
    reverse=True,
)

ORPHAN_AWARD_LINES = {
    "COMAP Scholarship",
    "SIAM Award",
    "MAA Award",
    "AMS Award",
    "ASA Award",
    "INFORMS Award",
    "Rachel Carson Award",
    "Leonhard Euler Award",
    "Frank Giordano Award",
    "Ben Fusaro Award",
    "Vilfredo Pareto Award",
    "Veena Mendiratta Award",
}

INSTITUTION_ALIASES = {
    "huazhong university of science and": "Huazhong University of Science and Technology",
    "huazhong university of science &": "Huazhong University of Science and Technology",
    "nanjing university of posts and": "Nanjing University of Posts and Telecommunications",
    "nanjing university of post and": "Nanjing University of Posts and Telecommunications",
    "nanjing university of posts and telecommunications": "Nanjing University of Posts and Telecommunications",
    "beijing university of posts and": "Beijing University of Posts and Telecommunications",
    "beijing university of post and": "Beijing University of Posts and Telecommunications",
    "beijing university of posts and telecommunications": "Beijing University of Posts and Telecommunications",
    "university of electronic science and": "University of Electronic Science and Technology of China",
    "university of electronic science and technology of china": "University of Electronic Science and Technology of China",
    "university of electronic science and technology": "University of Electronic Science and Technology of China",
    "university of electronic science": "University of Electronic Science and Technology of China",
    "uestc": "University of Electronic Science and Technology of China",
    "nanjing university of aeronautics and": "Nanjing University of Aeronautics and Astronautics",
    "nanjing university of aeronautics and astronautics": "Nanjing University of Aeronautics and Astronautics",
    "nanjing university of science and": "Nanjing University of Science and Technology",
    "nanjing university of science & technology": "Nanjing University of Science and Technology",
    "nanjing university of science technology": "Nanjing University of Science and Technology",
    "central university of finance and": "Central University of Finance and Economics",
    "central university of finance and economic": "Central University of Finance and Economics",
    "central university of finacial and": "Central University of Finance and Economics",
    "university of international business and": "University of International Business and Economics",
    "university of international business and economics": "University of International Business and Economics",
    "southwestern university of finance and": "Southwestern University of Finance and Economics",
    "southwest university of finance and": "Southwestern University of Finance and Economics",
    "southern university of science and": "Southern University of Science and Technology",
    "southern university of science and technology": "Southern University of Science and Technology",
    "north china university of science and": "North China University of Science and Technology",
    "north china university of science": "North China University of Science and Technology",
    "university of science and technology of": "University of Science and Technology of China",
    "university of science and technology of china": "University of Science and Technology of China",
    "university of science and technology": "University of Science and Technology of China",
    "capital university of economics and": "Capital University of Economics and Business",
    "capital university of economics and business": "Capital University of Economics and Business",
    "capital university of business and": "Capital University of Economics and Business",
    "dongbei university of finance and": "Dongbei University of Finance and Economics",
    "dongbeiuniversity of finance and": "Dongbei University of Finance and Economics",
    "beijing university of civil engineering and": "Beijing University of Civil Engineering and Architecture",
    "beijing university of civil engineering and architecture": "Beijing University of Civil Engineering and Architecture",
    "shanghai university of finance and": "Shanghai University of Finance and Economics",
    "shanghai university of finance and economics": "Shanghai University of Finance and Economics",
    "zhejiang university of finance and": "Zhejiang University of Finance and Economics",
    "zhejiang university of finance &": "Zhejiang University of Finance and Economics",
    "zhejiang university of finance & economics": "Zhejiang University of Finance and Economics",
    "qingdao university of science and": "Qingdao University of Science and Technology",
    "qingdao university of science and technology": "Qingdao University of Science and Technology",
    "east china university of science and": "East China University of Science and Technology",
    "east china university of science and technology": "East China University of Science and Technology",
    "china university of political science and": "China University of Political Science and Law",
    "china university of political science and law": "China University of Political Science and Law",
    "chongqing university of posts and": "Chongqing University of Posts and Telecommunications",
    "chongqing university of post and": "Chongqing University of Posts and Telecommunications",
    "chongqing university of posts and telecommunications": "Chongqing University of Posts and Telecommunications",
    "nanjing university of information science &": "Nanjing University of Information Science & Technology",
    "nanjing university of information science": "Nanjing University of Information Science & Technology",
    "nanjing university of information science & technology": "Nanjing University of Information Science & Technology",
    "shandong institute of petroleum and": "Shandong Institute of Petroleum and Chemical Technology",
    "central south university of forestry and": "Central South University of Forestry and Technology",
    "central south university of forestry and technology": "Central South University of Forestry and Technology",
    "beijing information science and": "Beijing Information Science and Technology University",
    "beijing information science & technology": "Beijing Information Science and Technology University",
    "harbin university of science and": "Harbin University of Science and Technology",
    "harbin university of science and technology": "Harbin University of Science and Technology",
    "wuhan university of science and": "Wuhan University of Science and Technology",
    "wuhan university of science and technology": "Wuhan University of Science and Technology",
    "yunnan university of finance and": "Yunnan University of Finance and Economics",
    "yunnan university of finance and economics": "Yunnan University of Finance and Economics",
    "chongqing university of science and": "Chongqing University of Science and Technology",
    "chongqing university of science and technology": "Chongqing University of Science and Technology",
    "shandong university of finance and": "Shandong University of Finance and Economics",
    "shandong university of finance and economics": "Shandong University of Finance and Economics",
    "guangdong university of science and": "Guangdong University of Science and Technology",
    "guangdong university of science &": "Guangdong University of Science and Technology",
    "university of shanghai for science and": "University of Shanghai for Science and Technology",
    "univerisity of shanghai for science and": "University of Shanghai for Science and Technology",
    "university of shanghai for science and technology": "University of Shanghai for Science and Technology",
    "china university of petroleum-beijing at": "China University of Petroleum-Beijing at Karamay",
    "china university of petroleum-beijing at karamay": "China University of Petroleum-Beijing at Karamay",
    "anhui university of science and": "Anhui University of Science and Technology",
    "anhui university of science and technology": "Anhui University of Science and Technology",
    "xi'an university of architecture and": "Xi'an University of Architecture and Technology",
    "xi’an university of architecture and": "Xi'an University of Architecture and Technology",
    "tianjin university of finance and": "Tianjin University of Finance and Economics",
    "tianjin university of finance and economics": "Tianjin University of Finance and Economics",
    "suzhou university of science and": "Suzhou University of Science and Technology",
    "suzhou university of science and technology": "Suzhou University of Science and Technology",
    "jiangxi university of finance and": "Jiangxi University of Finance and Economics",
    "jiangxi university of finance and economics": "Jiangxi University of Finance and Economics",
    "xi'an university of posts and": "Xi'an University of Posts and Telecommunications",
    "xi’an university of posts and": "Xi'an University of Posts and Telecommunications",
    "xi'an university of posts &": "Xi'an University of Posts and Telecommunications",
    "xi’an university of posts &": "Xi'an University of Posts and Telecommunications",
    "the hong kong university of science and": "The Hong Kong University of Science and Technology",
    "hong kong university of science and": "The Hong Kong University of Science and Technology",
    "the hong kong university of science and technology": "The Hong Kong University of Science and Technology",
    "jiangsu university of science and": "Jiangsu University of Science and Technology",
    "jiangsu university of science and technology": "Jiangsu University of Science and Technology",
    "hunan university of science and": "Hunan University of Science and Technology",
    "hunan university of science and technology": "Hunan University of Science and Technology",
    "macau university of science and": "Macau University of Science and Technology",
    "macau university of science and technology": "Macau University of Science and Technology",
    "heilongjiang university of science and": "Heilongjiang University of Science and Technology",
    "heilongjiang university of science and technology": "Heilongjiang University of Science and Technology",
    "zhejiang university of water resources and": "Zhejiang University of Water Resources and Electric Power",
    "zhejiang university of water resources and electric power": "Zhejiang University of Water Resources and Electric Power",
    "changchun university of science and": "Changchun University of Science and Technology",
    "changchun university of science and technology": "Changchun University of Science and Technology",
    "shaanxi university of science &": "Shaanxi University of Science and Technology",
    "shaanxi university of science and": "Shaanxi University of Science and Technology",
    "shaanxi university of science & technology": "Shaanxi University of Science and Technology",
    "beijing university of aeronautics and": "Beijing University of Aeronautics and Astronautics",
    "beijing university of aeronautics and astronautics": "Beijing University of Aeronautics and Astronautics",
    "shanghai university of political science and": "Shanghai University of Political Science and Law",
    "changsha university of science and": "Changsha University of Science and Technology",
    "changsha university of science &": "Changsha University of Science and Technology",
    "guangdong university of finance &": "Guangdong University of Finance and Economics",
    "guangdong university of finance and": "Guangdong University of Finance and Economics",
    "luoyang institute of science and": "Luoyang Institute of Science and Technology",
    "kunming university of science and": "Kunming University of Science and Technology",
    "guangzhou college of technology and": "Guangzhou College of Technology and Business",
    "nanjing university of finance and": "Nanjing University of Finance and Economics",
    "zhongkai university of agriculture and": "Zhongkai University of Agriculture and Engineering",
    "taiyuan university of science and": "Taiyuan University of Science and Technology",
    "zhengzhou railway vocational and": "Zhengzhou Railway Vocational and Technical College",
    "henan university of science and": "Henan University of Science and Technology",
    "shanghai zhongqiao vocational and": "Shanghai Zhongqiao Vocational and Technical University",
    "guiyang institute of humanities and": "Guiyang Institute of Humanities and Technology",
    "tianjin university of science and": "Tianjin University of Science and Technology",
    "sichuan university of science &": "Sichuan University of Science & Engineering",
    "sichuan university of science and": "Sichuan University of Science & Engineering",
    "hunan vocational college of science and": "Hunan Vocational College of Science and Technology",
    "ningbo university of finance and": "Ningbo University of Finance and Economics",
    "guangdong lingnan vocational and": "Guangdong Lingnan Vocational and Technical College",
    "shanghai university of international": "Shanghai University of International Business and Economics",
    "beijing technology and business": "Beijing Technology and Business University",
    "guangzhou university": "Guangzhou University",
    "shenyang jianzhu university": "Shenyang Jianzhu University",
    "shenyang jianzhu university": "Shenyang Jianzhu University",
    "shanxi normal univercity": "Shanxi Normal University",
    "wenzhou university": "Wenzhou University",
    "duke kunshan univeristy": "Duke Kunshan University",
    "china university of geosciences beijing": "China University of Geosciences (Beijing)",
    "china university of geosciences(beijing)": "China University of Geosciences (Beijing)",
    "china university of geosciences (beijing)": "China University of Geosciences (Beijing)",
    "china university of geosciences, wuhan": "China University of Geosciences (Wuhan)",
    "china university of geosciences (wuhan)": "China University of Geosciences (Wuhan)",
    "nanjing university of finance & economics": "Nanjing University of Finance and Economics",
    "nanjing university of finance and economics": "Nanjing University of Finance and Economics",
    "nanjing university of fiance and": "Nanjing University of Finance and Economics",
    "tongda colledge of nanjing university of": "Tongda College, Nanjing University of Posts and Telecommunications",
    "tongda college, nanjing university of posts": "Tongda College, Nanjing University of Posts and Telecommunications",
    "college of science & technology ningbo": "College of Science & Technology Ningbo University",
    "shenzhen university of information": "Shenzhen Institute of Information Technology",
    "century college, beijing university of posts": "Century College, Beijing University of Posts and Telecommunications",
    "century college,beijing university of posts": "Century College, Beijing University of Posts and Telecommunications",
    "harbin institute of technology,shenzhen": "Harbin Institute of Technology, Shenzhen",
    "harbin institute of technology , shenzhen": "Harbin Institute of Technology, Shenzhen",
    "harbin institute of technology,weihai": "Harbin Institute of Technology, Weihai",
    "shandong university of science and": "Shandong University of Science and Technology",
    "hainan vocational university of science": "Hainan Vocational University of Science and Technology",
    "chongqing college of mobile": "Chongqing College of Mobile Communication",
    "chongqing metropolitan college of science": "Chongqing Metropolitan College of Science and Technology",
    "university of chinese academy of social": "University of Chinese Academy of Social Sciences",
    "east china university of political science": "East China University of Political Science and Law",
    "ningbo universitiy": "Ningbo University",
    "national university of denfense technology": "National University of Defense Technology",
    "shanghai jiaotong university": "Shanghai Jiao Tong University",
    "the chinese university of hong kong,": "The Chinese University of Hong Kong, Shenzhen",
    "chinese university of hong kong,": "The Chinese University of Hong Kong, Shenzhen",
    "xi'an jiaotong university city college": "City College of Xi'an Jiaotong University",
    "harbin institute of technology weihai": "Harbin Institute of Technology, Weihai",
    "harbin institute of technology at weihai": "Harbin Institute of Technology, Weihai",
    "northeastern university(cn)": "Northeastern University",
    "northeastern university(china)": "Northeastern University",
    "northeastern university, china": "Northeastern University",
    "northeastern university (china)": "Northeastern University",
    "beijing university of aeronautics and astronautics": "Beihang University",
    "china university of geosciences, beijing": "China University of Geosciences (Beijing)",
    "china university of petroleum, beijing": "China University of Petroleum-Beijing",
    "taizhou university, zhejiang": "Taizhou University",
    "zhejiang a&f universityv": "Zhejiang A&F University",
    "zhengzhou railway vocational & technical": "Zhengzhou Railway Vocational and Technical College",
    "fuzhou university of inter national studies": "Fuzhou University of International Studies and Trade",
    "chongqing technology and business": "Chongqing Technology and Business University",
    "chongqing jianzhu college": "Chongqing Jianzhu College",
    "shenzhen university of advanced": "Shenzhen University of Advanced Technology",
    "hainan bielefeld university of applied": "Hainan Bielefeld University of Applied Sciences",
    "northwest a&f university (nwafu)": "Northwest A&F University",
    "ningbo university of finance & economics": "Ningbo University of Finance and Economics",
    "ningbo tech university": "NingboTech University",
    "xi'an mingde institute of": "Xi'an Mingde Institute of Technology",
    "xi’an mingde institute of": "Xi'an Mingde Institute of Technology",
}

INSTITUTION_ZH = {
    "Xi'an Jiaotong University": "西安交通大学",
    "Huazhong University of Science and Technology": "华中科技大学",
    "Northwestern Polytechnical University": "西北工业大学",
    "Harbin Engineering University": "哈尔滨工程大学",
    "Harbin Institute of Technology": "哈尔滨工业大学",
    "Chongqing University": "重庆大学",
    "Dalian University of Technology": "大连理工大学",
    "Nanjing University of Posts and Telecommunications": "南京邮电大学",
    "University of Electronic Science and Technology of China": "电子科技大学",
    "Beihang University": "北京航空航天大学",
    "Jilin University": "吉林大学",
    "Shanghai Jiao Tong University": "上海交通大学",
    "South China University of Technology": "华南理工大学",
    "Nanjing University": "南京大学",
    "Hohai University": "河海大学",
    "Fuzhou University": "福州大学",
    "Ningbo University": "宁波大学",
    "Northeastern University": "东北大学",
    "Wuhan University": "武汉大学",
    "Renmin University of China": "中国人民大学",
    "Beijing Normal-Hong Kong Baptist": "北京师范大学-香港浸会大学联合国际学院",
    "Ocean University of China": "中国海洋大学",
    "Beijing Institute of Technology": "北京理工大学",
    "Sun Yat-sen University": "中山大学",
    "Nanjing University of Aeronautics and Astronautics": "南京航空航天大学",
    "XIDIAN UNIVERSITY": "西安电子科技大学",
    "Xidian University": "西安电子科技大学",
    "Southeast University": "东南大学",
    "Nanjing University of Science and Technology": "南京理工大学",
    "Sichuan University": "四川大学",
    "Nankai University": "南开大学",
    "Fudan University": "复旦大学",
    "China University of Mining and Technology": "中国矿业大学",
    "University of Science and Technology of China": "中国科学技术大学",
    "China Agricultural University": "中国农业大学",
    "Southwest University": "西南大学",
    "Northeastern University at Qinhuangdao": "东北大学秦皇岛分校",
    "National University of Defense Technology": "国防科技大学",
    "Shanghai University": "上海大学",
    "Northwest A&F University": "西北农林科技大学",
    "Chang'an University": "长安大学",
    "Xiamen University": "厦门大学",
    "Beijing Normal University": "北京师范大学",
    "Zhejiang University": "浙江大学",
    "Tongji University": "同济大学",
    "Central University of Finance and Economics": "中央财经大学",
    "China Three Gorges University": "三峡大学",
    "Tianjin University": "天津大学",
    "Anhui University": "安徽大学",
    "Jinan University": "暨南大学",
    "South China Normal University": "华南师范大学",
    "University of International Business and Economics": "对外经济贸易大学",
    "Jiangnan University": "江南大学",
    "Shandong University": "山东大学",
    "Lanzhou University": "兰州大学",
    "Xi'an Jiaotong-Liverpool University": "西交利物浦大学",
    "Hangzhou Normal University": "杭州师范大学",
    "Soochow University": "苏州大学",
    "Donghua University": "东华大学",
    "Southwestern University of Finance and Economics": "西南财经大学",
    "Beijing Jiaotong University": "北京交通大学",
    "Dalian Maritime University": "大连海事大学",
    "North China University of Science and Technology": "华北理工大学",
    "Southern University of Science and Technology": "南方科技大学",
    "Communication University of China": "中国传媒大学",
    "Tsinghua University": "清华大学",
    "Xiamen University Malaysia": "厦门大学马来西亚分校",
    "Shenzhen University": "深圳大学",
    "Henan Polytechnic University": "河南理工大学",
    "Huazhong Agricultural University": "华中农业大学",
    "Hangzhou Dianzi University": "杭州电子科技大学",
    "Shanghai Lixin University of Accounting": "上海立信会计金融学院",
    "Xiangtan University": "湘潭大学",
    "Shantou University": "汕头大学",
    "Nanjing University of Information Science & Technology": "南京信息工程大学",
    "Civil Aviation University of China": "中国民航大学",
    "Dongbei University of Finance and Economics": "东北财经大学",
    "Central South University": "中南大学",
    "Capital University of Economics and Business": "首都经济贸易大学",
    "Northeast Agricultural University": "东北农业大学",
    "Beijing University of Posts and Telecommunications": "北京邮电大学",
    "Hefei University of Technology": "合肥工业大学",
    "Harbin Institute of Technology, Weihai": "哈尔滨工业大学（威海）",
    "Zhejiang University of Finance and Economics": "浙江财经大学",
    "China University of Petroleum": "中国石油大学",
    "Lanzhou University of Technology": "兰州理工大学",
    "Beijing University of Chemical Technology": "北京化工大学",
    "China University of Petroleum (East China)": "中国石油大学（华东）",
    "China University of Petroleum(East China)": "中国石油大学（华东）",
    "China University of Petroleum East China": "中国石油大学（华东）",
    "Jiangxi Normal University": "江西师范大学",
    "University of Health and Rehabilitation": "康复大学",
    "Hunan University": "湖南大学",
    "Nanjing Agricultural University": "南京农业大学",
    "Beijing University of Technology": "北京工业大学",
    "Beijing University of Civil Engineering and Architecture": "北京建筑大学",
    "Fujian Normal University": "福建师范大学",
    "Hunan Normal University": "湖南师范大学",
    "Shanghai University of Finance and Economics": "上海财经大学",
    "Hebei University of Technology": "河北工业大学",
    "Zhongnan University of Economics and Law": "中南财经政法大学",
    "Tiangong University": "天津工业大学",
    "Qingdao University of Science and Technology": "青岛科技大学",
    "Zhejiang University of Technology": "浙江工业大学",
    "East China University of Science and Technology": "华东理工大学",
    "Liaoning University": "辽宁大学",
    "Chengdu University of Information": "成都信息工程大学",
    "Harbin Institute of Technology, Shenzhen": "哈尔滨工业大学（深圳）",
    "Yangzhou University": "扬州大学",
    "Qingdao University": "青岛大学",
    "Wuhan University of Technology": "武汉理工大学",
    "Nanjing Tech University": "南京工业大学",
    "South-Central Minzu University": "中南民族大学",
    "Chongqing University of Posts and Telecommunications": "重庆邮电大学",
    "Liaoning Technical University": "辽宁工程技术大学",
    "North China Electric Power University": "华北电力大学",
    "Huaqiao University": "华侨大学",
    "Nanjing Forestry University": "南京林业大学",
    "Shenyang University of Technology": "沈阳工业大学",
    "China University of Political Science and Law": "中国政法大学",
    "People's Public Security University of China": "中国人民公安大学",
    "Zhengzhou University": "郑州大学",
    "Zhejiang Gongshang University": "浙江工商大学",
    "Nanjing Normal University": "南京师范大学",
    "Shanghai University of Engineering Science": "上海工程技术大学",
    "Shandong Institute of Petroleum and Chemical Technology": "山东石油化工学院",
    "Beijing Information Science and Technology University": "北京信息科技大学",
    "Anhui University of Finance and Economics": "安徽财经大学",
    "Yantai University": "烟台大学",
    "Central South University of Forestry and Technology": "中南林业科技大学",
    "Guangdong Polytechnic Normal University": "广东技术师范大学",
    "Shandong Jianzhu University": "山东建筑大学",
    "Xi’an University of Technology": "西安理工大学",
    "Xi'an University of Technology": "西安理工大学",
    "Minzu University of China": "中央民族大学",
    "Peking University": "北京大学",
    "Nanjing University of Chinese Medicine": "南京中医药大学",
    "China Jiliang University": "中国计量大学",
    "Shanghai Maritime University": "上海海事大学",
    "Shijiazhuang Tiedao University": "石家庄铁道大学",
    "Zhejiang Chinese Medical University": "浙江中医药大学",
    "Beijing Institute of Petrochemical": "北京石油化工学院",
    "Hunan Agricultural University": "湖南农业大学",
    "Anhui University of Technology": "安徽工业大学",
    "Beijing Forestry University": "北京林业大学",
    "Guangxi University": "广西大学",
    "Guangdong University of Foreign Studies": "广东外语外贸大学",
    "Northeast Forestry University": "东北林业大学",
    "Beihua University": "北华大学",
    "China University of Geosciences": "中国地质大学",
    "Guangdong University of Technology": "广东工业大学",
    "Inner Mongolia University": "内蒙古大学",
    "Xi'an University of Posts and Telecommunications": "西安邮电大学",
    "North China University of Technology": "北方工业大学",
    "Sichuan Agricultural University": "四川农业大学",
    "Wuhan University of Science and Technology": "武汉科技大学",
    "China Foreign Affairs University": "外交学院",
    "Hainan University": "海南大学",
    "Nanjing Institute of Technology": "南京工程学院",
    "Xinjiang University": "新疆大学",
    "Yunnan University of Finance and Economics": "云南财经大学",
    "Harbin University of Science and Technology": "哈尔滨理工大学",
    "Northeast Petroleum University": "东北石油大学",
    "Southwest Petroleum University": "西南石油大学",
    "Guangdong University of Science and Technology": "广东科技学院",
    "Anhui Jianzhu University": "安徽建筑大学",
    "Chongqing University of Science and Technology": "重庆科技大学",
    "Shandong University of Finance and Economics": "山东财经大学",
    "University of Shanghai for Science and Technology": "上海理工大学",
    "China University of Petroleum-Beijing at Karamay": "中国石油大学（北京）克拉玛依校区",
    "Chongqing Jiaotong University": "重庆交通大学",
    "University of South China": "南华大学",
    "Zhejiang Sci-Tech University": "浙江理工大学",
    "Capital Normal University": "首都师范大学",
    "Jishou University": "吉首大学",
    "Shaanxi University of Science and Technology": "陕西科技大学",
    "Taiyuan University of Technology": "太原理工大学",
    "Xi'an University of Architecture and Technology": "西安建筑科技大学",
    "The Hong Kong University of Science and Technology": "香港科技大学",
    "Anhui University of Science and Technology": "安徽理工大学",
    "Jiangxi University of Finance and Economics": "江西财经大学",
    "Tianjin University of Finance and Economics": "天津财经大学",
    "Suzhou University of Science and Technology": "苏州科技大学",
    "Changsha University of Science and Technology": "长沙理工大学",
    "Jiangsu University of Science and Technology": "江苏科技大学",
    "Heilongjiang University of Science and Technology": "黑龙江科技大学",
    "Zhejiang University of Water Resources and Electric Power": "浙江水利水电学院",
    "Hunan University of Science and Technology": "湖南科技大学",
    "Macau University of Science and Technology": "澳门科技大学",
    "Northeast Normal University": "东北师范大学",
    "Duke University": "杜克大学",
    "University of Wisconsin-Madison": "威斯康星大学麦迪逊分校",
    "University of California, Los Angeles": "加利福尼亚大学洛杉矶分校",
    "University of Illinois Urbana-Champaign": "伊利诺伊大学厄巴纳-香槟分校",
    "The Hong Kong Polytechnic University": "香港理工大学",
    "City University of Hong Kong": "香港城市大学",
    "The Chinese University of Hong Kong": "香港中文大学",
    "University of Macau": "澳门大学",
    "National University of Singapore": "新加坡国立大学",
    "Liuzhou Institute of Technology": "柳州工学院",
    "Foshan University": "佛山大学",
    "Shanghai University of International Business and Economics": "上海对外经贸大学",
    "Beijing Normal University at Zhuhai": "北京师范大学珠海校区",
    "East China Normal University": "华东师范大学",
    "Henan University": "河南大学",
    "Xi’an Jiaotong-Liverpool University": "西交利物浦大学",
    "Xi’an Jiaotong University": "西安交通大学",
    "Beijing Technology and Business University": "北京工商大学",
    "Guangzhou University": "广州大学",
    "Qinghai University": "青海大学",
    "Southwest Jiaotong University": "西南交通大学",
    "Shenyang Jianzhu University": "沈阳建筑大学",
    "Harbin University of Commerce": "哈尔滨商业大学",
    "Shenzhen MSU-BIT University": "深圳北理莫斯科大学",
    "Shenzhen MSU–BIT University": "深圳北理莫斯科大学",
    "Yangtze University": "长江大学",
    "Shanghai Normal University": "上海师范大学",
    "University of Nottingham Ningbo China": "宁波诺丁汉大学",
    "Qufu Normal University": "曲阜师范大学",
    "Hubei University of Arts and Science": "湖北文理学院",
    "Shanxi Normal University": "山西师范大学",
    "Wenzhou University": "温州大学",
    "Leshan Normal University": "乐山师范学院",
    "Yanshan University": "燕山大学",
    "China University of Geosciences (Beijing)": "中国地质大学（北京）",
    "China University of Geosciences (Wuhan)": "中国地质大学（武汉）",
    "East China University of Technology": "东华理工大学",
    "Qingdao University of Technology": "青岛理工大学",
    "Duke Kunshan University": "昆山杜克大学",
    "Chaohu University": "巢湖学院",
    "Fujian University of Technology": "福建理工大学",
    "Capital Medical University": "首都医科大学",
    "Xuzhou Medical University": "徐州医科大学",
    "North University of China": "中北大学",
    "Wuyi University": "五邑大学",
    "Xi'An Technological University": "西安工业大学",
    "Xi'an Technological University": "西安工业大学",
    "College of Science & Technology Ningbo University": "宁波大学科学技术学院",
    "Suqian University": "宿迁学院",
    "Shenzhen Institute of Information Technology": "深圳信息职业技术学院",
    "University of International Relations": "国际关系学院",
    "Nanjing University of Finance and Economics": "南京财经大学",
    "Nanjing University Of Finance & Economics": "南京财经大学",
    "Nanjing University of Finance & Economics": "南京财经大学",
    "Jinan University Zhuhai Campus": "暨南大学珠海校区",
    "Guilin Tourism University": "桂林旅游学院",
    "Fujian Agriculture and Forestry University": "福建农林大学",
    "Harbin Medical University": "哈尔滨医科大学",
    "Panzhihua University": "攀枝花学院",
    "Guangzhou City University of Technology": "广州城市理工学院",
    "Changsha University": "长沙学院",
    "Changzhou University": "常州大学",
    "Changchun Normal University": "长春师范大学",
    "Huizhou University": "惠州学院",
    "Shaoguan University": "韶关学院",
    "Lingnan Normal University": "岭南师范学院",
    "University of Chinese Academy of Sciences": "中国科学院大学",
    "China Pharmaceutical University": "中国药科大学",
    "Hubei University": "湖北大学",
    "Tongda College, Nanjing University of Posts and Telecommunications": "南京邮电大学通达学院",
    "South China Agricultural University": "华南农业大学",
    "ShanghaiTech University": "上海科技大学",
    "Anhui Normal University": "安徽师范大学",
    "Fuyang Normal University": "阜阳师范大学",
    "Neusoft Institute Guangdong": "广东东软学院",
    "Tianjin Normal University": "天津师范大学",
    "Xi’an Eurasia University": "西安欧亚学院",
    "Xi'an Eurasia University": "西安欧亚学院",
    "Ningbo University of Technology": "宁波工程学院",
    "Shandong Normal University": "山东师范大学",
    "Jiaxing University": "嘉兴大学",
    "Nantong University": "南通大学",
    "City College of Xi'an Jiaotong University": "西安交通大学城市学院",
    "Dalian Ocean University": "大连海洋大学",
    "Century College, Beijing University of Posts and Telecommunications": "北京邮电大学世纪学院",
    "Southern Medical University": "南方医科大学",
    "China University of Petroleum-Beijing": "中国石油大学（北京）",
    "Shihezi University": "石河子大学",
    "Nanchang University": "南昌大学",
    "Fuzhou University Zhicheng College": "福州大学至诚学院",
    "Xi'an International University": "西安外事学院",
    "Chengdu University of Technology": "成都理工大学",
    "Dalian University": "大连大学",
    "Huaiyin Institute of Technology": "淮阴工学院",
    "Jiangsu University": "江苏大学",
    "Xijing University": "西京学院",
    "Central China Normal University": "华中师范大学",
    "Putian University": "莆田学院",
    "Jiaying University": "嘉应学院",
    "Nanchang Institute of Technology": "南昌工程学院",
    "Anhui Polytechnic University": "安徽工程大学",
    "Wuhan Polytechnic University": "武汉轻工大学",
    "Beijing Language and Culture University": "北京语言大学",
    "Guangdong Ocean University": "广东海洋大学",
    "Qilu University of Technology": "齐鲁工业大学",
    "Changzhou Institute of Technology": "常州工学院",
    "Taizhou University": "台州学院",
    "Hunan Institute of Science and Technology": "湖南理工学院",
    "Shandong University of Science and Technology": "山东科技大学",
    "Information Support Force Engineering University": "信息支援部队工程大学",
    "Information Support Force Engineering": "信息支援部队工程大学",
    "Beijing Institute of Technology Zhuhai": "北京理工大学珠海学院",
    "Wuxi University": "无锡学院",
    "Shanxi University": "山西大学",
    "Hainan Vocational University of Science and Technology": "海南科技职业大学",
    "Chongqing College of Mobile Communication": "重庆移通学院",
    "Nanjing Audit University": "南京审计大学",
    "Geely University of China": "吉利学院",
    "University of Jinan": "济南大学",
    "Jiamusi University": "佳木斯大学",
    "Henan University of Chinese Medicine": "河南中医药大学",
    "Northeast Electric Power University": "东北电力大学",
    "Chongqing Metropolitan College of Science and Technology": "重庆城市科技学院",
    "Shanghai Institute of Technology": "上海应用技术大学",
    "Hubei Minzu University": "湖北民族大学",
    "Beijing Foreign Studies University": "北京外国语大学",
    "Qiannan Normal University for Nationalities": "黔南民族师范学院",
    "Dongguan University of Technology": "东莞理工学院",
    "Shandong University(Weihai)": "山东大学（威海）",
    "Shanghai International Studies University": "上海外国语大学",
    "Shanxi Institute of Science and Technology": "山西科技学院",
    "Shanghai University of Electric Power": "上海电力大学",
    "Zhejiang Police College": "浙江警察学院",
    "Zhejiang Ocean University": "浙江海洋大学",
    "University of Chinese Academy of Social Sciences": "中国社会科学院大学",
    "Civil Aviation Flight University of China": "中国民用航空飞行学院",
    "Tianjin University of Technology": "天津理工大学",
    "Dalian Polytechnic University": "大连工业大学",
    "Jinzhong College of Information": "晋中信息学院",
    "Guangzhou Huashang College": "广州华商学院",
    "Xuzhou University of Technology": "徐州工程学院",
    "West Anhui University": "皖西学院",
    "Henan Normal University": "河南师范大学",
    "Northwest University": "西北大学",
    "Henan University of Economics and Law": "河南财经政法大学",
    "Wenzhou University of Technology": "温州理工学院",
    "Beijing Sport University": "北京体育大学",
    "HUBEI UNIVERSITY OF ECONOMICS": "湖北经济学院",
    "Hubei University of Economics": "湖北经济学院",
    "Chongqing Normal University": "重庆师范大学",
    "Shenyang Pharmaceutical University": "沈阳药科大学",
    "Yunnan University": "云南大学",
    "Hunan City University": "湖南城市学院",
    "Hangzhou City University": "浙大城市学院",
    "East China University of Political Science and Law": "华东政法大学",
    "Anhui Xinhua University": "安徽新华学院",
    "Qingdao Huanghai University": "青岛黄海学院",
    "Guangzhou University of Software": "广州软件学院",
    "The Chinese University of Hong Kong, Shenzhen": "香港中文大学（深圳）",
    "Guangdong University of Finance and Economics": "广东财经大学",
    "Changchun University of Science and Technology": "长春理工大学",
    "Sias University": "郑州西亚斯学院",
    "Hebei Finance University": "河北金融学院",
    "Ningxia University": "宁夏大学",
    "Shenyang Agricultural University": "沈阳农业大学",
    "Nanchang Hangkong University": "南昌航空大学",
    "Jinling Institute of Technology": "金陵科技学院",
    "Shandong University of Technology": "山东理工大学",
    "Guangdong Technology College": "广东理工学院",
    "Linyi University": "临沂大学",
    "Jiangsu Normal University": "江苏师范大学",
    "Changchun University of Technology": "长春工业大学",
    "Shenyang Aerospace University": "沈阳航空航天大学",
    "NingboTech University": "浙大宁波理工学院",
    "Guangxi Minzu University": "广西民族大学",
    "Shanghai University of Political Science and Law": "上海政法学院",
    "Xi'an Traffic Engineering Institute": "西安交通工程学院",
    "Hainan Bielefeld University of Applied Sciences": "海南比勒费尔德应用科学大学",
    "Wenzhou Medical University": "温州医科大学",
    "Zhongyuan University of Technology": "中原工学院",
    "Pingdingshan University": "平顶山学院",
    "Shanghai Ocean University": "上海海洋大学",
    "Xiamen Institute of Technology": "厦门工学院",
    "Heilongjiang Institute of Construction Technology": "黑龙江建筑职业技术学院",
    "Heilongjiang Institute of Construction": "黑龙江建筑职业技术学院",
    "Shandong Agricultural University": "山东农业大学",
    "Huangshan University": "黄山学院",
    "Zhejiang A&F University": "浙江农林大学",
    "Fuzhou University of International Studies and Trade": "福州外语外贸学院",
    "Wenzhou-Kean University": "温州肯恩大学",
    "Changchun Guanghua University": "长春光华学院",
    "Zhengzhou Railway Vocational and Technical College": "郑州铁路职业技术学院",
    "Xi'an Mingde Institute of Technology": "西安明德理工学院",
    "Southeast University Chengxian College": "东南大学成贤学院",
    "Inner Mongolia University of Technology": "内蒙古工业大学",
    "Shaanxi Normal University": "陕西师范大学",
    "New York University Shanghai": "上海纽约大学",
    "Luoyang Institute of Science and Technology": "洛阳理工学院",
    "Shenzhen University of Advanced Technology": "深圳理工大学",
    "Kashi University": "喀什大学",
    "City University of Macau": "澳门城市大学",
    "Fujian Jiangxia University": "福建江夏学院",
    "Hangzhou Medical College": "杭州医学院",
    "Shenzhen Technology University": "深圳技术大学",
    "Kunming University of Science and Technology": "昆明理工大学",
    "Guangzhou College of Technology and Business": "广州工商学院",
    "Chongqing Technology and Business University": "重庆工商大学",
    "Chongqing Jianzhu College": "重庆建筑工程职业学院",
    "Shandong Yingcai University": "山东英才学院",
    "Neijiang Normal University": "内江师范学院",
    "Guizhou University": "贵州大学",
    "Haikou University of Economics": "海口经济学院",
    "Henan University of Technology": "河南工业大学",
    "Hefei University": "合肥大学",
    "Beijing Polytechnic University": "北京工业职业技术学院",
    "Tianjin Agricultural University": "天津农学院",
    "Guangzhou Maritime University": "广州航海学院",
    "Ningbo Polytechnic University": "宁波职业技术大学",
    "Hainan Normal University": "海南师范大学",
    "Xi'an Shiyou University": "西安石油大学",
    "Liaocheng University": "聊城大学",
    "Xiamen University of Technology": "厦门理工学院",
    "Beijing University of Aeronautics and Astronautics": "北京航空航天大学",
    "Yanbian University": "延边大学",
    "Tianjin University of Commerce": "天津商业大学",
    "Wenzhou Business College": "温州商学院",
    "Zhongkai University of Agriculture and Engineering": "仲恺农业工程学院",
    "Heilongjiang University": "黑龙江大学",
    "Xiamen University Tan Kah Kee College": "厦门大学嘉庚学院",
    "Shandong Police College": "山东警察学院",
    "Zhengzhou University of Light Industry": "郑州轻工业大学",
    "Nanning Normal University": "南宁师范大学",
    "Chengdu Technological University": "成都工业学院",
    "Inner Mongolia Normal University": "内蒙古师范大学",
    "Sanda University": "上海杉达学院",
    "Ningbo University of Finance and Economics": "宁波财经学院",
    "Inner Mongolia Agricultural University": "内蒙古农业大学",
    "Xi'an Aeronautical Polytechnic Institute": "西安航空职业技术学院",
    "Zhuhai College of Science and Technology": "珠海科技学院",
    "Liaoning Petrochemical University": "辽宁石油化工大学",
    "Chengdu Neusoft University": "成都东软学院",
    "Guilin University of Technology": "桂林理工大学",
}


def norm_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_institution(value: str) -> str:
    value = norm_spaces(value)
    if value in {"门", "尔", "/"}:
        return ""
    if "@" in value:
        return ""
    return INSTITUTION_ALIASES.get(value.casefold(), value)


def institution_zh(value: str) -> str:
    if not value:
        return ""
    if value in INSTITUTION_ZH:
        return INSTITUTION_ZH[value]
    value_key = value.casefold()
    for english_name, chinese_name in INSTITUTION_ZH.items():
        if english_name.casefold() == value_key:
            return chinese_name
    return ""


def merge_awards(*values: str) -> str:
    seen = set()
    merged = []
    for value in values:
        for part in re.split(r"\s*;\s*", value or ""):
            part = norm_spaces(part)
            if not part or part == "-":
                continue
            key = part.casefold().replace(" scholarship award", " scholarship")
            if key not in seen:
                seen.add(key)
                merged.append(part)
    return "; ".join(merged)


def designation_label(raw: str) -> str:
    raw = norm_spaces(raw)
    if raw.startswith("Unsuccessful"):
        return "Unsuccessful Participant"
    if raw.startswith("Disqualified"):
        return "Disqualified"
    return raw


def split_country(rest: str) -> tuple[str, str]:
    rest = norm_spaces(rest)
    if not rest:
        return "", ""

    for country in COUNTRY_SUFFIXES:
        if rest.casefold().endswith(country.casefold()):
            award = rest[: -len(country)].strip(" -")
            normalized_country = "China" if country.casefold() == "china" else country
            return award, normalized_country

    return rest, ""


def parse_line(
    line: str, contest: str, expected_problem: str, source_pdf: str, page: int
) -> dict[str, str | int] | None:
    normalized = norm_spaces(line)
    control_match = re.search(TEAM_PATTERN, normalized)
    if not control_match:
        return None

    team = control_match.group(0)
    institution_raw = norm_spaces(normalized[: control_match.start()])
    institution = clean_institution(institution_raw)
    after_team = normalized[control_match.end() :]
    designation_match = re.search(rf"\b([A-F])\s+{DESIGNATION_PATTERN}", after_team)
    if not designation_match:
        return None

    advisor = norm_spaces(after_team[: designation_match.start()])
    problem = designation_match.group(1)
    raw_designation = norm_spaces(designation_match.group(2))
    designation = designation_label(raw_designation)
    special_award, country = split_country(after_team[designation_match.end() :])

    if raw_designation.startswith(("Disqualified", "Unsuccessful")) and raw_designation != designation:
        note = raw_designation.replace("Disqualified", "").replace("Unsuccessful", "").strip()
        special_award = norm_spaces(f"{note} {special_award}".strip())

    return {
        "team": team,
        "institution": institution,
        "institution_raw": institution_raw,
        "institution_cn": institution_zh(institution),
        "institution_key": institution.casefold(),
        "certificate_url": f"https://www.comap-math.org/mcm/2026Certs/{team}.pdf",
        "country": country,
        "advisor": advisor,
        "contest": contest,
        "problem": problem,
        "expected_problem": expected_problem,
        "designation": designation,
        "designation_raw": raw_designation,
        "special_award": special_award,
        "source_pdf": source_pdf,
        "page": page,
    }


def expected_counts(first_page_text: str) -> dict[str, int]:
    counts = {}
    for designation in DESIGNATIONS:
        match = re.search(rf"{re.escape(designation)}\s+([0-9,]+)\s+", first_page_text)
        if match:
            counts[designation] = int(match.group(1).replace(",", ""))
    return counts


def featured_awards(first_page_text: str) -> dict[str, str]:
    awards_by_team: dict[str, str] = {}
    current_team = ""
    in_section = False

    for raw_line in first_page_text.splitlines():
        line = norm_spaces(raw_line)
        if line.startswith("TEAM#"):
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("All ") or "PARTNERS & SPONSORS" in line:
            break

        team_match = re.match(rf"^({TEAM_PATTERN})\s+", line)
        if team_match:
            current_team = team_match.group(1)
            awards_by_team.setdefault(current_team, "")
            if "—" in line:
                award = norm_spaces(line.split("—", 1)[1])
                awards_by_team[current_team] = merge_awards(awards_by_team[current_team], award)
        elif current_team and line.startswith("—"):
            award = norm_spaces(line.lstrip("—"))
            awards_by_team[current_team] = merge_awards(awards_by_team[current_team], award)

    return {team: awards for team, awards in awards_by_team.items() if awards}


def parse_pdf(path: Path, contest: str, problem: str) -> tuple[list[dict], dict, dict, list]:
    reader = PdfReader(str(path))
    first_page_text = reader.pages[0].extract_text() or ""
    expected = expected_counts(first_page_text)
    official_awards = featured_awards(first_page_text)
    rows = []
    issues = []
    pending = ""
    prefix_parts: list[str] = []

    for page_index in range(1, len(reader.pages)):
        text = reader.pages[page_index].extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(
                (f"{contest} Problem {problem} Contest Results", "institutionCtrl #", "2026")
            ):
                continue
            if line in ORPHAN_AWARD_LINES:
                continue

            has_team = bool(re.search(TEAM_PATTERN, line))
            if has_team:
                if pending:
                    parsed = parse_line(pending, contest, problem, path.name, page_index + 1)
                    if parsed:
                        rows.append(parsed)
                    else:
                        issues.append({"source_pdf": path.name, "page": page_index + 1, "line": pending})

                if prefix_parts:
                    pending = norm_spaces(" ".join(prefix_parts + [line]))
                    prefix_parts = []
                else:
                    pending = line
                if re.search(DESIGNATION_PATTERN, pending):
                    parsed = parse_line(pending, contest, problem, path.name, page_index + 1)
                    if parsed:
                        rows.append(parsed)
                        pending = ""
            elif pending:
                pending += " " + line
                if re.search(DESIGNATION_PATTERN, pending):
                    parsed = parse_line(pending, contest, problem, path.name, page_index + 1)
                    if parsed:
                        rows.append(parsed)
                        pending = ""
            else:
                prefix_parts.append(line)

    if pending:
        parsed = parse_line(pending, contest, problem, path.name, len(reader.pages))
        if parsed:
            rows.append(parsed)
        else:
            issues.append({"source_pdf": path.name, "page": len(reader.pages), "line": pending})

    return rows, expected, official_awards, issues


def build_summary(records: list[dict], expected: dict[str, dict[str, int]]) -> dict:
    by_problem = defaultdict(Counter)
    by_designation = Counter()
    by_country = Counter()
    institutions = Counter()
    institutions_cn = {}

    for row in records:
        by_problem[row["problem"]][row["designation"]] += 1
        by_designation[row["designation"]] += 1
        if row["country"]:
            by_country[row["country"]] += 1
        if row["institution"]:
            institutions[row["institution"]] += 1
            if row.get("institution_cn"):
                institutions_cn[row["institution"]] = row["institution_cn"]

    return {
        "record_count": len(records),
        "institution_count": len(institutions),
        "designation_order": DESIGNATIONS,
        "problem_order": ["A", "B", "C", "D", "E", "F"],
        "by_problem": {problem: dict(by_problem[problem]) for problem in ["A", "B", "C", "D", "E", "F"]},
        "by_designation": dict(by_designation),
        "top_institutions": institutions.most_common(30),
        "institution_names_cn": institutions_cn,
        "top_countries": by_country.most_common(20),
        "expected": expected,
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    records = []
    expected = {}
    issues = []

    for filename, contest, problem in PDFS:
        rows, pdf_expected, official_awards, pdf_issues = parse_pdf(root / filename, contest, problem)
        for row in rows:
            if row["team"] in official_awards:
                row["special_award"] = merge_awards(official_awards[row["team"]], row["special_award"])
        records.extend(rows)
        expected[problem] = pdf_expected
        issues.extend(pdf_issues)

    out_dir = root / "data"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "generated_from": [filename for filename, _, _ in PDFS],
        "summary": build_summary(records, expected),
        "records": records,
    }
    (out_dir / "awards.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (out_dir / "parse_issues.json").write_text(
        json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"records: {len(records)}")
    print(f"institutions: {payload['summary']['institution_count']}")
    print(f"parse issues: {len(issues)}")
    for problem in payload["summary"]["problem_order"]:
        parsed = payload["summary"]["by_problem"][problem]
        print(problem, parsed, "expected", expected.get(problem, {}))


if __name__ == "__main__":
    main()
