'use strict';

(function(){

  var module = angular.module('main_search', [], function($locationProvider) {
      $locationProvider.html5Mode(true);

      // make sure that angular doesn't intercept the page links
      angular.element("a").prop("target", "_self");
    });

    // Used to set the class of the filters based on the url parameters
    module.set_initial_filters_from_query = function (data, url_query, filter_param){
        for(var i=0;i<data.length;i++){
            if( url_query == data[i][filter_param] || url_query.indexOf(data[i][filter_param] ) != -1){
                data[i].active = 'active';
            }else{
                data[i].active = '';
            }
        }
        return data;
    }

  // Load categories and keywords
  module.load_filter = function (filter, $http, $rootScope, $location){
      if(filter == 'categories') {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
        $http.get(CATEGORIES_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('category__identifier__in')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['category__identifier__in'], 'identifier');
            }
            $rootScope.categories = data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
      }

      else if(filter == 'tabular_types') {

        $http.get(TABULAR_TYPES_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('tabular_type')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['tabular_type__name__in'], 'name');
            }
            $rootScope.tabular_types = data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
      }

      else if(filter == 'layer_types') {

        $http.get(LAYER_TYPES_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('layer_type')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['layer_type__name__in'], 'name');
            }
            $rootScope.layer_types = data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
      } 

      else if(filter == 'keywords') {

        $http.get(KEYWORDS_ENDPOINT, {params: params}).success(function(data){
            if($location.search().hasOwnProperty('keywords__slug__in')){
                data.objects = module.set_initial_filters_from_query(data.objects,
                    $location.search()['keywords__slug__in'], 'slug');
            }
            $rootScope.keywords = data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        });
      }

      else if(filter == 'creators') {
        var CREATORS_ENDPOINT = ($location.search().is_public == '1') ? 
          PUBLIC_CREATORS_ENDPOINT : PRIVATE_CREATORS_ENDPOINT;

        $http.get(CREATORS_ENDPOINT, {params: params}).success(function(data){
          if($location.search().hasOwnProperty('creator__username__in')){
              data.objects = module.set_initial_filters_from_query(data.objects,
                  $location.search()['creator_u_username__in'], 'username');
          }
          $rootScope.creators = data.objects;
          if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
              module.haystack_facets($http, $rootScope, $location);
          }
        });
      }

    }

  // Update facet counts for categories and keywords
  module.haystack_facets = function($http, $rootScope, $location) {
      var data = $rootScope.query_data;
      if ("categories" in $rootScope) {
          $rootScope.category_counts = data.meta.facets.category;
          for (var id in $rootScope.categories) {
              var category = $rootScope.categories[id];
              if (category.identifier in $rootScope.category_counts) {
                  category.count = $rootScope.category_counts[category.identifier]
              } else {
                  category.count = 0;
              }
          }
      }

      if ("tabular_types" in $rootScope) {
          $rootScope.tabular_type_counts = data.meta.facets.tabular_type;
          for (var id in $rootScope.tabular_types) {
              var tabular_type = $rootScope.tabular_types[id];
              if (tabular_type.identifier in $rootScope.tabular_types) {
                  tabular_type.count = $rootScope.tabular_types[tabular_type.identifier]
              } else {
                  tabular_type.count = 0;
              }
          }
      }

      if ("layer_types" in $rootScope) {
          $rootScope.later_type_counts = data.meta.facets.layer_type;
          for (var id in $rootScope.layer_types) {
              var layer_type = $rootScope.layer_types[id];
              if (layer_type.identifier in $rootScope.layer_types) {
                  layer_type.count = $rootScope.layer_types[layer_type.identifier]
              } else {
                  layer_type.count = 0;
              }
          }
      }

      if ("keywords" in $rootScope) {
          $rootScope.keyword_counts = data.meta.facets.keywords;
          for (var id in $rootScope.keywords) {
              var keyword = $rootScope.keywords[id];
              if (keyword.slug in $rootScope.keyword_counts) {
                  keyword.count = $rootScope.keyword_counts[keyword.slug]
              } else {
                  keyword.count = 0;
              }
          }
      }
  }

  /*
  * Load categories and keywords
  */
  module.run(function($http, $rootScope, $location){
    /*
    * Load categories and keywords if the filter is available in the page
    * and set active class if needed
    */
    ['categories','layer_types','tabular_types','keywords']
      .forEach(function(filter){
        if ($('#'+filter).length > 0)
          module.load_filter(filter, $http, $rootScope, $location);
      });

    // activate the proper public/private filter
    $("#sort a[data-value='"+$location.search().is_public+"'").addClass('selected');


    // Activate the type filters if in the url
    if($location.search().hasOwnProperty('type__in')){
      var types = $location.search()['type__in'];
      if(types instanceof Array){
        for(var i=0;i<types.length;i++){
          $('body').find("[data-filter='type__in'][data-value="+types[i]+"]").addClass('active');
        }
      }else{
        $('body').find("[data-filter='type__in'][data-value="+types+"]").addClass('active');
      }
    }

    // Activate the sort filter if in the url
    if($location.search().hasOwnProperty('order_by')){
      var sort = $location.search()['order_by'];
      $('body').find("[data-filter='order_by']").removeClass('selected');
      $('body').find("[data-filter='order_by'][data-value="+sort+"]").addClass('selected');
    }

  });

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller('MainController', function($injector, $scope, $location, $http, Configs){
    $scope.query = $location.search();
    $scope.query.limit = $scope.query.limit || CLIENT_RESULTS_LIMIT;
    $scope.query.offset = $scope.query.offset || 0;
    if($location.url() == "/layers/")
    $scope.query.is_public = $scope.query.is_public || "0";
    $scope.page = Math.round(($scope.query.offset / $scope.query.limit) + 1);

    // Load public layers
    function load_public_layers(data) {
      if(!module.layers) module.layers = [];

      var params = $.extend({}, data);
      params.is_public = "1";
      $http.get("/api/layers", {params: params}).success(function(data){
        var bycat = {};
        for(var i in data.objects) {
          var obj = data.objects[i];
          if(!bycat[obj.category_description]) {
            bycat[obj.category_description] = [];
          }
          
          if(module.layers[obj.id])
            obj.class = "active";
          else
            obj.class = "";

          bycat[obj.category_description].push(obj);
        }
        var objects = [];
        for(var i in bycat) {
          objects.push({category:i, layers:bycat[i]});
        }
        $scope.public_layers = objects;
      });
    }

    function clear_public_layers(data) {
      if(module.map) {
        for(var i in module.layers) {
          module.map.removeLayer(module.layers[i]);
        }
      }
      module.layers = [];
      $scope.public_layers = [];
    }

    function focus_map_on_objects(objects) {
      if(!module.map) return;

      var bounds = null;
      for(var i in objects) {

        var obj = objects[i];
        if(!bounds) {
          bounds = L.latLngBounds(
            L.latLng(obj.bbox_y0,obj.bbox_x0),
            L.latLng(obj.bbox_y1,obj.bbox_x1));
        } else {
          bounds.extend(L.latLng(obj.bbox_y0,obj.bbox_x0));
          bounds.extend(L.latLng(obj.bbox_y1,obj.bbox_x1));
        }
      }

      module.map.fitBounds(bounds);
    }

    function focus_map_on_extent(extent) {
      if(!module.map) return;
      var p=extent.split(",");
      var bounds = L.latLngBounds(
        L.latLng(p[1],p[0]),
        L.latLng(p[3],p[2]));
      module.map.fitBounds(bounds);
    }

    function clear_hulls(objects) {
      if(module.hulls_layer) 
        module.map.removeLayer(module.hulls_layer);
    }

    function draw_hulls(objects) {
      if(!module.map) return;

      if(module.hulls_layer) 
        module.map.removeLayer(module.hulls_layer);

      /* overlay the hulls of the layers */
      var geojson = [];

      for(var i in objects) {
        var hull = objects[i].concave_hull;
        if(hull) {
          geojson.push(JSON.parse(hull));
        }
      }

      module.hulls_layer = L.geoJson(geojson, {
        style: {
          "color": "#ff7800",
          "weight": 5,
          "opacity": 0.65
        }});
      module.hulls_layer.addTo(module.map);
    }

    //Get data from apis and make them available to the page
    function query_api(data){

      $scope.is_public = data.is_public == "1";

      var url = $scope.url || Configs.url;
      if(module.map) 
        load_public_layers(data);

      // select the proper type of public/private filter
      // XXX
      //$("#sort a[data-value='"+data.permission_class+"']").addClass("selected");

      var mapExtent = data.extent;
      $http.get(url, {params: data || {}}).success(function(data){

        if(module.map) {

          if(!$scope.is_public)
            draw_hulls(data.objects);
          else 
            clear_hulls();

            /*
            if(!mapExtent) {
              focus_map_on_objects(data.objects);
            } else {
              focus_map_on_extent(mapExtent);
            }
            */
        }

        $scope.results = data.objects;
        $scope.total_counts = data.meta.total_count;
        $scope.$root.query_data = data;
        if (HAYSTACK_SEARCH) {
          if ($location.search().hasOwnProperty('q')){
            $scope.text_query = $location.search()['q'].replace(/\+/g," ");
          }
        } else {
          if ($location.search().hasOwnProperty('title__contains')){
            $scope.text_query = $location.search()['title__contains'].replace(/\+/g," ");
          }
        }

        //Update facet/keyword/category counts from search results
        if (HAYSTACK_FACET_COUNTS){
            module.haystack_facets($http, $scope.$root, $location);
            $("#types").find("a").each(function(){
                if ($(this)[0].id in data.meta.facets.subtype) {
                    $(this).find("span").text(data.meta.facets.subtype[$(this)[0].id]);
                }
                else if ($(this)[0].id in data.meta.facets.type) {
                    $(this).find("span").text(data.meta.facets.type[$(this)[0].id]);
                    //$(this).show();
                } else {
                    $(this).find("span").text("0");
                    //$(this).hide();
                }
            });
        }
      });
    };
    query_api($scope.query);


    /*
    * Pagination 
    */
    // Control what happens when the total results change
    $scope.$watch('total_counts', function(){
      $scope.numpages = Math.round(
        ($scope.total_counts / $scope.query.limit) + 0.49
      );

      // In case the user is viewing a page > 1 and a 
      // subsequent query returns less pages, then 
      // reset the page to one and search again.
      if($scope.numpages < $scope.page){
        $scope.page = 1;
        $scope.query.offset = 0;
        query_api($scope.query);
      }

      // In case of no results, the number of pages is one.
      if($scope.numpages == 0){$scope.numpages = 1};
    });

    $scope.paginate_down = function(){
      if($scope.page > 1){
        $scope.page -= 1;
        $scope.query.offset =  $scope.query.limit * ($scope.page - 1);
        query_api($scope.query);
      }   
    }

    $scope.paginate_up = function(){
      if($scope.numpages > $scope.page){
        $scope.page += 1;
        $scope.query.offset = $scope.query.limit * ($scope.page - 1);
        query_api($scope.query);
      }
    }
    /*
    * End pagination
    */


    if (!Configs.hasOwnProperty("disableQuerySync")) {
        // Keep in sync the page location with the query object
        $scope.$watch('query', function(){
          $location.search($scope.query);
        }, true);
    }

    $scope.$watch('query.is_public',function(){
      module.load_filter('creators', $http, $scope, $location);
    }, true);

    $scope.toggle_nav = function($event){    
      var e = $event;
      var target = $event.target;
      e.preventDefault();
      if ($(target).parents("h4").siblings(".nav").is(":visible")) {
          $(target).parents("h4").siblings(".nav").slideUp();
          $(target).find("i").attr("class", "fa fa-chevron-right");
      } else {
          $(target).parents("h4").siblings(".nav").slideDown();
          $(target).find("i").attr("class", "fa fa-chevron-down");
      }      
    }

    $scope.toggle_map_overlay = function($event) {
      $event.preventDefault();
      var mmap = module.map;
      var target = $event.target;
      var obj_id = $(target).data('id');

      if($(target).hasClass("active")) {
        mmap.removeLayer(module.layers[obj_id]);
        module.layers.pop(obj_id);
        $(target).removeClass("active");

      } else {
        $http.get(Configs.url+obj_id).success(function(obj_data) {
          var wms_endpoint = null;
          for(var j in obj_data.links) {
            if(obj_data.links[j].link_type == "OGC:WMS") 
              wms_endpoint = obj_data.links[j].url;
          }
          if(wms_endpoint) {
            if(!module.layers) module.layers = {};
            module.layers[obj_id] = 
              L.tileLayer.wms(wms_endpoint, {
                  layers: obj_data.typename,
                  format: 'image/png',
                  transparent: true
              });
              module.layers[obj_id].addTo(mmap);
              $(target).addClass("active");
          }
        });   
      }
    }

    /*
    * Add the selection behavior to the element, it adds/removes the 'active' class
    * and pushes/removes the value of the element from the query object
    */
    $scope.multiple_choice_listener = function($event){    
      var element = $($event.target);
      var query_entry = [];
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');

      // If the query object has the record then grab it 
      if ($scope.query.hasOwnProperty(data_filter)){

        // When in the location are passed two filters of the same
        // type then they are put in an array otherwise is a single string
        if ($scope.query[data_filter] instanceof Array){
          query_entry = $scope.query[data_filter];
        }else{
          query_entry.push($scope.query[data_filter]);
        }     
      }

      // If the element is active active then deactivate it
      if(element.hasClass('active')){
        // clear the active class from it
        element.removeClass('active');

        // Remove the entry from the correct query in scope
        
        query_entry.splice(query_entry.indexOf(value), 1);
      }
      // if is not active then activate it
      else if(!element.hasClass('active')){
        // Add the entry in the correct query
        if (query_entry.indexOf(value) == -1){
          query_entry.push(value);  
        }         
        element.addClass('active');
      }

      //save back the new query entry to the scope query
      $scope.query[data_filter] = query_entry;

      //if the entry is empty then delete the property from the query
      if(query_entry.length == 0){
        delete($scope.query[data_filter]);
      }
      query_api($scope.query);
    }

    $scope.toggle_shared = function($event) {
      var element = $($event.target);
      var share = element.data('share');
      var resource_id = element.data('resource-id');
      var url = element.data('url');

      $.ajax({
          type: "POST",
          url: url,
          dataType: 'json',
          data: {
            resource_id: resource_id,
            shared: share
          },
          success: function(data){
             if(data.status != 'error'){
              var par = element.parent().parent();
                if(share) {
                  par.find(".shared").removeClass("ng-hide");
                  par.find(".notshared").addClass("ng-hide");
                } else {
                  par.find(".shared").addClass("ng-hide");
                  par.find(".notshared").removeClass("ng-hide");
                }
             }
          }
      });
    }

    $scope.single_choice_listener = function($event){
      var element = $($event.target);
      var query_entry = [];
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');
      var url = element.attr('data-url');

      // If the query object has the record then grab it 
      if ($scope.query.hasOwnProperty(data_filter)){
        query_entry = $scope.query[data_filter];
      }

      if(url) {
        $scope.url = url;
      }

      if(!element.hasClass('selected')){
        // Add the entry in the correct query

          query_entry = value;

          // clear the active class from it
          element.parents('ul').find('a').removeClass('selected');

          element.addClass('selected');

        if(value) {

          //save back the new query entry to the scope query
          $scope.query[data_filter] = query_entry;

        } else {

          delete $scope.query[data_filter];
        }      

        query_api($scope.query);        
      }     
    }

    /*
    * Text search management
    */
    var text_autocomplete = $('#text_search_input').yourlabsAutocomplete({
          url: AUTOCOMPLETE_URL,
          choiceSelector: 'span',
          hideAfter: 200,
          minimumCharacters: 1,
          appendAutocomplete: $('#text_search_input')
    });
    $('#text_search_input').bind('selectChoice', function(e, choice, text_autocomplete) {
          if(choice[0].children[0] == undefined) {
              $('#text_search_input').val(choice[0].innerHTML);
              $('#text_search_btn').click();
          }
    });

    $('#text_search_btn').click(function(){
        if (HAYSTACK_SEARCH)
            $scope.query['q'] = $('#text_search_input').val();
        else
            $scope.query['title__contains'] = $('#text_search_input').val();
        query_api($scope.query);
    });




    /*
    * Date management
    */

    $scope.date_query = {
      'date__gte': '',
      'date__lte': ''
    };

    $scope.$watch('date_query', function(){
      if($scope.date_query.date__gte != '' && $scope.date_query.date__lte != ''){
        $scope.query['date__range'] = $scope.date_query.date__gte + ',' + $scope.date_query.date__lte;
        delete $scope.query['date__gte'];
        delete $scope.query['date__lte'];
      }else if ($scope.date_query.date__gte != ''){
        $scope.query['date__gte'] = $scope.date_query.date__gte;
        delete $scope.query['date__range'];
        delete $scope.query['date__lte'];
      }else if ($scope.date_query.date__lte != ''){
        $scope.query['date__lte'] = $scope.date_query.date__lte;
        delete $scope.query['date__range'];
        delete $scope.query['date__gte'];
      }else{
        if (!$scope.query['date__range'] 
              && !$scope.query['date__gte']
              && !$scope.query['date__lte']) return;

        delete $scope.query['date__range'];
        delete $scope.query['date__gte'];
        delete $scope.query['date__lte'];
      }
      query_api($scope.query);
    }, true);

    /*
    * Spatial search
    */
    if ($('.leaflet_map').length > 0) {
      angular.extend($scope, {
        layers: {
          baselayers: {
            googleTerrain: {         
              name: 'Google Terrain',
              type: 'xyz',
              url: 'http://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            }
            /*
            stamen: {
              name: 'Toner Lite',
              type: 'xyz',
              url: 'http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
              layerOptions: {
                subdomains: ['a', 'b', 'c'],
                attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
                continuousWorld: true
              }
            }
            */
          }
        },
        map_center: {
          lat: -37, //5.6,
          lng: -66, //3.9,
          zoom: 3
        },
        defaults: {
          zoomControl: true
        }
      });

      var leafletData = $injector.get('leafletData'),
          map = leafletData.getMap();

      map.then(function(map) {
        module.map = map;
        if($scope.query.extent)
          focus_map_on_extent($scope.query.extent);
      });

      map.then(function(map){
        map.on('moveend', function(){
          $scope.query['extent'] = map.getBounds().toBBoxString();
          query_api($scope.query);
        });
      });
    }
  });
})();
