from flask import Flask

app = Flask(__name__)

srch = Flask(__name__)

import pyDimension.system
import pyDimension.access_control
import pyDimension.views
import pyDimension.search