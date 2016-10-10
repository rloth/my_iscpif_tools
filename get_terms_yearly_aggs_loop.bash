i=0
cat terms-5042.ls | while read line ;
    do echo $((i++)) ;
      echo $line ;
      padded_id=`printf "%04d" $i` ;
      fname=`echo $line | perl -pe 's/\W+/_/g'` ;
      q_string=`echo $line | perl -pe 's/ /%20/g'` ;
      curl -v -A "rloth script" -X GET "https://api.iscpif.fr/1/wos/search/histogram.json?q%5B%5D=%22${q_string}%22&since=2000&until=2015" > crawled/${padded_id}-${fname}.json ;
      sleep .15
    done
