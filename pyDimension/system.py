import os
import datetime
import time
import re
import codecs

from flask import (Flask, request, session, redirect, url_for,
                   abort, render_template, flash)
from werkzeug import secure_filename

from glob import glob
from markdown import markdown

from access_control import login_required

from pyDimension import app

# global cache item that breaks the request context. There is a potential for
# race conditions if multiple users are editing the same things at the same
# time, but pyDimension is not currently designed for concurrent multiple users.
# The session object in flask uses a cookie to store the session data between
# requests, which would be inappropriate for this kind of use. I'm not sure what
# the g object actually achieves, as it only persists within a single request!
articleCache = {}

def get_articles():
    files = glob("%s/articles/*.txt" % (app.config['SITE_ROOT_DIR']))
    files.sort()
    files.reverse()
    articles = []
    
    for f in files:
        filename = os.path.split(f)[1]
        elem = get_article_elements(filename)
        elem['editurl'] = url_for('edit', filename=filename)
        articles.append(elem)
        
    return articles
    

def get_drafts():
    files = glob("%s/*.txt" % (app.config['DRAFTS_ROOT_DIR']))
    files.sort()
    drafts = []
    
    for f in files:
        filename = os.path.split(f)[1]
        text = get_draft(filename).splitlines()
        line = 1
        snippet = ''
        while snippet == '' and line < len(text):
            snippet = text[line][0:30]
            line += 1
        drafts.append({'editurl': url_for('draft', filename=filename), 'title': filename[:-4], 'filename': filename, 'snippet':snippet})
        
    return drafts

    
def get_article_elements(filename):
    articlePath = "%s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename)
    if articlePath in articleCache:
        return articleCache[articlePath]
        
    try:
        articleFile = codecs.open(articlePath, encoding='utf-8', mode='r')
    except:
        flash("There was a problem accessing file: %s" % articlePath, category='error')
        return []
        
    rawText = articleFile.read()
    articleFile.close()
    
    html = ''
    title = ''
    link = ''
    if rawText != '':
        html = markdown(rawText, output_format='html5')
        titleElem = get_title_elements(rawText)
        title = titleElem[0]
        link = titleElem[1]
        
    url = build_article_url(articlePath)
    pubDate = get_pub_date(filename)
    
    article = {'filename': filename, 
               'rawText': rawText,
               'title': title, 
               'link': link, 
               'url': url, 
               'pubDate': pubDate, 
               'html': html,}
            
    articleCache[articlePath] = article
                                    
    return article


def get_draft(filename):
    draftPath = "%s/%s" % (app.config['DRAFTS_ROOT_DIR'], filename)
    
    try:
        draftFile = codecs.open(draftPath, encoding='utf-8', mode='r')
    except:
        flash("There was a problem accessing file: %s" % draftPath, category='error')
        return ''
    
    rawText = draftFile.read()
    draftFile.close()
    
    return rawText

    
def get_title_elements(rawText):
    title = rawText.splitlines()[0][1:]
    if title[0] == '[':
        title = title.split('](')
        return (title[0][1:], title[1][:-1])
    else:
        return (title, '')

def get_body_text(rawText):
    lines = rawText.splitlines()
    return "\n".join(lines[1:])
    
    
def kill_item_in_cache(filename):
    try:
        del articleCache["%s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename)]
    except:
        pass
    
            
def build_article_url(articlePath):
    filename = os.path.split(articlePath)[1]
    return "%s%s%s/%s.html" % (app.config['SITE_URL'], app.config['SITE_ROOT_URL'], filename[:10].replace('-','/'),  filename[17:-4])


def get_pub_date(filename):
    #legacy pages don't have pubDate in their filename.
    try:
        ts = time.strptime(filename[:16], "%Y-%m-%d_%H-%M")
        pubDate = (time.strftime("%a, %d %b %Y %H:%M:%S GMT", ts), time.strftime("%A, %d %B %Y @ %H:%M", ts))
    except:
        pubDate = ('', '')
        
    return pubDate

    
def get_safe_filename(filename):
    return secure_filename(filename)
    
    
def create_article_from_template(rawText, title, filename):
    articlePath = filename[:10].replace('-','/')
    if not os.path.exists("%s/%s" % (app.config['SITE_ROOT_DIR'], articlePath)):
        try:
            os.makedirs("%s/%s" % (app.config['SITE_ROOT_DIR'], articlePath))
        except:
            flash("There was a problem creating directories: %s/%s" % (app.config['SITE_ROOT_DIR'], articlePath), category='error')
            raise

    try:
        articleFile = codecs.open("%s/%s/%s.html" % (app.config['SITE_ROOT_DIR'], articlePath, filename[17:]),
                                  encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing file: %s/%s/%s.html" % (app.config['SITE_ROOT_DIR'], articlePath, filename[17:]), category='error')
        raise

    content = {'title': title,
               'html': markdown(rawText, output_format='html5'),
               'url': "%s%s%s/%s.html" % (app.config['SITE_URL'], app.config['SITE_ROOT_URL'], articlePath, filename[17:])}
    
    articleFile.write(render_template("%s/article.html" % (app.config['SITE_TEMPLATE']), 
                                   content=content,
                                   author=app.config['AUTHOR'],
                                   pubDate=get_pub_date(filename)[1]))
    articleFile.close()
    return content['url']


def rebuild_articles():
    articles = glob("%s/articles/*.txt" % app.config['SITE_ROOT_DIR'])
    for article in articles:
        elem = get_article_elements(os.path.split(article)[1])
        try: 
            create_article_from_template(elem['rawText'], elem['title'], elem['filename'][:-4])
        except:
            pass


def rebuild_archive_indexes():
    archiveYearDirs = glob("%s/[0-9][0-9][0-9][0-9]" % app.config['SITE_ROOT_DIR'])
    archiveYearDirs.sort()
    
    try:
        archiveFile = codecs.open("%s/archive.html" % (app.config['SITE_ROOT_DIR']),
                                  encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing the file %s/archive.html" % app.config['SITE_ROOT_DIR'], category='error')
        return
    
    archiveYears = []                          
    for y in archiveYearDirs:
        year = os.path.split(y)[1]
        archiveYears.append((year, year))
        
        for (path, dirs, files) in os.walk("%s/%s" % (app.config['SITE_ROOT_DIR'], year)):
            try:
                archiveIndex = codecs.open("%s/index.html" % path,
                                           encoding='utf-8', mode='w')
            except:
                flash("There was a problem accessing the file %s/index.html" % path, category='error')
                return
            
            dirs.sort()
            sPath = path[len(app.config['SITE_ROOT_DIR'])+1:]
            if not dirs:
                if 'index.html' in files:
                    files.remove('index.html')
                items = map(map_article_full_title, files) #can't think of a way to get back to filename
            else:
                if os.path.split(sPath)[0] != '':
                    days = dirs
                    month = [os.path.split(sPath)[1] for x in range(len(days))]
                    yr = [year for x in range(len(days))]
                    items = map(map_day_name, days, month, yr)
                else:
                    items = map(map_month_name, dirs)
                
            archiveIndex.write(render_template("%s/archive.html" % app.config['SITE_TEMPLATE'],
                                      site_root_url=app.config['SITE_ROOT_URL'], 
                                      items=items,
                                      breadcrumb=sPath.replace('\\', '/')+'/'))
            archiveIndex.close()
                              
    archiveFile.write(render_template("%s/archive.html" % app.config['SITE_TEMPLATE'],
                                      site_root_url=app.config['SITE_ROOT_URL'], 
                                      items=archiveYears,
                                      breadcrumb=""))
    archiveFile.close()
    
def map_month_name(monthNumber):
    months = ("January", "February", "March", 
              "April", "May", "June", "July", 
              "August", "September", "October", 
              "November", "December")
    return (monthNumber, months[int(monthNumber)-1])
    
def map_day_name(dayNumber, month, year):
    d = datetime.date(int(year), int(month), int(dayNumber))
    return (dayNumber, "%s, %s" % (d.strftime('%A'), dayNumber))
    
def map_article_full_title(f):
    return (f, f)
    
    
def rebuild_homepage():
    n = app.config['HOME_ARTICLE_COUNT']
    
    articles = glob("%s/articles/*.txt" % app.config['SITE_ROOT_DIR'])
    articles.sort()
    articles.reverse()

    articleElements = []

    for article in articles[:n]:
        elem = get_article_elements(os.path.split(article)[1])
        lines = elem['html'].splitlines()
        elem['body_html'] = "\n".join(lines[1:])
        articleElements.append(elem)
    
    try:
        homepageFile = codecs.open("%s/index.html" % app.config['SITE_ROOT_DIR'], encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing the file %s/index.html" % app.config['SITE_ROOT_DIR'], category='error')
    else:
        homepageFile.write(render_template("%s/home.html" % app.config['SITE_TEMPLATE'], 
                                           articles=articleElements,
                                           author=app.config['AUTHOR']))
        homepageFile.close()

    lastBuildDate = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime()) #Thu, 26 Apr 2012 10:09:47 GMT
    try:
        rssFile = codecs.open("%s/%s" % (app.config['SITE_ROOT_DIR'], app.config['RSS_FEED_FILENAME']), encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing the file %s/rss.xml" % app.config['SITE_TEMPLATE'], category='error')
    else:
        rssFile.write(render_template("%s/rss.xml" % app.config['SITE_TEMPLATE'],
                                      items=articleElements, date=lastBuildDate))
        rssFile.close()
    


#system function provided for convienience
@app.route('/rebuild')
def rebuild_site():
    rebuild_articles()
    rebuild_archive_indexes()
    rebuild_homepage()
    flash('Site rebuilt', category='info')
    return redirect(url_for('control_panel'))
    
    
    
def log(s):
    logFile = codecs.open("log.log", encoding='utf-8', mode='a')
    logFile.write(s+"\n")
    logFile.flush()
    logFile.close()