from django import template
import time
import os
#import lis
register = template.Library()

@register.simple_tag
def version_date():
    return "%s %s" % (1.0, time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime('../.git'))))
