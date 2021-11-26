declare -a arr=("wh_panel_mapping_forum" "wh_panel_mapping_bbs"
"wh_panel_mapping_social" "wh_panel_mapping_comment"
"wh_panel_mapping_youtube" "wh_panel_mapping_news" "wh_panel_mapping_Blog"
)

for tb in "${arr[@]}"
do
  mysqldump -urd2 -peland4321 -h172.18.20.190 -P3306 --lock-tables=false audience_result $tb | zip > /home/deeprd2/audience_production/2021_11_26/$tb.zip
done
