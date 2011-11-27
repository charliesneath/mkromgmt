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

class MainHandler(webapp.RequestHandler):
  '''send last 7 days of tasks to the client'''
  def get(self):
    self.check_for_new_user()
      
  def check_for_new_user(self):
    user = users.get_current_user()
    query = User.all()
    query.filter('user_id', user.user_id())
    for user in query:
      logging.debug('user already exists')
      logging.debug('this user: %s' % user.email)
      self.fetch_tasks()
      break
    else:
      logging.debug('user not found')
      self.record_user()
      self.initiate_user_tasks()
    
  def initiate_user_tasks(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    query = Task.all()
    for task in query:
      task.delete()
    categories = {
      'chores': ['clean room', 'laundry'],
      'exercise':['jog', 'gym'], 
      'research':['read books', 'read news', 'music news', 'tech news'],
      'creative':['writing', 'drawing', 'coding'], 
      'social': ['meet new people', 'booze', 'see friends', 'make plans', 'attend event', 'hungover'],
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
          status = 'active')
        new_task.put()
        task_id = task_id + 1
      category_id = category_id + 1
    self.redirect('/')

  def fetch_tasks(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    # put all categories into iterable lists
    data = {}
    categories = {}
    query = Task.all()
    query.filter ('status', 'active')
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
    query.filter ('status', 'active')
    for task in query:
      data['tasks'].append({
        'id': '%s-%s' % (task.category_id, task.id),
        'category_id': '%s' % task.category_id,
        'name': task.name})
    data['tasks'] = sorted(data['tasks'], key=lambda x: x['id'])

    data['dates'] = []
    today = date.today()
    timestamp = time.mktime((today.year, today.month, today.day, 0, 0, 0, 0, 0, 0))
    i = 0
    while i < 7:
      # get the current date by using the timestamp, where 86400 seconds = 1 day
      current_date = date.fromtimestamp(timestamp - (i * 86400))
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
  
  def record_user(self):
    user = users.get_current_user()
    query = User().all();
    query.filter('user_id', user.user_id())
    namespace_manager.set_namespace('')
    new_user = query.get()
    if not new_user:
      new_user = User(
        user_id = user.user_id(),
        email = user.email()
      )
      new_user.put()
      
class Settings(webapp.RequestHandler):
  '''show users current tasks and the categories they are a part of'''
  def get(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    data = {}
    categories = {}
    query = Task.all()
    for task in query:
      if not task.category_name in categories:
        categories[task.category_name] = {}
        categories[task.category_name]['tasks'] = []
        categories[task.category_name]['id'] = task.category_id
        categories[task.category_name]['name'] = task.category_name
      categories[task.category_name]['tasks'].append({
        'name': task.name,
        'id': task.id})
    
    data['categories'] = []
    for category_name, properties in categories.iteritems():
      properties['tasks'] = sorted(properties['tasks'], key=lambda x: x['id'])
      data['categories'].append({
        'name': category_name,
        'id': properties['id'],
        'tasks': properties['tasks']})
    
    data['categories'] = sorted(data['categories'], key=lambda x: x['id'])
    path = os.path.join(os.path.dirname(__file__), 'settings.html')
    self.response.out.write(template.render(path, data))

class AjaxHandler(webapp.RequestHandler):
  '''manages the application settings'''
  def get(self):
    if self.request.get('action') == 'fetch_complete_tasks':
      self.fetch_complete_tasks()
    elif self.request.get('action') == 'new_task':
      self.new_task()
    elif self.request.get('action') == 'delete_task':
      self.delete_task()
    elif self.request.get('action') == 'complete_task':
      self.complete_task()
    elif self.request.get('action') == 'incomplete_task':
      self.incomplete_task()
    elif self.request.get('action') == 'save_journal_entry':
      self.save_journal_entry()
    elif self.request.get('action') == 'fetch_journal_entry':
      self.fetch_journal_entry()
      
  def fetch_complete_tasks(self):
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
      query = CompletedTask.all()
      query.filter('date', current_date)
      for task in query:
        data['tasks'].append('%s-%s-%s' % (abs(date_id - 7), task.category_id, task.id))
      date_id = date_id + 1
    self.response.out.write(simplejson.dumps(data))

  def new_task(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    logging.debug('new task %s' % self.request.get('name'))
    task = Task(
      category_name = self.request.get('category_name'),
      category_id = '%s' % self.request.get('category_id'),
      name = self.request.get('name'),
      id = '%s' % self.request.get('id'),
      status = 'active')
    task.put()
    data = {
      'category_name': self.request.get('category_name'),
      'category_id': '%s' % self.request.get('category_id'),
      'name': self.request.get('name'),
      'id': '%s' % self.request.get('id')}
    # send task back to the client
    self.response.out.write(simplejson.dumps(data))

  def delete_task(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    query = Task.all()
    query.filter('id', self.request.get('id'))
    query.filter('category_id', self.request.get('category_id'))
    for task in query:
      task.delete()
    # renumber the tasks
    query = Task.all()
    query.filter('category_id', self.request.get('category_id'))
    i = 1
    for task in query:
      task.id = '%s' % i
      task.put()
      i = i + 1
    self.response.out.write('success')
      
  def complete_task(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
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
    
  def save_journal_entry(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    query = JournalEntry.all()
    query.filter('timestamp', self.request.get('timestamp'))
    for entry in query:
      entry.text = self.request.get('text')
      entry.put()
      self.response.out.write('success')
      break
    else:
      entry = JournalEntry(
        text = self.request.get('text'),
        timestamp = self.request.get('timestamp')
      )
      entry.put()

  def fetch_journal_entry(self):
    user = users.get_current_user()
    namespace_manager.set_namespace(user.user_id())
    query = JournalEntry.all()
    query.filter('timestamp', self.request.get('timestamp'))
    for entry in query:
      self.response.out.write(entry.text)

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
  
class JournalEntry(db.Model):
  text = db.TextProperty()
  timestamp = db.StringProperty()
  
class Logout(webapp.RequestHandler):
  def get(self):
    logout_url = users.create_logout_url('/')
    self.redirect(logout_url)
  
def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/settings', Settings),
    ('/ajax', AjaxHandler),
    ('/logout', Logout)],
    debug=True)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
