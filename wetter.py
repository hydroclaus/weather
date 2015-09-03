# encoding: utf-8
#!/usr/bin/env python
"""
wetter.py

Created by Claus Haslauer

source: https://github.com/clausTue/weather

What this does
- check the webpages of
    - DWD
    - ZAMG
    - KMNI ('AL' = analysis, 'PL' = prediction)
    - wetter.net
      for information regarding the "Grosswetterlage" in central / NE europe
- save the images if you want
- create an overview map containing all the relevant images

20130517 -- fixed issue with string of prognose (http://stackoverflow.com/questions/16585674/multi-line-text-with-matplotlib-gridspec)
20150903 -- fixed
                - only 2 prognosis maps available now from Dutch weather service (instead of 3)
                - the times when the script is run are a bit more simplified (maybe)
"""
import sys
import urllib2
import datetime
import time
#import codecs
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import cm #, colors
from PIL import Image
import numpy as np
import re
import HTMLParser
import sched

def main():

    # ------------------------------------------------------------
    # VARIABLES to be specified

    # TODO fix that this still needs manual input
    times_to_run = gen_times_to_run(start='today', stop='in 21 days', delta='6 hours')

    # TODO fix that this points to a chosen location
    output_path = r'E:\Dropbox\segeln_spanien\out'
    #output_path = r'F:/weather_out'

    # if set to FALSE it will overwrite individual images every time
    #    it creates an overview image
    save_individual_imgs = False


    # ------------------------------------------------------------
    # START of Script

    print("The Python version is %s.%s.%s" % sys.version_info[:3])

    now = datetime.datetime.now()
    print "script started at: ", now
    print "  first image at: ", times_to_run[0]
    print "  final image at: ", times_to_run[-1]

    n_runs = len(times_to_run)

    # loop over all selected times when a map is to be created
    for cur_i, time_to_run in enumerate(times_to_run):
        print "\n-------------------------------------------"
        print 'next run at: ', time_to_run
        n_remaining = n_runs - (cur_i + 1)
        print 'after this, there are %i runs remaining' % n_remaining
        #to_run_sec = time.mktime(datetime.datetime.strptime(time_to_run, "%d-%m-%Y_%H:%M").timetuple())
        to_run_sec = time.mktime(time_to_run.timetuple())
        sche = sched.scheduler(time.time, time.sleep)
        time_to_run = to_run_sec #now + 5 #datetime.timedelta(seconds=5)
        sche.enterabs(time_to_run, 1, create_grosswetterlage_overview_map, (output_path,save_individual_imgs))

        sche.run()

    print "Done execution of wetter.py"


def create_grosswetterlage_overview_map(img_path, save_individual_imgs):

    print "start creating map"

    timestamp = time.strftime('%Y_%m_%d_%H_%M_%S')
    cur_yr = time.strftime('%Y')
    cur_month = time.strftime('%m')
    cur_day = time.strftime('%d')
    cur_day_1 = '%02i' % (int(time.strftime('%d'))+1)
    cur_day_2 = '%02i' % (int(time.strftime('%d'))+2)
    cur_day_3 = '%02i' % (int(time.strftime('%d'))+3)


    ## ----------------
    ## get current URLs

    #DWD
    dwd_img_url = 'http://www.dwd.de/bvbw/generator/DWDWWW/Content/Oeffentlichkeit/KU/KUPK/Hobbymet/Wetterkarten/Analysekarten/Analysekarten__Default__Boden__Europa__Luftdruck__Bild,property=default.png'

    #ZAMG
    zamg_base_url = 'http://www.zamg.ac.at/cms/de/wetter/wetterkarte?'
    cur_zamg_img_url, cur_zamg_ID = find_cur_ZAMG_img_url(zamg_base_url)

    # WETTER.NET
    # todo -- is this really always the same URL?
    wetnet_img_url = 'http://www.wetter.net/images/kontinente/Europa-600.jpg'
    # extra Teil fuer den String des Vorhersagetextes
    url_wetterNet_gwl = 'http://www.wetter.net/kontinent/europa-grosswetterlage.html'
    title, prognose = get_gwl_string(url_wetterNet_gwl)

    # KMNI
    url_base_KMNI = "http://www.knmi.nl/waarschuwingen_en_verwachtingen/weerkaarten.php"
    list_cur_KMNI_ids = find_cur_KMNI(url_base_KMNI)
    # make sure there are four pictures loaded
    tmp = list_cur_KMNI_ids[-1]
    while len(list_cur_KMNI_ids) < 4:
        list_cur_KMNI_ids.append(tmp)
    base_url_kmni = 'http://cdn.knmi.nl/knmi/map/page/weer/waarschuwingen_verwachtingen/weerkaarten/%s_large.gif'
    knmi_urls = []
    for cur_url_id in list_cur_KMNI_ids:
        knmi_urls.append(base_url_kmni % cur_url_id)

    # prepare all images and text
    dict_of_urls = [('dwd' , dwd_img_url, 'DWD')
                  , ('zamg' , cur_zamg_img_url, 'ZAMG')
                  , ('KNMI_AL' , knmi_urls[0], 'KMNI_'+knmi_urls[0][-14:-10])
                  , ('wetter.net' , wetnet_img_url, 'wetter.net')
                  , ('infoBox', prognose, title)
                  , ('KNMI_PL_0' , knmi_urls[1], 'KMNI_'+knmi_urls[1][-14:-10])
                  , ('KNMI_PL_1' , knmi_urls[2], 'KMNI_'+knmi_urls[2][-14:-10])
                  , ('KNMI_PL_2' , knmi_urls[3], 'KMNI_'+knmi_urls[3][-14:-10])
              #    , ('KNMI_PL_3' , knmi_PL3_img_url, 'KMNI_'+knmi_PL3_img_url[-18:-14])
              ]

    ## -----------
    ## load images
    tmp_lst_imgs = []
    print 'loading maps: ',
    for cur_url_id in dict_of_urls:
        if cur_url_id[0] == 'infoBox':
            continue
        print '...', cur_url_id[0],
        if cur_url_id[0][:4]=="KNMI":
            file_extension = 'gif'
        else:
            file_extension = cur_url_id[1][-3:]

        if save_individual_imgs == True:
            picString =  'img_' + timestamp  + '_' + cur_url_id[0] + "." + file_extension
        else:
            # make a string such that images are overwritten in each run
            picString = 'img_' + cur_url_id[0] + "." + file_extension

        img_dst = os.path.join(img_path, picString)

        imgRequest = urllib2.Request(cur_url_id[1])
        imgData = urllib2.urlopen(imgRequest).read()

        output = open(img_dst,'wb')
        output.write(imgData)
        output.close()

        tmp_lst_imgs.append(img_dst)


    ## --------------------
    ## make composite image

    # loop over image list
    plt.close('all')
    fig = plt.figure(figsize=(5, 10))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.1)

    n_rows = 5
    outer_grid = gridspec.GridSpec(n_rows, 2 )# ,wspace=0.0, hspace=0.0

    print '\nmaking overview map: ',
    for cur_map_id, map_dict in enumerate(dict_of_urls):
        #print cur_map_id
        cur_row = (cur_map_id % n_rows)
        if cur_map_id / n_rows == 0:
            cur_column = 0
        else:
            cur_column = 1
        print '...', map_dict[0],

        # preparation: no axes
        ax = plt.subplot(outer_grid[cur_row, cur_column], frameon=False)
        ax.axes.get_yaxis().set_visible(False)
        ax.axes.get_xaxis().set_visible(False)

        # fix for the fact that the fourth entry is text and not in tmp_lst_imgs
        if cur_map_id > 4:
            cur_map_id = cur_map_id - 1

        # the actual plotting
        if map_dict[0] in ['wetter.net', 'KNMI_AL', 'KNMI_PL_0', 'KNMI_PL_1', 'KNMI_PL_2']: # , 'KNMI_PL_3'
            im = plt.imread(tmp_lst_imgs[cur_map_id])
            ax.imshow(im, origin='upper') #
        elif map_dict[0] in ['dwd']:
            im = Image.open(tmp_lst_imgs[cur_map_id])#.convert("L")
            ar = np.asarray(im)
            ax.imshow(ar) #, cmap='Greys_r'
        elif map_dict[0] == 'infoBox':
            ax.text(0.05, 0.5, map_dict[1], size=6)
        else:
            #print cur_map_id
            im = plt.imread(tmp_lst_imgs[cur_map_id])
            ax.imshow(im) #√ß
        ax.set_title(map_dict[2], size=6)
        fig.add_subplot(ax)

    # TODO plot the text of the prognosis in reasonable way
    title_x_c = 0.5
    title_y_c = 0.95
    cur_date_time = time.strftime('%Y_%m_%d_%H_%M_%S')
    outfig_name = '_grosswetterlage_overview_' + cur_date_time + ".png"
    plt.savefig(os.path.join(img_path, outfig_name), dpi=300, bbox_inches="tight", pad_inches=0)

    print "\ndone!"

def gen_times_to_run(start='today', stop='in 1 days', delta='6 hours'):
    # old conventions:
    # dates when the script is to be run
    # dd-mm-yyy_hh:mm
    # hour in 24 hours
    # mm in 60 minutes

    # parse the start
    if start == 'today':
        cur_hour = datetime.datetime.now().hour
        #print cur_hour

        # if not in these intervals, then start at 19
        hour_intervals = [[1,6], [7,12],[13,18]]
        time_to_start = 19

        for cur_inter in hour_intervals:
            if cur_inter[0] <= cur_hour <= cur_inter[1]:
                time_to_start =cur_inter[0]

        # this is really the important time
        cur_start = datetime.datetime.today().replace(hour=time_to_start, minute=0, second=0, microsecond=0)
    else:
        raise Exception

    # parse end
    matchObj = re.search("\\s([0-9]+)\\s", stop, re.S)
    if matchObj:
        #print "matchObj.group() : ", matchObj.group()
        #print "matchObj.group(1) : ", matchObj.group(1)
        delta_days = int(matchObj.group(1))
    else:
        print "No match!!"
        raise Exception


    # parse delta
    matchObj = re.search("([0-9]+)\\s", delta, re.S)
    if matchObj:
        # print "matchObj.group() : ", matchObj.group()
        #print "matchObj.group(1) : ", matchObj.group(1)
        delta_hours = int(matchObj.group(1))
    else:
        print "No match!!"
        raise Exception

    cur_end = cur_start + datetime.timedelta(days=delta_days, hours=delta_hours)
    cur_delta = datetime.timedelta(hours=delta_hours)

    times_to_run = []
    for result in perdelta(cur_start, cur_end, cur_delta):
        times_to_run.append(result)

    return times_to_run

def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta


def get_gwl_string(url):
    aResp = urllib2.urlopen(url)
    web_pg = aResp.read()

    # parse for title
    re_title = '<h1>(Gro&szlig;wetterlage in Europa f&uuml;r den [0-9]*.[0-9]*.[0-9]*)</h1>'
    title = reFind(re_title, web_pg)
    print 'title: ', title

    # parse for prognose
    re_prognose = '<h2>Die aktuelle Wetterprognose zur Gro&szlig;wetterlage</h2>\s([\w\&\;\,\.\-\s]*)'
    prognose = reFind(re_prognose, web_pg)


    #match 80 characters, plus some more, until a space is reached
    pattern = re.compile(r'(.{70}\w*?)(\s)')
    #keep the '80 characters, plus some more' and substitute the following space with new line
    prognose = pattern.sub(r'\1\n', prognose)
    print 'prognose: ', prognose

    return title, prognose

def reFind(re_string, txt_string):
    #print "IN reFIND()"
    #print "re_string: ", re_string
    regEx = re.compile(re_string)
    str_html = re.findall(regEx, txt_string)
    #print str_html
    if len(str_html)==0:
        raise Exception

    h = HTMLParser.HTMLParser()
    str_from_txt = h.unescape(str_html[0]).strip()
    return str_from_txt

def find_cur_KMNI(url):
    """
    find the names of the current files of the images of analysis and prediction of the Dutch Weather service
    """
    # find the 
    aResp = urllib2.urlopen(url)
    web_pg = aResp.read()
    re_cur_inds = 'href="//cdn.knmi.nl/knmi/map/page/weer/waarschuwingen_verwachtingen/weerkaarten/([APL]*[0-9]*)_large.gif"'
    cur_IDs = re.findall(re_cur_inds, web_pg)

    if len(cur_IDs) !=4:
        # previously there were 4 maps available (1 analysis, 3 predictions)
        # this is not the case anymore
        # hence, an error is printed, not an exception raised
        print "=== !!! ==="
        print "The Dutch don't have 4 maps available, as they usually do"
        print "=== !!! ==="
        # raise Exception

    return cur_IDs

def find_cur_ZAMG_img_url(url):
    aResp = urllib2.urlopen(url)
    web_pg = aResp.read()
    zamg_re = "<img src=\"(http://www.zamg.ac.at/fix/wetter/bodenkarte/[0-9]*/[0-9]*/[0-9]*/BK_BodAna_Sat_([0-9]*).png)\" border=\"0\" />"


    cur_id = re.findall(zamg_re, web_pg)
    return cur_id[0][0], cur_id[0][1]


if __name__ == '__main__':
    main()