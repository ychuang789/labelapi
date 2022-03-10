from datetime import datetime
from unittest import TestCase

from utils.data.input_example import InputExample
from workers.data_filter.data_filter_core import DataFilterWorker

fake_data_list = [
    '我老婆的pixel 6 pro 跟我自己的lg v60 也是一樣，<BR>都是配對三星手錶active2 , line 通話時螢幕不會自動變暗。<BR>直到看了樓上的回文，<BR>把手錶語音通話功能關閉後就恢復正常了。<BR>(拿到耳邊通話時螢幕自動變暗)感謝大家幫我解決了一個困擾的問題。',
    '<BR>我這陣子被老婆狂餵食消夜...下場就是胖了2公斤....<BR>',
    '如果時光從來,我會選擇跟岳母同住,娶人家女兒又附帶未來孩子的保母,沒有房貸負擔,生活好過呀...',
    '我改天跟老婆吵架情緒低落時<BR>一定專程來找黃社長發洩一下<BR>社長這麼nice的人應該可以接受吧',
    '我是今年大三的轉學生 爬過文說體育課學分是算次的 總共要修四次 那請問 1. 可以四次都上一樣的運動嗎？ 2. 一個學期可以修兩門體育課嗎？（算學分的',
    '我超好奇大學之道是在上什麼ㄟ哈哈哈',
    '各位學長姐真的是滿足了我對大學生活的想像...']


class TestDataFilter(TestCase):

    task_id = 1
    fake_data_input = [InputExample(id_="",
                                    s_area_id="",
                                    author="",
                                    title="",
                                    content=i,
                                    post_time=datetime.now())
                       for i in fake_data_list]

    def setUp(self):
        self.worker = DataFilterWorker(filter_task_id=self.task_id)
        self.dataset = self.fake_data_input

    def test_run_task(self):
        output_list = self.worker.run_task(self.fake_data_input)
        self.assertNotEqual(len(output_list), len(self.fake_data_input))
        self.assertNotEqual(len(output_list), 0)
