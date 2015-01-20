'use strict';

(function(){

	var disabled = false;
	try {L} catch(err) {disabled = true;}

  String.prototype.hashCode = function() {
    var hash = 0, i, chr, len;
    if (this.length == 0) return hash;
    for (i = 0, len = this.length; i < len; i++) {
      chr   = this.charCodeAt(i);
      hash  = ((hash << 5) - hash) + chr;
      hash |= 0; // Convert to 32bit integer
    }
    return hash;
  };

	if(!disabled) {
	  L.Control.Layers = L.Control.Layers.extend({

	    _getCategoryElem: function(container, category) {
	      var elems = container.getElementsByClassName(
	        "leaflet-layers-category-"+category.hashCode());
	      var elem = null;
	      if (elems.length == 0) {
	        elem = this._createCategoryElem(category);
	        container.appendChild(elem);
	      } else {
	        elem = elems[0];
	      }

	      var innerElem = elem.getElementsByTagName('div')[0];
	      return innerElem;
	    },

	    _createCategoryElem: function(category) {
	        var elem = document.createElement('div');
	        elem.className = 'leaflet-layers-category-'+category.hashCode();
	        
	        var title = null;
	        if(category) {
	          var title = document.createElement('span');
	          title.setAttribute("style","display:block; border-bottom: black solid 1px");

	            var arrow = document.createElement('i');
	            arrow.className = 'fa fa-chevron-right';

	            var text = document.createElement('span');       
	            text.innerHTML = category;                  

	          title.appendChild(arrow);
	          title.appendChild(text);

	          $(title).click(function(ev) {
	            $(ev.target)
	              .parent().parent()
	              .find(".leaflet-layers-category-inner").toggle();

	            var i = $(ev.target).parent().find("i");
	            if(i.hasClass("fa-chevron-right")) {
	              i.removeClass("fa-chevron-right");
	              i.addClass("fa-chevron-down");
	            } else {
	              i.addClass("fa-chevron-right");
	              i.removeClass("fa-chevron-down");                    
	            }
	          });
	          elem.appendChild(title);              
	        }


	        var innerElem = document.createElement('div');
	        innerElem.className = 'leaflet-layers-category-inner';
	        if(title) {
	          $(innerElem).hide();
	        }
	        elem.appendChild(innerElem);
	        return elem;
	    },

	    addOverlay: function (layer, name, category) {
	      this._addLayer(layer, name, true, category);
	      this._update();
	      return this;
	    },

	    _addLayer: function (layer, name, overlay, category) {
	      var id = L.stamp(layer);

	      this._layers[id] = {
	        layer: layer,
	        name: name,
	        category: category,
	        overlay: overlay
	      };

	      if (this.options.autoZIndex && layer.setZIndex) {
	        this._lastZIndex++;
	        layer.setZIndex(this._lastZIndex);
	      }
	    },

	    _addItem: function (obj) {
	      var label = document.createElement('label'),
	          input,
	          checked = this._map.hasLayer(obj.layer);

	      if (obj.overlay) {
	        input = document.createElement('input');
	        input.type = 'checkbox';
	        input.className = 'leaflet-control-layers-selector';
	        input.defaultChecked = checked;
	      } else {
	        input = this._createRadioElement('leaflet-base-layers', checked);
	      }

	      input.layerId = L.stamp(obj.layer);

	      L.DomEvent.on(input, 'click', this._onInputClick, this);

	      var name = document.createElement('span');
	      name.innerHTML = ' ' + obj.name;

	      if(obj.category) {
	      	label.className = "layer-overlay-toggle layer-overlay-toggle-"+obj.name.hashCode();
	      }
	      label.appendChild(input);
	      label.appendChild(name);

	      var container = obj.overlay ? this._overlaysList : this._baseLayersList;

	      if (!obj.category) {
	        obj.category = "";
	      }

	      var elem = this._getCategoryElem(container, obj.category);
	      elem.appendChild(label);

	      return label;
	    }
	  });
	}

  var module = angular.module('map', [], function($locationProvider) {
    $locationProvider.html5Mode(true);
  });

  if(!disabled) {
	  module.controller('MapController', function($injector, $scope, $location, $http, Configs){

		  // Load public layers
		  $scope.load_public_layers = function(map) {
		    var params = {is_public: "1"};
		    $http.get("/api/layers", {params: params}).success(function(data){

		      var control = new L.Control.Layers();
		      for(var i in data.objects) {
		        var obj = data.objects[i];

		        var wms_endpoint = 
		          obj.links.filter(function(link){return link.link_type == "OGC:WMS"});

		        if(wms_endpoint.length > 0) {
		          var layer = 
		            L.tileLayer.wms(wms_endpoint[0].url, {
		                layers: obj.typename,
		                format: 'image/png',
		                transparent: true
		            });

		          var cat = "";
		          if(obj.category) cat = obj.category.description;

		          control.addOverlay(layer, obj.title, cat);
		        }
		      }
		      control.addTo(map);
		      $(".leaflet-control-layers-list").css('width','200px');
		      $scope.update_public_layers(map);
		    });
		  }

		  $scope.update_public_layers = function(map) {
				var params = {extent: map.getBounds().toBBoxString(), is_public: "1"};
		    $http.get("/api/layers", {params: params}).success(function(data){
		      $(".layer-overlay-toggle").hide();
		      for(var i in data.objects) {
		        var obj = data.objects[i];
		        $(".layer-overlay-toggle-"+obj.title.hashCode()).show();
		      }
		    });
		  }

		  /*
	    $scope.focus_map_on_objects = function(objects) {
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
	    */

	    $scope.clear_hulls = function(objects) {
	      if(module.hulls_layer) 
	        module.map.removeLayer(module.hulls_layer);
	    }

	    $scope.draw_hulls = function(objects) {
	    	var map = $scope.map;
	    	if(!map) return;

	      if($scope.hulls_layer) 
	        map.removeLayer($scope.hulls_layer);

	      /* overlay the hulls of the layers */
	      var geojson = [];

	      for(var i in objects) {
	        var hull = objects[i].concave_hull;
	        if(hull) {
	          geojson.push(JSON.parse(hull));
	        }
	      }

	      $scope.hulls_layer = L.geoJson(geojson, {
	        style: {
	          "color": "#ff7800",
	          "weight": 5,
	          "opacity": 0.65
	        }});
	      $scope.hulls_layer.addTo(map);
	    }


			if($injector.has('leafletData')) {
	    	var map = $injector.get('leafletData').getMap();
		  	map.then(function(map) {
		  		$scope.map = map;
	      	$scope.load_public_layers(map);

	      	map.on('moveend', function(){
	        	$scope.update_public_layers(map);
	      	});
	    	});
		  }
		});
	}

})();