import pony

from pony.utils import decorator_with_params, tostring
from pony.templating import htmltag, Html, printhtml
from pony.web import http, url, css_link, script_link, component

@decorator_with_params
def webpage(old_func, *args, **keyargs):
    if pony.MODE.startswith('GAE-'):
        raise EnvironmentError('@webpage decorator does not work inside Google AppEngine.\n'
                               'Use @http decorator and html() function instead.')
    return http(*args, **keyargs)(printhtml(old_func))

def blueprint_link(column_count=24, column_width=30, gutter_width=10, ns=''):
    if column_count == 24 and column_width == 30 and gutter_width == 10 and ns == '':    
        return Html(
            '<link rel="stylesheet" href="/pony/static/blueprint/screen.css" type="text/css" media="screen, projection">\n'
            '<link rel="stylesheet" href="/pony/static/blueprint/print.css" type="text/css" media="print">\n'
            '<!--[if IE]><link rel="stylesheet" href="/pony/static/blueprint/ie.css.css" type="text/css" media="screen, projection"><![endif]-->\n'
            )
    if not ns: params = Html('%s/%s/%s') % (column_count, column_width, gutter_width)
    else: params = Html('%s/%s/%s/%s') % (column_count, column_width, gutter_width, ns)
    return Html(
        '<link rel="stylesheet" href="/pony/static/blueprint/%s/screen.css" type="text/css" media="screen, projection">\n'
        '<link rel="stylesheet" href="/pony/static/blueprint/%s/print.css" type="text/css" media="print">\n'
        '<!--[if IE]><link rel="stylesheet" href="/pony/static/blueprint/%s/ie.css.css" type="text/css" media="screen, projection"><![endif]-->\n'
        ) % (params, params, params)

def jquery_link(version='1.2.3'):
    return Html('<script src="/pony/static/jquery/jquery-%s.js"></script>' % version)

link_funcs = dict(
    blueprint=blueprint_link,
    jquery=jquery_link
    )

link_template = Html(u'<a href="%s">%s</a>')

def link(*args, **keyargs):
    if not args: raise TypeError('link() function requires at least one positional argument')
    first = args[0]
    if hasattr(first, 'http'):
        func = first
        args = args[1:]
        if func.__doc__ is None: description = func.__name__
        else: description = Html(func.__doc__.split('\n', 1)[0])
    elif len(args) > 1 and hasattr(args[1], 'http'):
        description = tostring(first)
        func = args[1]
        args = args[2:]
    elif isinstance(first, basestring):
        func = link_funcs.get(first)
        if func is not None: return func(*args[1:], **keyargs)
        if first.endswith('.css'):
            if keyargs: raise TypeError('Unexpected key arguments')
            return css_link(args)
        if first.endswith('.js'):
            if len(args) > 1: raise TypeError('Unexpected positional arguments')
            if keyargs: raise TypeError('Unexpected key arguments')
            return script_link(first)
        raise TypeError('Invalid arguments of link() function')
        
    href = url(func, *args, **keyargs)
    return link_template % (href, description)

img_template = Html(u'<img src="%s" title="%s" alt="%s">')

def img(*args, **keyargs):
    description = None
    if isinstance(args[0], basestring):
        description = args[0]
        func = args[1]
        args = args[2:]
    else:
        func = args[0]
        args = args[1:]
        if func.__doc__ is None: description = func.__name__
        else: description = Html(func.__doc__.split('\n', 1)[0])
    href = url(func, *args, **keyargs)
    return img_template % (href, description, description)

@component(css='/pony/static/css/rounded-corners.css')
def rounded(markup, **attrs):
    tagname = attrs.pop('tagname', 'div')
    radius = attrs.pop('radius', 10)
    result = [ htmltag(tagname, {'class': 'rounded'}, **attrs), markup,
               Html('<div class="top-left radius-%s"></div>\n'
                    '<div class="top-right radius-%s"></div>\n'
                    '<div class="bottom-left radius-%s"></div>\n'
                    '<div class="bottom-right radius-%s"></div>\n'
                    '</%s>') % (radius, radius, radius, radius, tagname)]
    return Html('\n').join(result)

class tabs(object):
    @component(css=[ ('/pony/static/jquery/jquery.tabs.css', 'print, projection, screen'),
                     ('/pony/static/jquery/jquery.tabs-ie.css', 'projection, screen', 'if lte IE 7') ],
                 js=[ '/pony/static/jquery/jquery-1.2.3.js',
                      '/pony/static/jquery/jquery.tabs.js',
                      '/pony/static/js/tabs.js' ])
    def __init__(self, **attrs):
        self.attrs = attrs
        self._tabs = []
    def tab(self, name, markup, **attrs):
        if id not in attrs: attrs['id'] = http.response.next_id()
        self._tabs.append((name, markup, attrs))
    def __unicode__(self):
        next_id = http.response.next_id
        result = [htmltag('div', {'class':'pony-tabs clearfix'}, **self.attrs), Html('\n<ul>\n') ]
        for name, markup, attrs in self._tabs:
            result.append(Html('<li><a href="#%s"><span>%s</span></a>\n') % (attrs['id'], name))
        result.append(Html('</ul>\n'))
        for name, markup, attrs in self._tabs:
            result.extend([htmltag('div', {'class': 'pony-tab clearfix'}, **attrs), markup, Html('</div>\n')])
        result.append(Html('</div>'))
        return Html('').join(result)