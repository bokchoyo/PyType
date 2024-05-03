from flask import render_template
from database import Database
from flask import redirect
from flask import request
from flask import Flask
import logging
import base64
import json

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
db = Database('data.json')

@app.route('/')
def app_index():
  return render_template('index.html')

@app.route('/lessons')
def app_lessons():
  return render_template('lessons.html')

@app.route('/lessons/<name>')
def app_lessons_name(name):
  return render_template('lesson.html', name=name)

@app.route('/scores')
def app_scores():
  return render_template('scores.html')

@app.route('/practice')
def app_practice():
  code = request.args.get('code')
  if code:
    return render_template('practice.html', code=str(code))
  return redirect('/', code=302)

@app.route('/api/get/lessons')
def api_get_lessons():
  categories = db.get('problems')
  items = []
  for item in categories:
    items.append({
      'name': item,
      'lessons': [i['title'] for i in categories[item]],
      'num_lessons': len(categories[item])
    })
  return {'success': True, 'lessons': items}

@app.route('/api/get/lesson/<name>')
def api_get_lesson(name):
  item = None
  data = db.get('problems')
  for i in data:
    for sub in data[i]:
      if name == sub['title']:
        item = sub
  item['success'] = True
  return item

@app.route('/api/execute', methods=['POST'])
def api_execute():
  data = json.loads(request.data.decode('utf-8'))
  code = data['code']
  items = db.get('problems')
  item = None
  for i in items:
    for sub in items[i]:
      if data['name'] == sub['title']:
        item = sub

  try:
    exec(code)
  except Exception as e:
    return {'success': False, 'error': str(e)}

  try:
    passed = 0
    for case in item['test_cases']:
      args = [i.strip() for i in case['case'].split('(')[1][:-1].split(',')]      
      if args == ['']:
        result = eval(case['case'].split('(')[0])()
      else:
        result = eval(case['case'].split('(')[0])(*map(eval, args))
      if str(result) == case['solution']: passed += 1
    return {'success': True, 
            'passed': True if passed == len(item['test_cases']) else False, 
            'correct': passed,
            'total': len(item['test_cases'])
           }
  except Exception as e:
    return {'success': False, 'error': str(e)}

@app.route('/api/save/score', methods=['POST'])
def api_save_score():
  data = json.loads(request.data.decode('utf-8'))
  scores = db.get('scores')
  items = db.get('problems')
  exercises = []
  for cat in items:
    exercises.extend([i['title'] for i in items[cat]])
  # if data['referrer'].split('/')[-1] in exercises:
  scores['sum'] += data['wpm']
  scores['tests'] += 1

  ldb = False
  if len(scores['leaderboard']) < 10:
    scores['leaderboard'].append(data)
    ldb = True
  else:
    for score in scores['leaderboard']:
      if data['wpm'] > score['wpm']:
        scores['leaderboard'].append(data)
        ldb = True
        break
    scores['leaderboard'] = sorted(scores['leaderboard'], key=lambda x: x['wpm'], reverse=True)
  scores['leaderboard'] = scores['leaderboard'][:10]
  db.set('scores', scores)
  return {'success': True, 'leaderboard': ldb}
  # return {'success': False} # bro tried to cheat 

@app.get('/api/scores')
def api_leaderboard():
  scores = db.get('scores')
  return {
    'average_wpm': scores['sum']/scores['tests'],
    'tests_taken': scores['tests'],
    'leaderboard': sorted(scores['leaderboard'], key=lambda x: x['wpm'], reverse=True)
  }

app.run(host='0.0.0.0', port=8080)