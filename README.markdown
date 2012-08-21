#pyDimension - static blog generator

pyDimension is a static blog generator, written in Python, using Flask.

##Getting it going

###Dependencies

pyDimension uses the following Python libraries:

+ Flask (with Werkzeug and Jinja2)
+ markdown

If you are deploying with Apache, you'll need `mod_wsgi` installed and enabled too.

###Settings files

I've included some examples of what the settings files look like, you can rename them, removing the `.example` extension.

####pyDimension.example
This is the Apache VirtualHost config, there are 2 VirtualHosts, the first one runs the actual management frontend, the second one runs the search view (if you want to use it. Search is **very** simplistic).

I have things configured with my website on the naked and www domains and the pyDimension control panel on a different subdomain. If you want everything on the same domain, you would need to change the line:

    WSGIScriptAlias / /path/to/pyDimension.wsgi

to

    WSGIScriptAlias /control_panel /path/to/pyDimension.wsgi

it would then be accessible at `www.yourdomain.com/control_panel`.

The application is run as the `www-data` user (Apache's default user). You will need to make sure this user has permissions to read and write in your static website directory.

####pyDimension.wsgi.example & search.wsgi.example
These should be fairly straight-forward. I moved the configuration out into these files though, rather than in the application itself, it would allow multiple sites to be run from the same codebase.

You just need to provide the absolute path to the `settings.cfg` file (see next).

####settings.cfg.example
This is the meaty confusing one, these values are loaded into the Flask application in the `.wsgi` files.

+ `SECRET_KEY` - This should be something secure, [the flask docs][1] have a good explanation on how to generate a good one.
+ `AUTHOR` - Your name, as you want it to appear in Bylines
+ `USERNAME` - Login username for management pages
+ `PASSWORD_HASH` - sha512 has of your password (see below)
+ `SITE_ROOT_DIR` - this is where your static site is built, 
+ `SITE_ROOT_URL` - if your blog is actually hosted at www.example.com/blog, would be '/blog', leave it as '/' in most cases.
+ `SITE_TEMPLATE` - template directory to use when building site, see below for more about templates.
+ `SITE_URL` - poorly named I suppose (like `SITE_ROOT_URL`), actually the domain, mainly used when generating the RSS feed. Include the `http://`
+ `RSS_FEED_FILENAME` = built at www.example.com/blog_feed.xml, useful if transferring from a different blogging system.
+ `DRAFTS_ROOT_DIR` - mine is a Dropbox synched notes folder
+ `SEARCH_INDEX_DIR` - *very* basic search system puts lots of little files in here.
+ `HOME_ARTICLE_COUNT` - number of articles displayed on the home page.

##### Generating a password hash
You can generate a password hash at the Python commandline:

    $ python
    >>> import hashlib
    >>> hashlib.sha512('mypassword').hexdigest()
    'a336f671080fbf4f2a230f313560ddf0d0c12dfcf1741e49e8722a234673037dc493caa8d291d8025f71089d63cea809cc8ae53e5b17054806837dbe4099c4ca'
    >>>

Copy the full string, without the `'` and paste it into the `settings.cfg` file.

I'm fully aware that this is probably only a tiny little step better than not having a password at all, but it could be worse, I could be storing it as plaintext. This is also part of the reason that I host the actual static website from a different directory; there are no URLs on my server that expose the settings file.

####startDevServer.py
You can use this to test the system before you fully deploy it with Apache (or Gunicorn, or whatever, I've only tested Apache. If you do use something else, drop me a note, I'm interested!)

**DO NOT** run the site this way permanently. The built-in Flask dev server is *really* clever. Where there's an error it gives you a fully live python prompt, right there in the browser to help you debug the problem. This is fantastic for debugging whilst developing. It's a **REALLY BAD** thing to have on a live production server.

This is *REALLY* important. Don't do that.

###The static website

I have my site configured with everything in different directories. My `pyDimension` code is in my `projects` directory, the `.wsgi` stuff lives in my `public_html` folder and the website sits along-side it in a different folder.

There is a small caveat with getting things started: The raw markdown of all of the published articles is stored in files in an `articles/` subdirectory. You have to create that manually because I'm lazy and I didn't write a thing to do it (pyDimension took over from my [previous PHP system][2], so it never occurred to me.)

####Templates

Templates are a little tricky - the static site templates live in the `pyDimension/templates/{template_name}/` directory. These templates are used by the system to generate static html files that are then dropped into the static site directory. The templates will need to reference things like `.css` and `.xml` files, images, javascript whatever, *as if they are in the static site*, not in the templates directory.

It makes things a little fiddly, but it does work. Flask uses the [Jinja2][3] templating system, which is really good. I've left my templates in to give an idea of how they work. Basically anthing between `{{ }}` or `{% %}` is Jinja2 stuff.

##Getting in touch

I'm happy to help if you do want to use pyDimension. Get in touch through GitHub or [my website][4]

[1]: http://flask.pocoo.org/docs/quickstart/#sessions
[2]: https://github.com/MalphasWats/staticDimension
[3]: http://jinja.pocoo.org/
[4]: http://subdimension.co.uk/2011/04/05/about_me.html