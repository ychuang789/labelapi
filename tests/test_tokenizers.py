from unittest import TestCase
from utils.tokenizers import DeepnlpPosTokenizer, JiebaTokenizer

DOCS = [
    "蘋果下半年新款 iPhone 設計外界關注。分析師預期，6.1 吋新款 LCD 版 iPhone 的上天線，可能維持 MPI 與 LCP 混合設計；新 iPhone 的 ",
    "NFC 軟板天線，也會升級到 4 層板。 天風國際證券分析師郭明錤報告預估，今年下半年 6.1 吋新款 LCD 版 iPhone 的上天線（UAT），可能仍",
    "維持軟板異質 PI（Modified PI）與液晶聚合物 LCP（Liquid crystal polymer）混合的設計。 報告指出，原因在於新 6.1 吋 LCD 版 ",
    "iPhone 是下半年新機型中的低階機種，MPI 成本較 LCP 低；此外若全採用 LCP 設計，日本廠商村田製作所（Murata）將成獨家供應商，",
    "供應風險高；再者調整設計後，MPI 仍能符合蘋果技術標準。 在軟板設計部分，報告預期，今年下半年新款 iPhone 的近距離無線通訊（NFC）",
    "軟板天線，會從 2 層板升級到 4 層板，價格也明顯增加。 展望明年新款 iPhone 設計，報告預期明年下半年新款 iPhone 將支援 5G 通訊、",
    "且 LCP 用量將增加，因此預期蘋果需要更多 LCP 供應商，降低供應風險。 此外，明年下半年高階新款有機發光二極體（OLED）版 iPhone，",
    "將採用 Y-OCTA 面板觸控技術與 COP（Chip On Pi）封裝技術，可降低成本、減少面板厚度與縮小邊框，有利外觀設計。",
    "今年新款 iPhone 規格功能各界關注，分析師預估相機鏡頭升級是今年下半年新 iPhone 最大賣點之一。其中 6.5 吋 OLED 版、5.8 吋 OLED ",
    "版和 6.1 吋 LCD 版 3 款，後置相機分別升級到 3 顆鏡頭、3 顆鏡頭與雙鏡頭。",
    "市場一般預期，今年新 iPhone 可能推出 6.5 吋 OLED 螢幕、5.8 吋 OLED 螢幕以及 6.1 吋 LCD 螢幕等 3 款機種，",
    "螢幕上方的「瀏海」面積與去年機種相同。今年新 iPhone 將支援雙向無線充電，可能均採用 Lightning 連接線，並無支援 USB Type-C 功能。",
]


class TestDeepNLPTokenizers(TestCase):
    def test_deepnlp_tokenize(self):
        docs = [doc.replace(" ", "") for doc in map(str.strip, DOCS)]
        tokenizer = DeepnlpPosTokenizer(api_host="http://127.0.0.1:5000/segment")
        rs = tokenizer.tokenize(docs)
        self.assertEqual(len(rs), len(DOCS))
        self.assertEqual(len("".join(rs[0])), len(docs[0]))

    def test_jieba_tokenize(self):
        docs = [doc.replace(" ", "") for doc in map(str.strip, DOCS)]
        tokenizer = JiebaTokenizer()
        rs = tokenizer.tokenize(docs)
        self.assertEqual(len(rs), len(DOCS))
        self.assertEqual(len("".join(rs[0])), len(docs[0]))

