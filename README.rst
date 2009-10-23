============
django-layar
============

Django generic view for making `Layar <http://layar.com>`_ endpoints.

Provides abstract class that responds to Layar API requests in the appropriate format.  By implementing two small functions it is possible to add a layer to the Layar augmented reality application for Android and iPhone.

django-layar is a project of Sunlight Labs (c) 2009.
Written by James Turk <jturk@sunlightfoundation.com>

Source: http://github.com/sunlightlabs/django-layar/

Requirements
============

python >= 2.4

django >= 1.0

Installation
============

To install run

    ``python setup.py install``

which will install the application into the site-packages directory.

Usage
=====

Layar Developer Key
--------------------

If you haven't already, it is necessary to `sign up with Layar <http://dev.layar.com>`_ to obtain an API key.

Set ``LAYAR_DEVELOPER_KEY='<YOUR_KEY>'`` in settings.py


Creating a ``LayarView`` subclass
---------------------------------

django-layar provides a class-based generic view at :class:`layar.LayarView`.  In order to provide your own layers
it is necessary to inherit from this view and implement two simple functions (per layer).

The required functions are :func:`get_LAYERNAME_queryset` and :func:`poi_from_LAYERNAME_item`.

It is possible to serve as many layers as you desire from a single Layar endpoint, just make sure that the name of your functions matches the name you provide when registering your layers with Layar.com

:func:`get_LAYERNAME_queryset` is passed a number of arguments (see :class:`layar.LayarView` for detail)
and should return a queryset of the objects for :class:`LayarView` to paginate and return.

:func:`poi_from_LAYERNAME_item` is called on each item being returned, and should convert items
into :class:`POI` objects.

It is usually best to then create an instance of your derived class in your application's ``views.py``

Example::

    # views.py

    from django.contrib.gis.geos import Point
    from myapp.models import BusStop
    from layar import LayarView, POI

    class BusStopLayar(LayarView):

        # make sure to accept **kwargs
        def get_busstop_queryset(self, latitude, longitude, radius, **kwargs):
            return BusStop.objects.filter(location__distance_lt=(Point(longitude, latitude), radius))

        def poi_from_recoverygov_item(self, item):
            return POI(id=item.id, lat=item.location.y, lon=item.location.x, title=item.name,
                        line2=item.route_name, line3='Distance: %distance%')

    # create an instance of BusStopLayar
    busstop_layar = BusStopLayar()

In urls.py it is then necessary to map a URL directly to ``busstop_layar``::

    # urls.py

    from django.conf.urls.defaults import *

    urlpatterns = patterns('',
        url(r'^layar_endpoint/$', 'myapp.views.busstop_layar'),
    )
