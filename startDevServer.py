from pyDimension import app

import os

print "Starting server in %s" % os.getcwd()

app.config.from_pyfile('/path/to/settings.cfg')
app.run(host='0.0.0.0', debug=True)