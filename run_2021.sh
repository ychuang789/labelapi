 declare -a arr=("wh_bbs_01" "wh_bbs_02" "wh_forum_01" "wh_forum_02" "wh_backpackers" "wh_blog_01" "wh_comment_01" "wh_comment_app"
 "wh_comment_podcast" "wh_fb" "wh_fb_group" "wh_fb_kol" "wh_fb_private_group" "wh_instagram"
 "wh_news_01" "wh_news_02" "wh_news_03" "wh_news_import" "wh_tiktok" "wh_twitter" "wh_youtube"
 "wh_fb_ex_06" "wh_fb_ex_05" "wh_fb_ex_04" "wh_fb_ex_03" "wh_fb_ex_02" "wh_fb_ex" "wh_fb_pm" "wh_plurk")

#declare -a arr=("wh_bbs_01" "wh_bbs_02" "wh_forum_01" "wh_forum_02")
#declare -a arr=("wh_backpackers" "wh_blog_01" "wh_comment_01" "wh_comment_app")
#declare -a arr=("wh_comment_podcast" "wh_fb" "wh_fb_group" "wh_fb_ex")
#declare -a arr=("wh_news_01" "wh_news_02" "wh_news_03" "wh_news_import")
#declare -a arr=("wh_fb_ex_06" "wh_fb_ex_05" "wh_fb_ex_04" "wh_fb_ex_03")
#declare -a arr=("wh_fb_kol" "wh_fb_private_group" "wh_instagram" "wh_fb_ex_02" )
#declare -a arr=("wh_tiktok" "wh_twitter" "wh_youtube" "wh_plurk")
#declare -a arr=("wh_fb_pm")

# datetime
start_time="2021-01-01 00:00:00"
end_time="2022-01-01 00:00:00"

# models
model_type="keyword_model"
predict_type="author_name"


declare -i count=0

#for var in "$@"
#do
#  curl -X 'POST' \
#    "http://0.0.0.0:8000/api/tasks/" \
#    -H "accept: application/json" \
#    -H "Content-Type: application/json" \
#    -d '{
#    "MODEL_TYPE": "'$model_type'",
#    "PREDICT_TYPE": "'$predict_type'",
#    "START_TIME": "'$start_time'",
#    "END_TIME": "'$end_time'",
#    "INPUT_SCHEMA": "'${arr[count]}'",
#    "INPUT_TABLE": "ts_page_content",
#    "OUTPUT_SCHEMA": "audience_result",
#    "COUNTDOWN": 5,
#    "QUEUE": "'$var'"
#  }'
#  ((count=count+1))
#done

#for db in "${arr[@]}"
#do
#
#  echo $db
#  curl -X 'POST' \
#  "http://0.0.0.0:8000/api/tasks/" \
#  -H "accept: application/json" \
#  -H "Content-Type: application/json" \
#  -d '{
#  "MODEL_TYPE": "'$model_type'",
#  "PREDICT_TYPE": "'$predict_type'",
#  "START_TIME": "'$start_time'",
#  "END_TIME": "'$end_time'",
#  "INPUT_SCHEMA": "'$db'",
#  "INPUT_TABLE": "ts_page_content",
#  "OUTPUT_SCHEMA": "audience_result",
#  "COUNTDOWN": 5,
#  "QUEUE": "'$queue'"
#}'
#done
