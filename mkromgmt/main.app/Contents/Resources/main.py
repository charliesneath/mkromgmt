from google.appengine.dist import use_library
use_library('django', '1.2')

#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
from datetime import date
import time
from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
import logging
from google.appengine.ext.webapp import template
from google.appengine.api import namespace_manager
from google.appengine.api import users

class Initiate(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    query = Task.all()
    for task in query:
      task.delete()
    categories = {
      'chores': ['clean room', 'do stuff', 'laundry'],
      'exercise':['jog', 'gym', 'pushups', 'golf'], 
      'research':['read books', 'tech news', 'transit news', 'music news', 'design inspire'],
      'creative':['write', 'journal', 'photo mgmt', 'piano', 'coding'], 
      'social': ['chicks', 'meet people', 'booze', 'friends', 'make plans', 'attend event', 'hungover'],
      'travel': ['travel']}
    category_id = 1
    for category_name, tasks in categories.iteritems():
      task_id = 1
      for task_name in tasks:
        new_task = Task(
          category_name = category_name,
          category_id = '%s' % category_id,
          name = task_name,
          id = '%s' % task_id,
          status = 'active'
        )
        new_task.put()
        task_id = task_id + 1
      category_id = category_id + 1
    self.response.out.write('Tasks saved!')

class MainHandler(webapp.RequestHandler):
  '''send last 7 days of tasks to the client'''
  def get(self):
    user = users.get_current_user()
    self.record_user(user)
    namespace_manager.set_namespace(user.user_id())

    # put all categories into iterable lists
    data = {}
    categories = {}
    query = Task.all()
    num_tasks = {}
    # collect category category data by interating through tasks
    for task in query:
      num_tasks = self.count_tasks(num_tasks, task.category_name)
      if not task.category_name in categories:
        categories[task.category_name] = {
          'name': task.category_name,
          'id': task.category_id,
          'tasks': []}
      categories[task.category_name]['tasks'].append(task.name)
    data['categories'] = []
    for category in categories:
      data['categories'].append({
        'name': categories[category]['name'],
        'id': categories[category]['id'],
        'num_tasks': num_tasks[categories[category]['name']],
        'tasks': categories[category]['tasks']})
    data['categories'] = sorted(data['categories'], key=lambda x: x['id'])
    
    data['tasks'] = []
    query = Task.all()
    for task in query:
      data['tasks'].append({
        'id': '%s-%s' % (task.category_id, task.id), 
        'name': task.name})
    data['tasks'] = sorted(data['tasks'], key=lambda x: x['id'])

    data['dates'] = []
    today = date.today()
    timestamp = time.mktime((today.year, today.month, today.day, 0, 0, 0, 0, 0, 0))
    i = 0
    while i < 7:
      # get the current date by using the timestamp, where 86400 seconds = 1 day
      current_date = date.fromtimestamp(timestamp - (i * 86400))
      logging.debug(timestamp - (i * 86400))
      data['dates'].append(current_date.strftime('%a %b %d').upper())
      i = i + 1
    data['dates'].reverse()
    
    path = os.path.join(os.path.dirname(__file__), 'main.html')
    self.response.out.write(template.render(path, data))       
    
  def count_tasks(self, num_tasks, category_name):
    if not category_name in num_tasks:
      num_tasks[category_name] = 1
    else:
      num_tasks[category_name] = num_tasks[category_name] + 1
    return num_tasks
  
  def record_user(self, user):
    query = User().all();
    query.filter('user_id', user.user_id())
    new_user = query.get()
    if not new_user:
      new_user = User(
        user_id = user.user_id(),
        email = user.email()
      )
      new_user.put()

class SettingsHandler(webapp.RequestHandler):
  '''show users current tasks and the categories they are a part of'''
  def get(self):
    data = {}
    data['categories'] = {}
    query = Task.all()
    for task in query:
      if not task.task_category in data['categories']:
        data['categories'][task.task_category] = []
      data['categories'][task.task_category].append(task.task_name)
      logging.debug('%s - %s' % (task.task_category, task.task_name))
    path = os.path.join(os.path.dirname(__file__), 'settings.html')
    self.response.out.write(template.render(path, data))

class AjaxHandler(webapp.RequestHandler):
  '''manages the application settings'''
  def get(self):
    if self.request.get('action') == 'fetch_complete_tasks':
      self.fetch_complete_tasks()
    elif self.request.get('action') == 'new_task':
      self.new_task()
    elif self.request.get('action') == 'complete_task':
      self.complete_task()
    elif self.request.get('action') == 'incomplete_task':
      self.incomplete_task()
      
  def fetch_complete_tasks(self):
    logging.debug('fetching complete tasks')
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    data = {}
    data['tasks'] = []
    today = date.today()
    timestamp = (today.year, today.month, today.day, 0, 0, 0, 0, 0, 0)
    timestamp = int(time.mktime(timestamp))
    
    # dates are listed on site in reverse chronological order, so reverse it
    date_id = 0
    while date_id < 7:
      # get the current date by using the timestamp, where 86400 seconds = 1 day
      current_date = str(timestamp - (date_id * 86400))
      logging.debug('date - %s' % current_date)
      query = CompletedTask.all()
      query.filter('date', current_date)
      for task in query:
        logging.debug('found %s' % task.name)
        data['tasks'].append('%s-%s-%s' % (abs(date_id - 7), task.category_id, task.id))
        logging.debug('%s-%s-%s' % (date_id, task.category_id, task.id))
      date_id = date_id + 1
    self.response.out.write(simplejson.dumps(data))

  def new_task(self):
    logging.debug('received new task')
    query = Task.all()
    query.filter('category', self.request.get('category'))
    query.filter('name', self.request.get('name'))
    # check to make sure task doesn't exist
    for task in query:
      logging.debug('%s - %s' % (self.request.get('category'), self.request.get('name')))
      if task.task_category == self.request.get('category') and task.task_task == self.request.get('name'):
        logging.debug('duplicate task')
        self.response.out.write('duplicate')
    task = Task(
      task_category = self.request.get('category'),
      task_name = self.request.get('name').replace(' ', '_'))
    task.put()
    self.response.out.write(simplejson.dumps({
      'name': self.request.get('name'),
      'category': self.request.get('category')}))

  def delete_task(self):
    logging.debug('deleting task')
    logging.debug('%s - %s' % (self.request.get('category'), self.request.get('name')))
    query = Task.all()
    query.filter('category= ', self.request.get('category'))
    query.filter('name= ', self.request.get('name'))
    for task in query:
      task.delete()
      self.response.out.write('success')
      
  def complete_task(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    logging.debug('task complete')
    logging.debug('%s - %s' % (self.request.get('category_name'), self.request.get('name')))
    completed_task = CompletedTask(
      category_name = self.request.get('category_name'),
      category_id = self.request.get('category_id'),
      name = self.request.get('name'),
      id = self.request.get('id'),
      date = self.request.get('date')
    )
    completed_task.put()
    self.response.out.write('success')

  def incomplete_task(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    query = CompletedTask().all()
    query.filter('date', self.request.get('date'))
    query.filter('category_name', self.request.get('category_name'))
    query.filter('category_id', self.request.get('category_id'))
    query.filter('name', self.request.get('name'))
    for task in query:
      task.delete()
    self.response.out.write('success')

class Task(db.Model):
  '''gets shared album info from the db'''
  category_name = db.StringProperty()
  category_id = db.StringProperty()
  name = db.StringProperty()
  id = db.StringProperty()
  status = db.StringProperty()
    
class CompletedTask(db.Model):
  '''a daily task that has been completed'''
  category_name = db.StringProperty()
  category_id = db.StringProperty()
  name = db.StringProperty()
  id = db.StringProperty()
  date = db.StringProperty()

class User(db.Model):
  user_id = db.StringProperty()
  email = db.StringProperty()
  
def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/settings', SettingsHandler),
    ('/ajax', AjaxHandler),
    ('/set', Initiate)],
    debug=True)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
