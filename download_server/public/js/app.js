angular.module('downloadServer', ['angular.filter'])
.controller('TaskController', ['$scope', '$http', '$interval', function($scope, $http, $interval) {
  $scope.getStatusClass = function(status) {
    switch (status) {
      case 'active':
        return '';
      case 'waiting':
        return 'warning';
      case 'paused':
        return 'warning';
      case 'error':
        return 'negitive';
      case 'complete':
        return 'positive';
      case 'removed':
        return 'disabled';
    }
  };

  var self = this;
  self.tasks = [];

  self.selectedTasksDo = function(action) {
    angular.forEach(self.tasks, function(task) {
      if (task.selected) {
        action(task);
      }
    });
  };

  $interval(function() {
    $http.get('/task').then(function onSuccess(response) {
      selectedTaskIds = {};
      self.selectedTasksDo(function(task) {
        selectedTaskIds[task.gid] = true;
      });
      angular.forEach(response.data.tasks, function(task) {
        if (selectedTaskIds[task.gid]) {
          task.selected = true;
        }
      })
      self.tasks = response.data.tasks;
    });
  }, 1000);

  self.add = function() {
    $http.post('/task', {'url': self.newUrl});
    self.newUrl = '';
  };

  self.stop = function() {
    self.selectedTasksDo(function(task) {
      $http.delete('/task', {params: {gid: task.gid}});
    })
  };

  self.pause = function() {
    self.selectedTasksDo(function(task) {
      $http.post('/task', {gid: task.gid, action: 'pause'});
    })
  };

  self.resume = function() {
    self.selectedTasksDo(function(task) {
      $http.post('/task', {gid: task.gid, action: 'resume'});
    })
  };
}]);
