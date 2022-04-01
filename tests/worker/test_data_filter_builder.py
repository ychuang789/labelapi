from datetime import datetime
from unittest import TestCase

from utils.data.input_example import InputExample
from workers.data_filter_builder import DataFilterBuilder

fake_data_list = [
    '我老婆的pixel 6 pro 跟我自己的lg v60 也是一樣，<BR>都是配對三星手錶active2 , line 通話時螢幕不會自動變暗。<BR>直到看了樓上的回文，<BR>把手錶語音通話功能關閉後就恢復正常了。<BR>(拿到耳邊通話時螢幕自動變暗)感謝大家幫我解決了一個困擾的問題。',
    '<BR>我這陣子被老婆狂餵食消夜...下場就是胖了2公斤....<BR>',
    '如果時光從來,我會選擇跟岳母同住,娶人家女兒又附帶未來孩子的保母,沒有房貸負擔,生活好過呀...',
    '我改天跟老婆吵架情緒低落時<BR>一定專程來找黃社長發洩一下<BR>社長這麼nice的人應該可以接受吧',
    '我是今年大三的轉學生 爬過文說體育課學分是算次的 總共要修四次 那請問 1. 可以四次都上一樣的運動嗎？ 2. 一個學期可以修兩門體育課嗎？（算學分的',
    '我超好奇大學之道是在上什麼ㄟ哈哈哈',
    '各位學長姐真的是滿足了我對大學生活的想像...']

fake_data_list_2 = ['【📣礦山小小藝術家集合囉！一日山城探險X金工DIY 等你來報名❗️】<BR>2020夏日限定🌞！礦山藝術季開跑啦！<BR>#新北市立黃金博物館 今夏特別推出【礦山玩藝術】水金九藝術教育體驗課程🎨<BR>✨地表最划算✨──💸2張國父的費用，吃喝玩樂包透透🥳<BR>✨課程超豐富✨──⛰️上午快樂山城遊，下午金工動手做🔨<BR>✨父母好輕鬆✨──👶假日小孩放這裡，爸媽逍遙放假去😎<BR>名額有限，滿了就沒啦～趕快來報名參加吧🙌<BR>——————————————————————<BR>｜活動資訊｜<BR>📅活動皆為一日課程，梯次如下：<BR>【礦山玩藝術】水金九藝術教育體驗課程<BR>7/25（六）、7/26（日）、8/1（六）<BR>【礦山玩藝術】水金九藝術教育體驗課程X古蹟月<BR>9/13（日）、9/19（六）、9/20（日）<BR>📍活動地點：新北市立黃金博物館及周邊地區<BR>🙋活動對象：國小四至六年級學童(包括小三升小四及應屆畢業生)<BR>👫招生人數：每梯次15名<BR>💰報名費用：新台幣200元整/每人每梯次（費用內含導覽、金工教材、保險、餐點、交通等）<BR>📢報名時間：即日起-7月16日（四）<BR>💡報名網頁：https://forms.gle/9MFNPyV2XxB1EMSN7<BR>☎️如有任何問題，請於上班日聯繫(02)2597-9725 廖小姐、王小姐'
]

class TestDataFilterBuilder(TestCase):
    """Test the data filter func"""
    fake_data_input = [InputExample(id_="",
                                    s_area_id="",
                                    author="",
                                    title="",
                                    content=i,
                                    post_time=datetime.now())
                       for i in fake_data_list_2]

    def setUp(self):
        self.builder = DataFilterBuilder()
        self.id_list = [1]
        self.dataset = self.fake_data_input

    # def test_get_task_instance(self):
    #     task_list = self.builder.get_task_instance(self.id_list)
    #     self.assertIsNotNone(task_list)

    def test_method_chain(self):
        output_list = self.builder.data_filter_method_chain(self.dataset, [2,3,4,5])
        self.assertNotEqual(len(output_list), len(fake_data_list))
        self.assertNotEqual(len(output_list), 0)



