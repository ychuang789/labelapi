declare -a arr=("wh_bbs_01" "wh_bbs_02" "wh_forum_01" "wh_forum_02" "wh_backpackers" "wh_blog_01" "wh_comment_01" "wh_comment_app" "wh_comment_podcast" "wh_fb" "wh_fb_group" "wh_fb_kol" "wh_fb_private_group" "wh_instagram" "wh_news_01" "wh_news_02" "wh_news_03" "wh_news_import" "wh_tiktok" "wh_twitter" "wh_youtube" "wh_fb_ex_06" "wh_fb_ex_05" "wh_fb_ex_04" "wh_fb_ex_03" "wh_fb_ex_02" "wh_fb_ex" "wh_fb_pm" "wh_plurk")

for db in "${arr[@]}"
do
  curl -X 'POST' \
  "http://0.0.0.0:8000/api/tasks/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
  "MODEL_TYPE": "keyword_model",
  "PREDICT_TYPE": "author_name",
  "START_TIME": "2021-01-01 00:00:00",
  "END_TIME": "2022-01-01 00:00:00",
  "INPUT_SCHEMA": '$db',
  "INPUT_TABLE": "ts_page_content",
  "OUTPUT_SCHEMA": "audience_result",
  "COUNTDOWN": 5,
  "QUEUE": "queue1"
}'
done
