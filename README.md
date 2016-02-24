# my_iscpif_tools


### filter_and_agg.py

**usage**

```
python3 filter_and_agg.py [-h] [-i pathto/input.json] [-d pathto/gexfdir]
```

**goal**
This script filters an elasticsearch terms aggregation (JSON) on an external list of terms...

The filtering master list can be retrieved from a directory of gexf files (which means keeping only the terms that correspond to a gexf node label) or provided as a one per line txt doc.

**options**
```
  -h, --help            show the help message and exit
  -i pathto/input.json  path to a JSON with ES-style time + terms aggregations
  -d pathto/gexfdir     the dir with the gexf with the target terms (ie their
                        //node/@label)
  -l pathto/termlist    alternative to -d : a path with a prepared master term
                        list (a txt file with one term per line)
```
