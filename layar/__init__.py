from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.hashcompat import sha_constructor as sha1
from django.utils import simplejson as json

class LayarException(Exception):
    ''' Layar exception - takes a code (20-29) to return to Layar'''
    def __init__(self, code, message):
        self.code = code
        self.message = message

class POI(object):
    '''
        Object representing Layar Points of Interest

        Layar has some specific requirements (eg. that lat/longs are converted
        to fixed point) that are taken care of when converting these objects
        to JSON.  String lengths mentioned below are recommended, strings will
        not be truncated on the server.

        Required fields:
            ``id``
                unique id for this POI
            ``lat``
                latitude of POI
            ``lon``
                longitude of POI
            ``title``
                Name of POI, displayed in large font. (<= 60 chars)

        Optional fields:
            ``imageURL``
                image to display when POI is selected
            ``line2, line3, line4``
                additional lines of detail (use special token %distance% to
                display distance to POI) (<= 35 chars)
            ``type``
                numerical type (0-3), can set meaning when publishing Layar
            ``attribution``
                bottom line of display, shown in small font (<= 45 chars)
            ``actions``
                dictionary mapping names of actions to URIs
        '''

    def __init__(self, id, lat, lon, title, actions=None, image_url=None,
                 line2=None, line3=None, line4=None, type=0, attribution=None):
        self.id = str(id)
        self.lat = lat
        self.lon = lon
        self.title = title          # recommended max len 60
        self.imageURL = image_url
        self.line2 = line2          # recommended max len 35
        self.line3 = line3
        self.line4 = line4
        self.type = type            # must be 0..3
        self.attribution = attribution  # recommended max len 45
        self.actions = actions

    def to_dict(self):
        d = dict(self.__dict__)

        # do lat/long conversion
        if isinstance(self.lat, float):
            d['lat'] = int(self.lat*1000000)
        if isinstance(self.lon, float):
            d['lon'] = int(self.lon*1000000)

        # convert actions dictionary into expected format
        if self.actions:
            d['actions'] = [{'label':k, 'uri':v} for k,v in self.actions.iteritems()]
        else:
            d['actions'] = []

        return d

class LayarView(object):
    '''
        Class-based generic view for creating a Layar endpoint.

        To add a layar it is necessary to write two functions:
            ``get_LAYERNAME_queryset``
                This function is passed latitude, longitude, radius,
                radio_option, search_query, and slider_value parameters.

                radio_option, search_query, and slider_value may be None
                depending on how you've configured your widgets on layar.com

                **Note:** It is strongly recommended that you make this function
                accept **kwargs for maximum compatibility

            ``poi_from_LAYERNAME_item(item)``
                convert an item of whatever type is returned by 
                :func:`get_LAYARNAME_queryset` into a ``POI`` object

        This separation allows LayarView to handle pagination correctly.

        Your derived class can also set a number of options.  The defaults
        should be suitable for most purposes as Layar doesn't display more
        than 50 points.

        ``results_per_page``
            controls the number of results returned at once (default: 15)
        ``max_results``
            controls the maximum number of results across all pages (default: 50)
        ``verify_hash``
            set to False to disable hash verification (useful for testing)
    '''

    results_per_page = 15
    max_results = 50
    verify_hash = True

    def __init__(self):
        self.developer_key = settings.LAYAR_DEVELOPER_KEY

    def __call__(self, request):
        try:
            user_id = request.GET['userId']
            developer_id = request.GET['developerId']
            developer_hash = request.GET['developerHash']
            timestamp = request.GET['timestamp']
            layer_name = request.GET['layerName']
            lat = float(request.GET['lat'])
            lon = float(request.GET['lon'])
            accuracy = int(request.GET['accuracy'])
            radius = int(request.GET['radius'])
            radio_option = request.GET.get('RADIOLIST')
            search = request.GET.get('SEARCHBOX')
            slider = request.GET.get('CUSTOM_SLIDER')
            page = int(request.GET.get('pageKey', 0))
        except KeyError, e:
            return HttpResponseBadRequest('missing required parameter: %s' % e)

        layar_response = dict(hotspots=[], layer=layer_name, errorCode=0,
                          errorString='ok', nextPageKey=None, morePages=False)

        try:

            # verify hash
            if self.verify_hash:
                key = self.developer_key + timestamp
                if sha1(key).hexdigest() != developer_hash:
                    raise LayarException(20, 'Bad developerHash')

            # get ``max_results`` items from queryset
            try:
                qs_func = getattr(self, 'get_%s_queryset' % layer_name)
            except AttributeError:
                raise LayarException(21, 'no such layer: %s' % layer_name)

            qs = qs_func(latitude=lat, longitude=lon, radius=radius,
                         radio_option=radio_option, search_query=search,
                         slider_value=slider)[:self.max_results]

            # do pagination if results_per_page is set
            if self.results_per_page:
                start_index = self.results_per_page * page
                end_index = start_index + self.results_per_page

                # if there are more pages, indicate that in response
                if end_index < qs.count()-1:
                    layar_response['morePages'] = True
                    layar_response['nextPageKey'] = str(page+1)

                qs = qs[start_index:end_index]

            # convert queryset into POIs
            try:
                poi_func = getattr(self, 'poi_from_%s_item' % layer_name)
            except AttributeError:
                raise LayarException(21, 'no such layer: %s' % layer_name)

            pois = [poi_func(item) for item in qs]
            layar_response['hotspots'] = [poi.to_dict() for poi in pois]

        except LayarException, e:
            layar_response['errorCode'] = e.code
            layar_response['errorString'] = e.message

        content = json.dumps(layar_response)
        return HttpResponse(content,
                content_type='application/javascript; charset=utf-8')
