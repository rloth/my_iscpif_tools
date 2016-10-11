mkdir -p newcrawled
i=0
cat terms-5042.ls | while read line ;
    do echo $((i++)) ;
      echo $line ;
      padded_id=`printf "%04d" $i` ;
      fname=`echo $line | perl -pe 's/\W+/_/g'` ;
      q_string=`echo $line | perl -pe 's/ /%20/g ; $_ = lc $_'` ;
      curl -v -A "rloth script" -X GET "https://api.iscpif.fr/1/wos/search/histogram.json?q%5B%5D=%22${q_string}%22&since=2000&until=2015" > newcrawled/${padded_id}-${fname}.json ;
      sleep .5
    done





# redoing the same but with preexisting ids
# -----------------------------------------
OLDIFS=IFS
IFS=''
i=0
cat /home/romain/tw/risk2015_scraps/recency/terms_added-43.ls | while read line ;
    do echo $((i++)) ;
      echo $line
      id=`echo -e $line | cut -f1` ;
      name=`echo -e $line | cut -f2` ;
      echo $id
      echo $name
      padded_id=`printf "%04d" $id` ;
      fname=`echo $name | perl -pe 's/\W+/_/g'` ;
      q_string=`echo $name | perl -pe 's/ /%20/g ; $_ = lc $_'` ;
      curl -v -A "rloth script" -X GET "https://api.iscpif.fr/1/wos/search/histogram.json?q%5B%5D=%22${q_string}%22&since=2000&until=2015" > newcrawled/${padded_id}-${fname}.json ;
      sleep .5
    done
IFS=OLDIFS
