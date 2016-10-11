# continuation for get_terms_yearly_aggs_loop

ls | while read fnam ;
  do
    our_id=`echo $fnam | perl -pe 's/-.*$//'` ;
    realnam=`echo $fnam | perl -pe 's/^\d+-//;s/_.json$//'` ;
    tsvline=`jq -r ".aggs.publicationCount.buckets | map(.doc_count|tostring)| join(\"\t\")" < $fnam` ;
    # tsv output
    echo -e "$our_id\t$realnam\t$tsvline"
  done



# example results:
# id  label 2000	2001	2002	2003	2004	2005	2006	2007	2008	2009	2010	2011	2012	2013	2014	2015
# 0001	AA_genotype	20	23	42	45	55	70	78	99	99	123	162	156	230	214	253	263
# 0002	ACE_inhibitors	385	373	385	402	367	359	330	312	284	262	232	239	191	193	191	127
# 0003	ACL_injury	15	13	27	17	25	30	48	50	53	75	98	85	101	91	109	120
# 0004	ACR	96	123	146	141	153	165	200	193	237	226	258	340	393	494	420	366
# 0005	ACS	233	293	321	437	528	652	714	877	854	998	1133	1190	1250	1460	1493	1293




# ============================
# jq: exemple on one filename
# ============================
#
# ------
# SOURCE
# ------
# {"took": 11, "total": 11033,
#   "aggs": {"publicationCount": {"buckets": [
#         {"key": 2000, "doc_count": 485},
#         {"key": 2001, "doc_count": 518},
#         {"key": 2002, "doc_count": 533},
#         {"key": 2003, "doc_count": 632},
#         {"key": 2004, "doc_count": 581},
#         {"key": 2005, "doc_count": 601},
#         {"key": 2006, "doc_count": 621},
#         {"key": 2007, "doc_count": 660},
#         {"key": 2008, "doc_count": 746},
#         {"key": 2009, "doc_count": 733},
#         {"key": 2010, "doc_count": 768},
#         {"key": 2011, "doc_count": 806},
#         {"key": 2012, "doc_count": 855},
#         {"key": 2013, "doc_count": 883},
#         {"key": 2014, "doc_count": 904},
#         {"key": 2015, "doc_count": 707}
#       ]
#     }
#   },
#   "hits": {"total": 11033, "max_score": 0, "hits": [] }
# }
#
# -------------
# make tsvline
# -------------
# jq -r ".aggs.publicationCount.buckets | map(.doc_count|tostring)| join(\"\t\")" 5042-zooplankton_.json
#
# -------
# RESULT
# -------
# > 485	518	533	632	581	601	621	660	746	733	768	806	855	883	904	707
