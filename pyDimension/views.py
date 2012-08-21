import os
import time
import re
import codecs

from flask import (Flask, request, session, g, redirect, url_for,
                   abort, render_template, flash)

from markdown import markdown

from pyDimension.access_control import login_required
from pyDimension.system import *
from pyDimension.search import add_to_index, remove_from_index

from pyDimension import app


@app.route('/')
@login_required
def control_panel():
    return render_template('control_panel.html', 
                           articles=get_articles(),
                           drafts=get_drafts())

                           
@app.route('/save', methods=['POST'])
@login_required
def save():
    if request.form.get('preview') == 'Preview':
        return render_template('preview.html', 
                           preview_html=markdown(request.form['text'], output_format="html5"),
                           rawText=request.form['text'],
                           filename=request.form['filename'])
    if request.form['text'] == '':
        flash("articles must have body text", category='error')
        return redirect(url_for('control_panel'))                      
    title = get_title_elements(request.form['text'])[0]
    safe_title = re.sub('[^a-zA-Z0-9\s]', '', title).replace(' ', '_')
    date = time.strftime('%Y-%m-%d_%H-%M', time.gmtime())
    
    if request.form.get('draft') == 'on':
        if request.form['filename'] != '':
            filename = request.form['filename']
        else:
            filename = "%s.txt" % safe_title
        
        try:
            articleFile = codecs.open("%s/%s" % (app.config['DRAFTS_ROOT_DIR'], filename), encoding='utf-8', mode='w')
        except:
            flash("There was a problem accessing the file %s/%s" % (app.config['DRAFTS_ROOT_DIR'], filename), category='error')
            return redirect(url_for('control_panel'))
        
        articleFile.write(request.form['text'])
        articleFile.flush()
        articleFile.close()
        flash("The draft was saved", category='info')
    else:
        if request.form['wasDraft'] == 'yes':
            filename = "%s_%s" % (date, get_safe_filename(request.form['filename']))
        elif request.form['filename'] != '':
            filename = get_safe_filename(request.form['filename'])
            kill_item_in_cache(filename)
        else:
            filename = "%s_%s.txt" % (date, safe_title)
        
        try:
            articleFile = codecs.open("%s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename), encoding='utf-8', mode='w')
        except:
            flash("There was a problem accessing the file %s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename), category='error')
            return redirect(url_for('control_panel'))
            
        articleFile.write(request.form['text'])
        articleFile.flush()
        articleFile.close()
        flash("The article was saved", category='info')
        
        try:
            url = create_article_from_template(request.form['text'], title, filename[:-4])
        except:
            pass
        else:
            rebuild_archive_indexes()
            rebuild_homepage()

            add_to_index(request.form['text'], url)
    
    return redirect(url_for('control_panel'))
    
    
@app.route('/edit/<filename>')
@login_required
def edit(filename):
    filename = get_safe_filename(filename)
    articleElements = get_article_elements(filename)
    
    return render_template('editor.html',
                           filename=filename, 
                           rawText=articleElements['rawText'],
                           isDraft=False)
                           
                         
@app.route('/draft/<filename>')
@login_required
def draft(filename):
    draft = get_draft(filename)
    
    return render_template('editor.html',
                           filename=filename, 
                           rawText=draft,
                           isDraft=True)
                           
                           
@app.route('/delete/article/<filename>')
@login_required
def delete_article(filename):
    filename = get_safe_filename(filename)
    elem = get_article_elements(filename)
    try:
        os.remove("%s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename))
    except:
        flash("unable to delete file: %s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename), category='error')
        return redirect(url_for('control_panel'))
        
    articlePath = filename[:10].replace('-','/')
    try:
        os.remove("%s/%s/%s.html" % (app.config['SITE_ROOT_DIR'], articlePath, filename[17:-4]))
    except:
        flash("unable to delete file: %s/%s/%s.html" % (app.config['SITE_ROOT_DIR'], articlePath, filename[17:-4]), category='error')
        return redirect(url_for('control_panel'))
        
    rebuild_archive_indexes()
    rebuild_homepage()
    
    kill_item_in_cache(filename)
    remove_from_index(elem['rawText'], elem['url'])
    flash("deleted %s" % filename, category='info')
    return redirect(url_for('control_panel'))
    
    
@app.route('/delete/draft/<filename>')
@login_required
def delete_draft(filename):
    try:
        os.remove("%s/%s" % (app.config['DRAFTS_ROOT_DIR'], filename))
    except:
        flash("unable to delete file: %s/%s" % (app.config['DRAFTS_ROOT_DIR'], filename), category='error')
        return redirect(url_for('control_panel'))
    
    flash("deleted %s" % filename, category='info')
    return redirect(url_for('control_panel'))
    
    
    
#debugging use mostly
@app.route('/preview/<filename>')
@login_required
def preview_article(filename):
    filename = get_safe_filename(filename)
    articleFile = codecs.open("%s/articles/%s" % (app.config['SITE_ROOT_DIR'], filename), encoding='utf-8', mode='r')
    articleText = articleFile.read()
    articleFile.close()
    
    html = markdown(articleText,
                           output_format="html5")
    
    return render_template("%s/preview.html" % (app.config['SITE_TEMPLATE']), 
                           content=html,
                           author=app.config['AUTHOR'],
                           pubDate="Just now")
