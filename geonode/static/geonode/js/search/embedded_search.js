'use strict';

(function(){


  var module = angular.module('embedded_search', function($locationProvider) {
      $locationProvider.html5Mode(true);

      // // make sure that angular doesn't intercept the page links
      // angular.element("a").prop("target", "_self");
    });

  module.run(function($http, $rootScope, $location){

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
  module.controller('EmbeddedSearchController', function($injector, $scope, $location, $http, Configs){
    
    $scope.query = Configs.query;
    //$scope.query = $location.search();
    $scope.query.limit = $scope.query.limit || CLIENT_RESULTS_LIMIT;
    $scope.query.offset = $scope.query.offset || 0;
    $scope.page = Math.round(($scope.query.offset / $scope.query.limit) + 1);

    //Get data from apis and make them available to the page
    function query_api(data){

      var url = Configs.url;

      $http.get(url, {params: data || {}}).success(function(data){

        $scope.results = data.objects;
        $scope.total_counts = data.meta.total_count;

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


    // if (!Configs.hasOwnProperty("disableQuerySync")) {
    //     // Keep in sync the page location with the query object
    //     $scope.$watch('query', function(){
    //       $location.search($scope.query);
    //     }, true);
    // }

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
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');

      if(value.length == 0)
        delete $scope.query[data_filter];
      else
        $scope.query[data_filter] = value;

      if(!element.hasClass('selected')){          
        element.parents('ul').find('a').removeClass('selected');
        element.addClass('selected');
      }

      query_api($scope.query);
    }
  });
})();
