pyqdb
=====

A quotes database in python.

Setup
-----

# Check out source code

    git clone git://github.com/Ramblurr/pyqdb.git
# Install dependencies

    pip install -U -r requirements.txt
# Setup Database

    cd src;
    ./sql_setup.py

# Start server
    python pyqdb.py

API
---

pyqdb tries very hard to be RESTful. As such there is no special API uri. Instead you can make requests to the same URIs used for browsing the page in HTML, but pass the `Accept: application/json` (or one of the custom mimetypes below) and pyqdb will return nifty json for the resource. 

pyqdb treats HTML and JSON as two representations of the same state. It tries to respect the `Accept:` and `Content-Type` headers at all times. In the spirit of HATEOAS there is no documentation describing every possible API call. Toss a `GET` at the root URI (with the Accept JSON header) to see the available resources. 

pyqdb makes use of the [`Link`][linkhdr] to hint the consumer where to go next. A good example of this is pagination when getting the list of latest quotes the link header contains the URI to the next and previous pages.

    $ curl -I -H "Accept: application/json" vtbash.org/quotes
    HTTP/1.1 200 OK
    Content-Type: application/json
    Link: </quotes?start=15>; rel="next"
    Content-Length: 4911

Similarly, when fetching a blank skeleton for quote submission the Link header contains the hint on where to submit the quote.

    curl -i -H "Accept: application/json" vtbash.org/quotes/new
    HTTP/1.1 200 OK
    Date: Tue, 09 Aug 2011 16:42:32 GMT
    Content-Type: application/json
    Link: </quotes>; rel="submit"
    Content-Length: 98

    {"body": "Quote here", "link": {"href": "/quotes", "method": "post", "rel": "submit"}, "tags": []}

You can see above that pyqdb also embeds link information into the JSON as well using the `link` JSON object. Possible values for this key are:
* `href` (required)- the URI to the resource being linked
* `rel` (required) - the relation of the link to the containing resource
* `method` (optional) - the suggested method to use, if no method is specified GET is the assumed default
* `title` (optional) - a human readable description of the link

pyqdb uses relative URIs wherever possible.


[linkhdr]: http://www.w3.org/Protocols/9707-link-header.html

