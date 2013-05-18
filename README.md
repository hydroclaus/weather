weather
=======

This code

- is inspired by [this article][1] on "small data"
- checks the following webpages for information regarding the "Grosswetterlage" in central / NE europe:
    - [DWD][2]
    - [ZAMG][3]
    - [KMNI][4] ('AL' = analysis, 'PL' = prediction)
    - [wetter.net][5]
* save the individual images if you want
* create an overview map containing all the relevant images;
    * left column: analysis (current time)
    * right column: prediction (future)
    * these overview maps can be stored
    * these stored files are interesting to analyze in their sequence over time (compared with the predictions)
* this might be useful for preparing skiing or sailing trips, or just general curiosity


## ToDo

* **done 20130517** plot the text of the prognosis in reasonable way (bottom left)
* make the headings prettier 
    * date and hour formatting
    * left: analysis; right: prognosis (only KMNI)
* find out when a png is flipped and when it is ok


## Example Output
![alt text](grosswetterlage_overview_2013_05_07_07_30_08.png "Example of resulting image")

## License
CC BY-NC 3.0

see [creativecommons webpage][6]
## Changelog

### 0.1 2013-05-10

* initial commit
* basic functionality

[1]: http://m.guardian.co.uk/news/datablog/2013/apr/25/forget-big-data-small-data-revolution
[2]: http://www.dwd.de/bvbw/appmanager/bvbw/dwdwwwDesktop?_nfpb=true&_pageLabel=_dwdwww_spezielle_nutzer_hobbymeteorologen_karten&T19603831211153462939953gsbDocumentPath=Navigation%2FOeffentlichkeit%2FSpezielle__Nutzer%2FHobbymet%2FWetterkarten%2FAnalysekarten%2FAnalysekarten__Boden__Luftdruck__Westeuropa__node.html%3F__nnn%3Dtrue
[3]: http://www.zamg.ac.at/cms/de/wetter/wetterkarte
[4]: http://www.knmi.nl/waarschuwingen_en_verwachtingen/weerkaarten.php
[5]: http://www.wetter.net/kontinent/europa-grosswetterlage.html
[6]: http://creativecommons.org/licenses/by-nc/3.0/