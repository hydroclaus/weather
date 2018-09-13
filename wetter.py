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

revisions:
20130517 -- fixed issue with string of prognose (http://stackoverflow.com/questions/16585674/multi-line-text-with-matplotlib-gridspec)
201505   -- fixed KMNI service update
20151103 -- updated DWD service update
20160517 -- updated to python 3.5 including UTF-8 decoding
"""
import sys
import datetime
import time
import os
import re
import numpy as np
import urllib
from PIL import Image

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import html.parser
import sched
import html


def main():

    # ------------------------------------------------------------
    # VARIABLES to be specified

    # TODO fix that this still needs manual input
    times_to_run = gen_times_to_run(start='today', stop='in 21 days', delta='6 hours')
    # runs every 6 hours at UTC +49min (waiting 49min for update of ZAMG image)
    # UTC       Stuttgart   Athens
    #  0         2           3       dwd aendert analysekarte
    #  6         8           9
    # 12        14          15       dwd aendert analysekarte
    # 18        20          21

    my_dpi = 500

    # TODO fix that this points to a chosen location
    # segeln_spanien directory
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    # cur_dir = os.path.normpath(join(os.getcwd(), path))
    print(cur_dir)
    ssdir = os.path.split(cur_dir)[0]
    print(ssdir)
    output_path = os.path.join(ssdir, 'out')
    print(output_path)
    #output_path = r'F:/weather_out'

    # if set to FALSE it will overwrite individual images every time
    #    it creates an overview image
    save_individual_imgs = False

    # ------------------------------------------------------------
    # START of Script

    print(("The Python version is %s.%s.%s" % sys.version_info[:3]))

    now = datetime.datetime.now()
    print("script started at: ", now)
    print("  first image at: ", times_to_run[0])
    print("  final image at: ", times_to_run[-1])

    n_runs = len(times_to_run)

    # loop over all selected times when a map is to be created
    for cur_i, time_to_run in enumerate(times_to_run):
        print("\n-------------------------------------------")
        print('next run at: ', time_to_run)
        n_remaining = n_runs - (cur_i + 1)
        print('after this, there are %i runs remaining' % n_remaining)
        #to_run_sec = time.mktime(datetime.datetime.strptime(time_to_run, "%d-%m-%Y_%H:%M").timetuple())
        to_run_sec = time.mktime(time_to_run.timetuple())
        sche = sched.scheduler(time.time, time.sleep)
        time_to_run = to_run_sec #now + 5 #datetime.timedelta(seconds=5)
        sche.enterabs(time_to_run, 1, create_grosswetterlage_overview_map, (output_path, save_individual_imgs, my_dpi))

        sche.run()

    print("Done execution of wetter.py")


def create_grosswetterlage_overview_map(img_path, save_individual_imgs, my_dpi):
    """
    makes the overview weater-maps and forecast png
    """
    font_size = 16
    print("start creating map")

    timestamp = time.strftime('%Y_%m_%d_%H_%M_%S')
    cur_yr = time.strftime('%Y')
    cur_yr_short = time.strftime('%y')
    cur_month = time.strftime('%m')
    cur_day = time.strftime('%d')
    cur_hour = time.strftime('%H')

    now_utc = datetime.datetime.utcnow()
    cur_hour_utc = now_utc.strftime("%H")


    cur_day_1 = '%02i' % (int(time.strftime('%d'))+1)
    cur_day_2 = '%02i' % (int(time.strftime('%d'))+2)
    cur_day_3 = '%02i' % (int(time.strftime('%d'))+3)

    # ----------------
    # get current URLs
    # DWD

    dwd_img_url = 'http://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/bwk_bodendruck_na_ana.png'
    dwd_img_url_24 = 'http://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/ico_tkboden_na_024.png'
    dwd_img_url_36 = 'http://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/ico_tkboden_na_036.png'
    dwd_img_url_48 = 'http://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/ico_tkboden_na_048.png'
    dwd_img_url_84 = 'http://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/ico_tkboden_na_084.png'
    dwd_img_url_108 = 'http://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/ico_tkboden_na_108.png'

    # ZAMG
    zamg_base_url = 'http://www.zamg.ac.at/cms/de/wetter/wetterkarte?'
    cur_zamg_img_url, cur_zamg_ID = find_cur_ZAMG_img_url(zamg_base_url)

    # backup if reading does not work
    # BK_timestamp = cur_yr_short + cur_month + cur_day + cur_hour_utc + '00'
    # cur_zamg_img_url = 'https://www.zamg.ac.at/fix/wetter/bodenkarte/' + cur_yr + '/' + cur_month +'/' + cur_day + '/BK_BodAna_Sat_' + BK_timestamp + '.png'
    # print("cur_zamg_img_url")

    # WETTER.NET
    # todo -- is this really always the same URL?
    wetnet_img_url = 'http://www.wetter.net/images/kontinente/Europa-600.jpg'
    # extra Teil fuer den String des Vorhersagetextes
    url_wetterNet_gwl = 'http://www.wetter.net/kontinent/europa-grosswetterlage.html'
    # title, prognose = get_gwl_string(url_wetterNet_gwl)

    # Seewetterbericht
    dwd_seewetter_url = 'https://www.dwd.de/DE/leistungen/seewettermittelmeer/seewettermittelmeer.html?nn=392762'
    issued, wetterlage_ausgabezeit, wetterlage, windvorhersage = get_seewetter(dwd_seewetter_url)
    title = "DWD Seewetterlage: " + issued + " " + wetterlage_ausgabezeit
    prognose = wetterlage.replace(". ", ".\n") + windvorhersage

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
        knmi_urls.append(base_url_kmni % cur_url_id.decode("utf-8"))

    # the second las and last number indicate plotting position:
    #     the second last number: column id
    #     the last number: row id
    # this is hard coded, because the weather websites seem to change there services quite
    #                     a bit (and this changes plotting positions)
    #  , ('wetter.net' , wetnet_img_url, 'wetter.net', 0, 3)
    dict_of_urls = [('dwd', dwd_img_url, 'DWD', 0, 0),
                    ('zamg', cur_zamg_img_url, 'ZAMG', 0, 1),
                    ('KNMI_AL', knmi_urls[0], 'KMNI_' + knmi_urls[0][-14:-10], 0, 2),
                    ('infoBox', prognose, title, 0, 4),
                    ('KNMI_PL_0', knmi_urls[1], 'KMNI_' + knmi_urls[1][-14:-10], 1, 0),
                    ('KNMI_PL_1', knmi_urls[2], 'KMNI_' + knmi_urls[2][-14:-10], 1, 1),
                    ('KNMI_PL_2', knmi_urls[3], 'KMNI_' + knmi_urls[3][-14:-10], 1, 2),
                    ('dwd24', dwd_img_url_24, 'DWD +24H', 2, 0),
                    ('dwd36', dwd_img_url_36, 'DWD +36H', 2, 1),
                    ('dwd48', dwd_img_url_48, 'DWD +48H', 2, 2),
                    ('dwd84', dwd_img_url_84, 'DWD +84H', 2, 3),
                    ('dwd108', dwd_img_url_108, 'DWD +108H', 2, 4),
                    ]

    # ============================================================
    # load images and saving into list of variables `tmp_lst_imgs`
    tmp_lst_imgs = []
    print('loading maps: ', end=' ')
    for cur_url_id in dict_of_urls:
        print('...', cur_url_id[0], end=' ')

        if cur_url_id[0] == 'infoBox':
            continue

        if cur_url_id[0][:4]=="KNMI":
            file_extension = 'gif'
        else:
            file_extension = cur_url_id[1][-3:]

        if save_individual_imgs == True:
            pic_string = 'img_' + timestamp + '_' + cur_url_id[0] + "." + file_extension
        else:
            # make a string such that images are overwritten in each run
            pic_string = 'img_' + cur_url_id[0] + "." + file_extension

        # actually loading the URL
        img_dst = os.path.join(img_path, pic_string)
        img_request = urllib.request.Request(cur_url_id[1])
        try:
            img_data = urllib.request.urlopen(img_request).read()
        except urllib.error.HTTPError as e:
            error_string = f"\nthrown error while processing: {cur_url_id[0]} \n Processing URL {cur_url_id[1]} \n {e.code} \n {e.msg}"
            print(error_string)
            fobj = open(os.path.join(img_path, f'error_{timestamp}_stuttgart.txt'), 'w')
            fobj.writelines(error_string)
            fobj.close()
            pass

        output = open(img_dst, 'wb')
        output.write(img_data)
        output.close()
        print("img saved to: ", img_dst)
        tmp_lst_imgs.append(img_dst)  # da stehen variablen mit images drin

    # ============================================================
    # make composite image with matplotlib
    print('\nmaking overview map: ', end=' ')
    # query width and height of DWD analysekarte
    im_dwd_analyse = Image.open(tmp_lst_imgs[0])
    analyse_width, analyse_height = im_dwd_analyse.size

    # setup of plot parameters
    n_columns_axes = 3  # number of columns in the plot
    n_rows_axes = 5
    # dimensions of the plot depending on specified dpi (given at the top)
    fig_size_x = analyse_width/my_dpi * n_columns_axes
    fig_size_y = analyse_height/my_dpi * n_rows_axes

    plt.close('all')

    fig = plt.figure(figsize=(fig_size_x, fig_size_y))
    plt.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.1)
    outer_grid = gridspec.GridSpec(n_rows_axes,
                                   n_columns_axes )

    for cur_map_id, map_dict in enumerate(dict_of_urls):

        cur_row = map_dict[-1]
        cur_column = map_dict[-2]

        print('...', map_dict[0], end=' ')

        # preparation: no axes
        print("cur_row", cur_row)
        ax = plt.subplot(outer_grid[cur_row, cur_column], frameon=False)
        ax.axes.get_yaxis().set_visible(False)
        ax.axes.get_xaxis().set_visible(False)

        # fix for the fact that the fourth entry is text and not in tmp_lst_imgs
        if cur_map_id > 4:
            cur_map_id = cur_map_id - 1

        # the actual plotting
        if map_dict[0] in ['KNMI_AL', 'KNMI_PL_0', 'KNMI_PL_1', 'KNMI_PL_2']:  # , 'KNMI_PL_3' 'wetter.net'
            im = plt.imread(tmp_lst_imgs[cur_map_id])
            ax.imshow(im, origin='upper')
        elif map_dict[0] in ['dwd', 'dwd24', 'dwd36', 'dwd48', 'dwd84']:
            im = Image.open(tmp_lst_imgs[cur_map_id])
            ar = np.asarray(im)
            ax.imshow(ar)

        elif map_dict[0] == 'infoBox':
            ax.text(0.05, 0.15, map_dict[1], size=font_size, ha='left', wrap=True)
        else:
            # print cur_map_id
            im = plt.imread(tmp_lst_imgs[cur_map_id])
            ax.imshow(im)
        ax.set_title(map_dict[2], size=font_size)
        fig.add_subplot(ax)

        cur_row += 1

    cur_date_time = time.strftime('%Y_%m_%d_%H_%M_%S')
    out_fig_name = '_grosswetterlage_overview_' + cur_date_time + ".png"
    plt.savefig(os.path.join(img_path, out_fig_name),
                dpi=my_dpi,
                bbox_inches="tight",
                pad_inches=0)

    # try compression
    im = Image.open(os.path.join(img_path, out_fig_name))
    im2 = im.convert('RGB').convert('P', palette=Image.ADAPTIVE)
    out_fig_name_adaptive = '_grosswetterlage_overview_' + cur_date_time + "_RGB_adaptive.png"
    im2.save(os.path.join(img_path, out_fig_name_adaptive), format='PNG')

    # todo delete out_fig_name

    print("\ndone!")


def gen_times_to_run(start='today', stop='in 1 days', delta='6 hours'):
    # old conventions:
    # dates when the script is to be run
    # dd-mm-yyy_hh:mm
    # hour in 24 hours
    # mm in 60 minutes

    # parse the start
    if start == 'today':
        cur_hour = datetime.datetime.now().hour

        # if not in these intervals, then start at 19
        # WINTERZEIT
        # hour_intervals = [[1,6], [7,12],[13,18]]
        # time_to_start = 19
        # SOMMERZEIT
        hour_intervals = [[2,7], [8,13],[14,19], [20,1]]
        time_to_start = 21

        for cur_inter in hour_intervals:
            if cur_inter[0] <= cur_hour <= cur_inter[1]:
                time_to_start = cur_inter[0]

        # this is really the important time
        cur_start = datetime.datetime.today().replace(hour=time_to_start, minute=10, second=0, microsecond=0)
    else:
        raise Exception

    # parse end
    matchObj = re.search("\\s([0-9]+)\\s", stop, re.S)
    if matchObj:
        delta_days = int(matchObj.group(1))
    else:
        print("No match!!")
        raise Exception

    # parse delta
    matchObj = re.search("([0-9]+)\\s", delta, re.S)
    if matchObj:
        delta_hours = int(matchObj.group(1))
    else:
        print("No match!!")
        raise Exception

    # end within delta_days, but add also the delta_hours so the final time is the one desired
    cur_end = cur_start + datetime.timedelta(days=delta_days, hours=delta_hours)
    cur_delta = datetime.timedelta(hours=delta_hours)
#     cur_start = datetime.datetime.now()
#     cur_end = datetime.datetime.now().replace(hour=19) + datetime.timedelta(days=1)
#     cur_delta = datetime.timedelta(hours=8)

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
    aResp = urllib.request.urlopen(url)
    web_pg = aResp.read()

    # parse for title
    re_title = b'<h1>(Gro&szlig;wetterlage in Europa f&uuml;r den [0-9]*.[0-9]*.[0-9]*)</h1>'
    title = reFind(re_title, web_pg)
    print('title: ', title)

    # parse for prognose
    re_prognose = b'<h2>Die aktuelle Wetterprognose zur Gro&szlig;wetterlage</h2>\s([\w\&\;\,\.\-\s]*)'
    prognose = reFind(re_prognose, web_pg)

    # match 80 characters, plus some more, until a space is reached
    pattern = re.compile(r'(.{70}\w*?)(\s)')
    # keep the '80 characters, plus some more' and substitute the following space with new line
    prognose = pattern.sub(r'\1\n', prognose)
    print('prognose: ', prognose)

    return title, prognose


def reFind(re_string, txt_string):
    # print "IN reFIND()"
    # print "re_string: ", re_string
    regEx = re.compile(re_string)
    str_html = re.findall(regEx, txt_string)
    if len(str_html)==0:
        raise Exception

    h = html.parser.HTMLParser()
    str_from_txt = h.unescape(str_html[0].decode("utf-8")).strip()
    return str_from_txt


def find_cur_KMNI(url):
    """
    find the names of the current files of the images of analysis and prediction of the Dutch Weather service
    """
    aResp = urllib.request.urlopen(url)
    web_pg = aResp.read()
    re_cur_inds = b'href="//cdn.knmi.nl/knmi/map/page/weer/waarschuwingen_verwachtingen/weerkaarten/([APL]*[0-9]*)_large.gif"'
    cur_IDs = re.findall(re_cur_inds, web_pg)

    if len(cur_IDs) !=4:
        # previously there were 4 maps available (1 analysis, 3 predictions)
        # this is not the case anymore
        # hence, an error is printed, not an exception raised
        print("=== !!! ===")
        print("The Dutch don't have 4 maps available, as they usually do")
        print("=== !!! ===")
        # raise Exception

    return cur_IDs


def find_cur_ZAMG_img_url(url):
    aResp = urllib.request.urlopen(url)
    web_pg = aResp.read()
    zamg_re = b"(/fix/wetter/bodenkarte/([0-9]*/[0-9]*/[0-9]*)/BK_BodAna_Sat_([0-9]*).png)"
    cur_id = re.findall(zamg_re,
                        web_pg)
    zamg_img_url = 'https://www.zamg.ac.at/' + cur_id[0][0].decode("utf-8")
    return zamg_img_url, cur_id[0][1].decode("utf-8")

def get_seewetter(dwd_seewetter_url):
    web_pg = str(urllib.request.urlopen(dwd_seewetter_url).read())

    find_issued_timestamp = r"\\nam\s([0-9]*\.[0-9]*\.[0-9]*\,\s[0-9]*\.[0-9]*\sUTC)"
    issued_re = re.findall(find_issued_timestamp, web_pg)
    issued = issued_re[0]
    print(issued)

    find_wetterlage_ausgabezeit = "Wetterlage\svon\sheute\s([0-9]*\sUTC)"
    wetterlage_ausgabezeit_re = re.findall(find_wetterlage_ausgabezeit, web_pg)
    wetterlage_ausgabezeit = wetterlage_ausgabezeit_re[0]
    print(wetterlage_ausgabezeit)

    find_wetterlage = r"</B><br\s/>\s\\n(.*)Vorhersagen\sbis"
    wetterlage_re = re.findall(find_wetterlage, web_pg)
    wetterlage = html.unescape(wetterlage_re[0]).replace("\\n", "")
    print(wetterlage)

    find_adria = r"Adria: </B><br /> \\n(.*)\\n</p>\\n<p><B>Ionisches Meer"
    adria_re = re.findall(find_adria, web_pg)
    adria = "Adria: " + html.unescape(adria_re[0]).strip()
    print(adria)

    find_ionisches_meer = r"Ionisches Meer: </B><br /> \\n(.*)\\n</p>\\n<p><B>\&Auml;g\&auml;is"
    ionisches_meer_re = re.findall(find_ionisches_meer, web_pg)
    ionisches_meer = "Ion.Meer: " + html.unescape(ionisches_meer_re[0].strip())
    print(ionisches_meer)

    find_aegaeis = r"\&Auml;g\&auml;is: </B><br /> \\n(.*)\\n</p>\\n<p><B>Taurus"
    aegaeis_re = re.findall(find_aegaeis, web_pg)
    aegaeis = "Ägäis: " + html.unescape(aegaeis_re[0].strip().replace("\\n", ""))
    print(aegaeis)

    windvorhersage = adria + "\n" + ionisches_meer + "\n" + aegaeis

    return issued, wetterlage_ausgabezeit, wetterlage, windvorhersage

if __name__ == '__main__':
    main()
