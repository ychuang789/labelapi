import os
from dotenv import load_dotenv
from datetime import date
from pydantic import BaseModel, BaseSettings, Field
from typing import Dict, Optional, List, Union

from definition import SAVE_DETAIL_FOLDER
from utils.enum_config import ModelType, PredictTarget

load_dotenv()

SOURCE: Dict = {
    "Comment": [
        "WH_F0183",
        "WH_F0198",
        "WH_F0200",
        "WH_F0199",
        "WH_F0500"
    ],
    # "Dcard": [
    #     "WH_F0116"
    # ],
    "Instagram": [
        "WH_F0157"
    ],
    "Ptt": [
        "WH_F0001"
    ],
    "Tiktok": [
        "WH_F0501"
    ],
    "Twitter": [
        "WH_F0127"
    ],
    "Youtube": [
        "WH_F0147"
    ],
    "blog": [
        "WH_B0002",
        "WH_B0003",
        "WH_B0004",
        "WH_B0006",
        "WH_B0007",
        "WH_B0008",
        "WH_B0009",
        "WH_B0010",
        "WH_B0011",
        "WH_B0013",
        "WH_B0016",
        "WH_B0017",
        "WH_B0018",
        "WH_B0019",
        "WH_B0020",
        "WH_B0021",
        "WH_B0022",
        "WH_B0023",
        "WH_B0024",
        "WH_B0026",
        "WH_B0027",
        "WH_B0028",
        "WH_B0029",
        "WH_B0030",
        "WH_B0031",
        "WH_B0032",
        "WH_B0033",
        "WH_B0034",
        "WH_B0035",
        "WH_B0036",
        "WH_B0037",
        "WH_B0038",
        "WH_B0039",
        "WH_B0040",
        "WH_B0041",
        "WH_B0042",
        "WH_B0043",
        "WH_B0044",
        "WH_B0045",
        "WH_B0046",
        "WH_B0047",
        "WH_B0048",
        "WH_B0049"
    ],
    "fbfans": [
        "WH_F0045"
    ],
    "fbgroup": [
        "WH_F0165"
    ],
    "fbkol": [
        "WH_F0071"
    ],
    "fbpm": [
        "WH_F0072"
    ],
    "fbprivategroup": [
        "WH_F0167"
    ],
    "forum": [
        "WH_F0002",
        "WH_F0003",
        "WH_F0005",
        "WH_F0006",
        "WH_F0007",
        "WH_F0008",
        "WH_F0011",
        "WH_F0012",
        "WH_F0013",
        "WH_F0014",
        "WH_F0015",
        "WH_F0016",
        "WH_F0018",
        "WH_F0019",
        "WH_F0021",
        "WH_F0022",
        "WH_F0023",
        "WH_F0024",
        "WH_F0026",
        "WH_F0027",
        "WH_F0028",
        "WH_F0029",
        "WH_F0031",
        "WH_F0032",
        "WH_F0033",
        "WH_F0034",
        "WH_F0035",
        "WH_F0036",
        "WH_F0039",
        "WH_F0040",
        "WH_F0043",
        "WH_F0044",
        "WH_F0046",
        "WH_F0047",
        "WH_F0048",
        "WH_F0050",
        "WH_F0051",
        "WH_F0052",
        "WH_F0053",
        "WH_F0054",
        "WH_F0055",
        "WH_F0056",
        "WH_F0057",
        "WH_F0058",
        "WH_F0059",
        "WH_F0060",
        "WH_F0061",
        "WH_F0063",
        "WH_F0064",
        "WH_F0065",
        "WH_F0066",
        "WH_F0067",
        "WH_F0068",
        "WH_F0069",
        "WH_F0070",
        "WH_F0073",
        "WH_F0074",
        "WH_F0076",
        "WH_F0077",
        "WH_F0078",
        "WH_F0079",
        "WH_F0080",
        "WH_F0081",
        "WH_F0082",
        "WH_F0083",
        "WH_F0084",
        "WH_F0085",
        "WH_F0086",
        "WH_F0087",
        "WH_F0089",
        "WH_F0090",
        "WH_F0091",
        "WH_F0092",
        "WH_F0093",
        "WH_F0094",
        "WH_F0095",
        "WH_F0096",
        "WH_F0097",
        "WH_F0098",
        "WH_F0099",
        "WH_F0100",
        "WH_F0101",
        "WH_F0102",
        "WH_F0103",
        "WH_F0104",
        "WH_F0105",
        "WH_F0107",
        "WH_F0108",
        "WH_F0109",
        "WH_F0110",
        "WH_F0111",
        "WH_F0112",
        "WH_F0113",
        "WH_F0115",
        "WH_F0116",
        "WH_F0117",
        "WH_F0118",
        "WH_F0119",
        "WH_F0120",
        "WH_F0121",
        "WH_F0122",
        "WH_F0123",
        "WH_F0125",
        "WH_F0126",
        "WH_F0128",
        "WH_F0129",
        "WH_F0130",
        "WH_F0131",
        "WH_F0132",
        "WH_F0133",
        "WH_F0134",
        "WH_F0135",
        "WH_F0136",
        "WH_F0138",
        "WH_F0139",
        "WH_F0140",
        "WH_F0141",
        "WH_F0142",
        "WH_F0143",
        "WH_F0145",
        "WH_F0146",
        "WH_F0148",
        "WH_F0149",
        "WH_F0150",
        "WH_F0151",
        "WH_F0152",
        "WH_F0153",
        "WH_F0154",
        "WH_F0155",
        "WH_F0156",
        "WH_F0158",
        "WH_F0159",
        "WH_F0160",
        "WH_F0161",
        "WH_F0162",
        "WH_F0163",
        "WH_F0164",
        "WH_F0166",
        "WH_F0168",
        "WH_F0169",
        "WH_F0170",
        "WH_F0171",
        "WH_F0172",
        "WH_F0173",
        "WH_F0174",
        "WH_F0175",
        "WH_F0176",
        "WH_F0177",
        "WH_F0178",
        "WH_F0179",
        "WH_F0180",
        "WH_F0181",
        "WH_F0182",
        "WH_F0184",
        "WH_F0185",
        "WH_F0186",
        "WH_F0187",
        "WH_F0188",
        "WH_F0189",
        "WH_F0190",
        "WH_F0191",
        "WH_F0192",
        "WH_F0193",
        "WH_F0194",
        "WH_F0195",
        "WH_F0201",
        "WH_F0202",
        "WH_F0203",
        "WH_F0206",
        "WH_F0208",
        "WH_F0209"
    ],
    "news": [
        "WH_CTN0026",
        "WH_N0001",
        "WH_N0002",
        "WH_N0003",
        "WH_N0004",
        "WH_N0005",
        "WH_N0006",
        "WH_N0007",
        "WH_N0008",
        "WH_N0010",
        "WH_N0012",
        "WH_N0014",
        "WH_N0015",
        "WH_N0017",
        "WH_N0018",
        "WH_N0019",
        "WH_N0020",
        "WH_N0021",
        "WH_N0022",
        "WH_N0023",
        "WH_N0032",
        "WH_N0038",
        "WH_N0039",
        "WH_N0042",
        "WH_N0044",
        "WH_N0045",
        "WH_N0047",
        "WH_N0048",
        "WH_N0055",
        "WH_N0058",
        "WH_N0059",
        "WH_N0060",
        "WH_N0061",
        "WH_N0062",
        "WH_N0063",
        "WH_N0064",
        "WH_N0065",
        "WH_N0066",
        "WH_N0067",
        "WH_N0068",
        "WH_N0069",
        "WH_N0071",
        "WH_N0087",
        "WH_N0096",
        "WH_N0103",
        "WH_N0105",
        "WH_N0106",
        "WH_N0107",
        "WH_N0108",
        "WH_N0109",
        "WH_N0110",
        "WH_N0111",
        "WH_N0112",
        "WH_N0113",
        "WH_N0114",
        "WH_N0115",
        "WH_N0116",
        "WH_N0117",
        "WH_N0118",
        "WH_N0119",
        "WH_N0120",
        "WH_N0121",
        "WH_N0122",
        "WH_N0123",
        "WH_N0124",
        "WH_N0125",
        "WH_N0126",
        "WH_N0127",
        "WH_N0128",
        "WH_N0129",
        "WH_N0130",
        "WH_N0131",
        "WH_N0132",
        "WH_N0133",
        "WH_N0134",
        "WH_N0135",
        "WH_N0136",
        "WH_N0137",
        "WH_N0138",
        "WH_N0139",
        "WH_N0140",
        "WH_N0141",
        "WH_N0142",
        "WH_N0143",
        "WH_N0144",
        "WH_N0145",
        "WH_N0146",
        "WH_N0147",
        "WH_N0148",
        "WH_N0149",
        "WH_N0150",
        "WH_N0152",
        "WH_N0153",
        "WH_N0154",
        "WH_N0155",
        "WH_N0156",
        "WH_N0157",
        "WH_N0158",
        "WH_N0159",
        "WH_N0160",
        "WH_N0161",
        "WH_N0162",
        "WH_N0163",
        "WH_N0164",
        "WH_N0165",
        "WH_N0166",
        "WH_N0167",
        "WH_N0168",
        "WH_N0169",
        "WH_N0170",
        "WH_N0171",
        "WH_N0172",
        "WH_N0173",
        "WH_N0174",
        "WH_N0175",
        "WH_N0176",
        "WH_N0177",
        "WH_N0178",
        "WH_N0179",
        "WH_N0180",
        "WH_N0181",
        "WH_N0182",
        "WH_N0183",
        "WH_N0186",
        "WH_N0187",
        "WH_N0188",
        "WH_N0189",
        "WH_N0190",
        "WH_N0191",
        "WH_N0192",
        "WH_N0193",
        "WH_N0194",
        "WH_N0195",
        "WH_N0196",
        "WH_N0197",
        "WH_N0198",
        "WH_N0199",
        "WH_N0200",
        "WH_N0201",
        "WH_N0202",
        "WH_N0203",
        "WH_N0204",
        "WH_N0205",
        "WH_N0206",
        "WH_N0207",
        "WH_N0208",
        "WH_N0209",
        "WH_N0210",
        "WH_N0211",
        "WH_N0212",
        "WH_N0213",
        "WH_N0214",
        "WH_N0215",
        "WH_N0216",
        "WH_N0217",
        "WH_N0218",
        "WH_N0219",
        "WH_N0220",
        "WH_N0221",
        "WH_N0222",
        "WH_N0223",
        "WH_N0224",
        "WH_N0225",
        "WH_N0226",
        "WH_N0227",
        "WH_N0234",
        "WH_N0235",
        "WH_N0236",
        "WH_N0237",
        "WH_N0239",
        "WH_N0242",
        "WH_N0244",
        "WH_N0245",
        "WH_N0251",
        "WH_N0252",
        "WH_N0253",
        "WH_N0254",
        "WH_N0255",
        "WH_N0256",
        "WH_N0257",
        "WH_N0258",
        "WH_N0259",
        "WH_N0260",
        "WH_N0271",
        "WH_N0272",
        "WH_N0280",
        "WH_N0281",
        "WH_N0282",
        "WH_N0283",
        "WH_N0284",
        "WH_N0285",
        "WH_N0286",
        "WH_N0287",
        "WH_N0288",
        "WH_N0289",
        "WH_N0290",
        "WH_N0291",
        "WH_N0292",
        "WH_N0293",
        "WH_N0294",
        "WH_N0295",
        "WH_N0296",
        "WH_N0297",
        "WH_N0298",
        "WH_N0299",
        "WH_N0300",
        "WH_N0301",
        "WH_N0302",
        "WH_N0303",
        "WH_N0304",
        "WH_N0305",
        "WH_N0306",
        "WH_N0307",
        "WH_N0308",
        "WH_N0309",
        "WH_N0313",
        "WH_N0314",
        "WH_N0315",
        "WH_N0316",
        "WH_N0317",
        "WH_N0318",
        "WH_N0319",
        "WH_N0320",
        "WH_N0321",
        "WH_N0322",
        "WH_N0327",
        "WH_N0328",
        "WH_N0329",
        "WH_N0330",
        "WH_N0331",
        "WH_N0334",
        "WH_N0335",
        "WH_N0336",
        "WH_N0337",
        "WH_N0338",
        "WH_N0339",
        "WH_N0340",
        "WH_N0341",
        "WH_N0342",
        "WH_N0343",
        "WH_N0344",
        "WH_N0345",
        "WH_N0346",
        "WH_N0347",
        "WH_N0354",
        "WH_N0355",
        "WH_N0356",
        "WH_N0357",
        "WH_N0360",
        "WH_N0362",
        "WH_N0364",
        "WH_N0368",
        "WH_N0369",
        "WH_N0370",
        "WH_N0371",
        "WH_N0372",
        "WH_N0373",
        "WH_N0374",
        "WH_N0375",
        "WH_N0376",
        "WH_N0377",
        "WH_N0378",
        "WH_N0379",
        "WH_N0380",
        "WH_N0381",
        "WH_N0382",
        "WH_N0383",
        "WH_N0384",
        "WH_N0385",
        "WH_N0387",
        "WH_N0388",
        "WH_N0389",
        "WH_N0390",
        "WH_N0406",
        "WH_N0416",
        "WH_N0417",
        "WH_N0418",
        "WH_N0419",
        "WH_N0420",
        "WH_N0442",
        "WH_N0443",
        "WH_N0444",
        "WH_N0445",
        "WH_N0446",
        "WH_N0447",
        "WH_N0448",
        "WH_N0449",
        "WH_N0450",
        "WH_N0451",
        "WH_N0452",
        "WH_N0453",
        "WH_N0454",
        "WH_N0455",
        "WH_N0456",
        "WH_N0457",
        "WH_N0458",
        "WH_N0459",
        "WH_N0460",
        "WH_N0461",
        "WH_N0462",
        "WH_N0463",
        "WH_N0464",
        "WH_N0465",
        "WH_N0471",
        "WH_N0472",
        "WH_N0473",
        "WH_N0474",
        "WH_N0475",
        "WH_N0494",
        "WH_N0495",
        "WH_N0496",
        "WH_N0497",
        "WH_N0498",
        "WH_N0542",
        "WH_N0543",
        "WH_N0544",
        "WH_N0545",
        "WH_N0546",
        "WH_N0547",
        "WH_N0548",
        "WH_N0549",
        "WH_N0550",
        "WH_N0570",
        "WH_N0571",
        "WH_N0572",
        "WH_N0573",
        "WH_N0574",
        "WH_N0575",
        "WH_N0576",
        "WH_N0577",
        "WH_N0578",
        "WH_N0579",
        "WH_N0585",
        "WH_N0586",
        "WH_N0587",
        "WH_N0588",
        "WH_N0613",
        "WH_N0614",
        "WH_N0615",
        "WH_N0616",
        "WH_N0617",
        "WH_N0618",
        "WH_N0619",
        "WH_N0620",
        "WH_N0631",
        "WH_N0640",
        "WH_N0641",
        "WH_N0642",
        "WH_N0643",
        "WH_N0645",
        "WH_N0646",
        "WH_N0647",
        "WH_N0648",
        "WH_N0649",
        "WH_N0650",
        "WH_N0651",
        "WH_N0652",
        "WH_N0653",
        "WH_N0654",
        "WH_N0655",
        "WH_N0656",
        "WH_N0657",
        "WH_N0658",
        "WH_N0659",
        "WH_N0660",
        "WH_N0661",
        "WH_N0662",
        "WH_N0663",
        "WH_N0664",
        "WH_N0665",
        "WH_N0666",
        "WH_N0667",
        "WH_N0668",
        "WH_N0669",
        "WH_N0670",
        "WH_N0671",
        "WH_N0672",
        "WH_N0673",
        "WH_N0674",
        "WH_N0675",
        "WH_N0676",
        "WH_N0677",
        "WH_N0678",
        "WH_N0679",
        "WH_N0680",
        "WH_N0681",
        "WH_N0682",
        "WH_N0683",
        "WH_N0684",
        "WH_N0685",
        "WH_N0686",
        "WH_N0687",
        "WH_N0688",
        "WH_N0689",
        "WH_N0690",
        "WH_N0691",
        "WH_N0692",
        "WH_N0693",
        "WH_N0694",
        "WH_N0695",
        "WH_N0696",
        "WH_N0697",
        "WH_N0698",
        "WH_N0699",
        "WH_N0700",
        "WH_N0701",
        "WH_N0702",
        "WH_N0703",
        "WH_N0704",
        "WH_N0705",
        "WH_N0706",
        "WH_N0707",
        "WH_N0708",
        "WH_N0709",
        "WH_N0710",
        "WH_N0711",
        "WH_N0712",
        "WH_N0713",
        "WH_N0714",
        "WH_N0715",
        "WH_N0716",
        "WH_N0717",
        "WH_N0718",
        "WH_N0719",
        "WH_N0720",
        "WH_N0721",
        "WH_N0722",
        "WH_N0723",
        "WH_N0724",
        "WH_N0725",
        "WH_N0726",
        "WH_N0727",
        "WH_N0728",
        "WH_N0729",
        "WH_N0740",
        "WH_N0741",
        "WH_N0742",
        "WH_N0743",
        "WH_N0744",
        "WH_N0745",
        "WH_N0746",
        "WH_N0747",
        "WH_N0748",
        "WH_N0749",
        "WH_N0750",
        "WH_N0751",
        "WH_N0752",
        "WH_N0753",
        "WH_N0754",
        "WH_N0759",
        "WH_N0760",
        "WH_N0761",
        "WH_N0762",
        "WH_N0763",
        "WH_NI001",
        "WH_NI002",
        "WH_NI003",
        "WH_NI004",
        "WH_NI005",
        "WH_NI006",
        "WH_NI007",
        "WH_NI008",
        "WH_NI009",
        "WH_NI010",
        "WH_NI011",
        "WH_NI012",
        "WH_NI013",
        "WH_NI014",
        "WH_NI015",
        "WH_NI016"
    ],
    "plurk": [
        "WH_F0038"
    ],
    "video": [
        "wh_v001"
    ]
}

# ==============================
#             Dump
# ==============================

TABLE_PREFIX = 'wh_panel_mapping_'

TABLE_GROUPS_FOR_INDEX = {
    'fb': ['fbfans', 'fbgroup', 'fbkol', 'fbpm', 'fbprivategroup'],
    'forum': ['forum', 'Dcard'],
    'bbs': ['Ptt'],
    'social': ['Instagram', 'Tiktok', 'Twitter', 'plurk'],
    'comment': ['Comment'],
    'youtube': ['Youtube'],
    'news': ['news'],
    'Blog': ['blog']
}

CONFLICT_GROUPS = {
    'GENDER': ['/male', '/female'],
    'MARRIAGE': ['/unmarried', '/married'],
}

LABEL = {'男性': 'male',
         '女性': 'female',
         '未婚': 'unmarried',
         '已婚': 'married',
         '孩子': 'child',
         '有子女': 'parenting',
         '青年': 'young',
         '上班族': 'employee',
         '學生': 'student'}

DUMP_COLUMNS = ('source_author', 'panel', 'create_time')

SITE_SCHEMA = 'audience-toolkit-django'

# ==============================
#          Preprocess
# ==============================

DATA_FILTER_TASK_ID_LIST = {
    "REGEX_MODEL": [2,3],
    "KEYWORD_MODEL": [4,5],
    "ALL": [2,3,4,5]
}

# ==============================
#            Model
# ==============================

MODEL_PATH_FIELD_DIRECTORY = 'model_files'

MODEL_INFORMATION = {
    "KEYWORD_MODEL": "models.rule_based_models.keyword_model.KeywordModel",
    "REGEX_MODEL": "models.rule_based_models.regex_model.RegexModel",
    "RANDOM_FOREST_MODEL": "models.trainable_models.rf_model.RandomForestModel",
    "TERM_WEIGHT_MODEL": "models.trainable_models.tw_model.TermWeightModel",
}

TERM_WEIGHT_FIELDS_MAPPING = {
    'content': '字詞',
    'label': '標籤',
    'score': '分數',
}

SAVE_DETAIL_EXTENSION = {'csv'}

MATCH_TYPE_DICT = {'比對開頭': 'start',
                   '比對結尾': 'end',
                   '完全一致': 'exactly',
                   '部分吻合': 'partially'}

# ==============================
#            Document
# ==============================

SAVE_DOCUMENT_EXTENSION = {'csv'}

# ==============================
#          Application
# ==============================

# the size of timedelta batch (hour) querying source database
TIME_INTERVAL = 1

class DevelopConfig(BaseSettings):
    API_HOST: str = '127.0.0.1'
    API_TITLE: str = 'Audience API'
    API_VERSION: float = 2.1
    CELERY_NAME: str = 'celery_worker'
    CELERY_SQL_URI: str = 'sqlite:///save.db'
    CELERY_BACKEND: str = 'db+sqlite:///save.db'
    CELERY_BROKER: str = 'redis://localhost'
    CELERY_TIMEZONE: str = 'Asia/Taipei'
    CELERY_ENABLE_UTC: bool = False
    CELERY_RESULT_EXPIRES: int = 7
    CELERY_RESULT_EXTENDED: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_ACKS_LATE: bool = True
    DUMP_ZIP: bool = False


class ProductionConfig(DevelopConfig):
    API_HOST: str = '0.0.0.0'
    CELERY_BROKER: str = 'redis://0.0.0.0'


# ==============================
#          Connection
# ==============================
class TableName:
    state = 'state'
    model_status = 'model_status'
    model_report = 'model_report'
    term_weights = 'term_weights'
    rules = 'rules'
    upload_model = 'upload_model'
    eval_details = 'eval_details'
    filter_rule = 'filter_rule'
    filter_rule_task = 'filter_rule_task'
    document_task = 'document_task'
    document_dataset = 'document_dataset'
    document_rules = 'document_rules'
    document_upload = 'document_upload'
    document_download = 'document_download'


class DatabaseConfig:
    INPUT_HOST: str = os.getenv('INPUT_HOST')
    INPUT_PORT: int = int(os.getenv('INPUT_PORT'))
    INPUT_USER: str = os.getenv('INPUT_USER')
    INPUT_PASSWORD: str = os.getenv('INPUT_PASSWORD')
    INPUT_SCHEMA: str = os.getenv('INPUT_SCHEMA')
    INPUT_TABLE: str = os.getenv('INPUT_TABLE')
    OUTPUT_HOST: str = os.getenv('OUTPUT_HOST')
    OUTPUT_PORT: int = int(os.getenv('OUTPUT_PORT'))
    OUTPUT_USER: str = os.getenv('OUTPUT_USER')
    OUTPUT_PASSWORD: str = os.getenv('OUTPUT_PASSWORD')
    OUTPUT_SCHEMA: str = os.getenv('OUTPUT_SCHEMA')
    OUTPUT_ENGINE_INFO: str = f'mysql+pymysql://{os.getenv("OUTPUT_USER")}:' \
                              f'{os.getenv("OUTPUT_PASSWORD")}@{os.getenv("OUTPUT_HOST")}:' \
                              f'{os.getenv("OUTPUT_PORT")}/{os.getenv("OUTPUT_SCHEMA")}?charset=utf8mb4'
    DUMP_FROM_SCHEMA: str = os.getenv('DUMP_FROM_SCHEMA')
    DUMP_TO_SCHEMA: str = os.getenv('DUMP_TO_SCHEMA')


class TestDatabaseConfig:
    HOST: str = os.getenv('190_HOST')
    PORT: int = int(os.getenv('190_PORT'))
    USER: str = os.getenv('190_USER')
    PASSWORD: str = os.getenv('190_PASSWORD')


LOCAL_TEST = os.getenv('LOCAL_TEST', None)


# ==============================
#          API request
# ==============================

# class TaskConfig(BaseModel):
#     START_TIME: date = "2020-01-01"
#     END_TIME: date = "2021-01-01"
#     INPUT_SCHEMA: str = os.getenv("INPUT_SCHEMA")
#     INPUT_TABLE: str = os.getenv("INPUT_TABLE")
#     COUNTDOWN: int = 5
#     QUEUE: str = "queue1"
#     MODEL_ID_LIST: List[str] = None
#     SITE_CONFIG: Optional[Dict] = None
#
#
# class AbortConfig(BaseModel):
#     TASK_ID: str = 'string'
#
#
# class DeleteConfig(BaseModel):
#     TASK_ID: str = None
#
#
# class DumpConfig(BaseModel):
#     ID_LIST: List[int] = "place task_id list or predicting_job_id list here"
#     OLD_TABLE_DATABASE: str = DatabaseConfig.DUMP_FROM_SCHEMA
#     NEW_TABLE_DATABASE: str = DatabaseConfig.OUTPUT_SCHEMA
#     DUMP_DATABASE: str = DatabaseConfig.DUMP_TO_SCHEMA
#     QUEUE: str = "queue1"
#
#
# class TaskSampleResult:
#     OUTPUT_SCHEMA: str = os.getenv('OUTPUT_SCHEMA')
#     ORDER_COLUMN: str = 'create_time'
#     NUMBER: int = 50
#     OFFSET: int = 1000
#
#
# class ModelingTrainingConfig(BaseModel):
#     # TRAINING_SCHEMA: str = os.getenv('TRAINING_SCHEMA')
#     QUEUE: str = "queue2"
#     DATASET_DB: str = 'audience-toolkit-django'
#     DATASET_NO: int = 1
#     TASK_ID: str = None
#     PREDICT_TYPE: str = PredictTarget.CONTENT.name
#     MODEL_TYPE: str = ModelType.RANDOM_FOREST_MODEL.name
#     MODEL_INFO: Dict[str, Union[str, Dict]] = {"model_path": "model_path",
#                                                "feature_model": "SGD"
#                                                }
#
#
# class ModelingTestingConfig(BaseModel):
#     QUEUE: str = "queue2"
#     DATASET_DB: str = 'audience-toolkit-django'
#     DATASET_NO: int = 1
#     TASK_ID: str = None
#     PREDICT_TYPE: str = PredictTarget.CONTENT.name
#     MODEL_TYPE: str = ModelType.RANDOM_FOREST_MODEL.name
#     MODEL_INFO: Dict[str, Union[str, Dict]] = {"model_path": "model_path"}
#
#
# class ModelingAbort(BaseModel):
#     TASK_ID: str = None
#
#
# class ModelingDelete(BaseModel):
#     TASK_ID: str = None
#
#
# class ModelingUpload(BaseModel):
#     QUEUE: str = "queue2"
#     TASK_ID: str = None
#     UPLOAD_JOB_ID: int = None

