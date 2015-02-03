'use strict';

(function(){

  var module = angular.module('profile_list', [], function($locationProvider) {
    $locationProvider.html5Mode(true);
  });


	module.controller('ProfileListController', function($injector, $scope, $location, $http, Configs){

  	$.get("/api/profiles")
  	  .success(function(data) {
  			$scope.profile_list = data.objects;

        $scope.profiles = {};
        $scope.usernames = {user: [], organization: [], application: []};

        for(i in data.objects) {
          var obj = data.objects[i];
          if(obj.profile == 'application' && applications.indexOf(obj.id)<0) continue;
          
          if($scope.usernames[obj.profile]) $scope.usernames[obj.profile].push(obj.username);
          var enabled = permissions.users[obj.username] != null && permissions.users[obj.username].length > 0;
          $scope.profiles[obj.username] = {profile: obj.profile, avatar: obj.avatar_100, enabled: enabled}
        }
        $scope.permissions = permissions;
        $scope.applications = applications;
        $scope.update_empty();
        $scope.$apply();
  		});


    $scope.update_empty = function() {
      $scope.empty = {user: true, organization: true};
      for(i in $scope.profiles) {
        var obj = $scope.profiles[i];
        $scope.empty[obj.profile] &= !obj.enabled; 
      }
    }

    $scope.remove_permission = function($event,username) {
      $event.stopPropagation();
      $event.preventDefault();
      delete permissions.users[username];
      $scope.update_empty();
      $.post("/security/permissions/"+layer_id, JSON.stringify(permissions));
    }

    $scope.toggle_permission = function($event,username) {
      $event.stopPropagation();
      $event.preventDefault();
      if(!$scope.profiles[username].enabled) {
        permissions.users[username] = ["view_resourcebase","change_resourcebase"];
      } else {
        delete permissions.users[username];
      }
      $.post("/security/permissions/"+layer_id, JSON.stringify(permissions))
        .success(function(ev) {
          $scope.profiles[username].enabled = !$scope.profiles[username].enabled;
          $scope.update_empty();
          $scope.$apply();
        });
    };
    

    $scope.add_permission = function($event,username) {
      $event.stopPropagation();
      $event.preventDefault();
      permissions.users[username] = ["view_resourcebase","change_resourcebase"];
      $.post("/security/permissions/"+layer_id, JSON.stringify(permissions))
        .success(function(ev) {
          $scope.profiles[username].enabled = true;
          $scope.$apply();
          $("#_permissions").modal("hide");
        });
    };

    $scope.remove_permission = function($event,username) {
      $event.stopPropagation();
      $event.preventDefault();
      delete permissions.users[username];
      $.post("/security/permissions/"+layer_id, JSON.stringify(permissions))
        .success(function(ev) {
          $scope.profiles[username].enabled = false;
          $scope.update_empty();
          $scope.$apply();
        });
    };



    $scope.add_permission_dialog = function($event,profile) {
      $scope.modal_profile = profile;
      //$scope.$apply();
      $("#_permissions").modal();
    }

	});

})();