weather
=======

This code

- checks the webpages of
    - DWD
    - ZAMG
    - KMNI ('AL' = analysis, 'PL' = prediction)
    - wetter.net
  for information regarding the "Grosswetterlage" in central / NE europe
- save the images if you want
- create an overview map containing all the relevant images


ToDo
----

* plot the text of the prognosis in reasonable way (bottom left)
* make the headings prettier 
    * date and hour formatting
    * left: analysis; right: prognosis (only KMNI)


Result should be a map similar to this:

![alt text](grosswetterlage_overview_2013_05_07_07_30_08.png "Example of resulting image")