'use strict';

(function(){

  var module = angular.module('profile_list', [], function($locationProvider) {
    $locationProvider.html5Mode(true);
  });


	module.controller('ProfileListController', function($injector, $scope, $location, $http, Configs){

    var users = [];
    $scope.disabled_users = [];
    for(var user in permissions.users) {
      if(user != owner) {
        users.push(user);
      }
      if(permissions.users[user].length == 0)
        $scope.disabled_users.push(user);
    }

    $scope.disabled_user = function(username) {
      return $scope.disabled_users.indexOf(username) >= 0;
    }    

  	$.get("/api/profiles",{"username__in": users.join(',')})
  	  .success(function(data) {
  			$scope.profile_list = data.objects;
  		});

    $scope.remove_permission = function($event,username) {
      $event.stopPropagation();
      $event.preventDefault();
      delete permissions.users[username];
      $.post("/security/permissions/"+layer_id, JSON.stringify(permissions));
    }

    $scope.toggle_permission = function($event,username) {
      $event.stopPropagation();
      $event.preventDefault();
      if($scope.disabled_user(username)) {
        permissions.users[username] = ["view_resourcebase","change_resourcebase"];
        $scope.disabled_users.pop(username);
      } else {
        delete permissions.users[username];
        $scope.disabled_users.push(username);
      }
      $.post("/security/permissions/"+layer_id, JSON.stringify(permissions));
    };

	});

})();