import gdown
import re
import difflib
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context, jsonify, Response
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from os.path import exists
from transformersum.extractive import ExtractiveSummarizer
from typing import List, Any, Callable, Tuple, Union
import html

# https://skeptric.com/python-diffs/
Token = str
TokenList = List[Token]

whitespace = re.compile('\s+')
end_sentence = re.compile('[.!?]\s+')

def tokenize(s:str) -> TokenList:
    '''Split a string into tokens'''
    return whitespace.split(s)

def untokenize(ts:TokenList) -> str:
    '''Join a list of tokens into a string'''
    return ' '.join(ts)

def sentencize(s:str) -> TokenList:
    '''Split a string into a list of sentences'''
    return end_sentence.split(s)

def unsentencise(ts:TokenList) -> str:
    '''Join a list of sentences into a string'''
    return '. '.join(ts)

def html_unsentencise(ts:TokenList) -> str:
    '''Joing a list of sentences into HTML for display'''
    return ''.join(f'<p>{t}</p>' for t in ts)
    
def mark_span(text:TokenList) -> TokenList:
    return [mark_text(token) for token in text]

def mark_text(text:str) -> str:
    return f'<span style="color: red;">{text}</span>'

def markup_diff(a:TokenList, b:TokenList,
                mark: Callable[[TokenList], TokenList] = mark_span,
                default_mark: Callable[[TokenList], TokenList] = lambda x: x,
                isjunk: Union[None, Callable[[Token], bool]]=None) -> Tuple[TokenList, TokenList]:
    """Returns a and b with any differences processed by mark

    Junk is ignored by the differ
    """
    seqmatcher = difflib.SequenceMatcher(isjunk=isjunk, a=a, b=b, autojunk=False)
    out_a, out_b = [], []
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        markup = default_mark if tag == 'equal' else mark_span
        out_a += markup(a[a0:a1])
        out_b += markup(b[b0:b1])
    assert len(out_a) == len(a)
    assert len(out_b) == len(b)
    return out_a, out_b

def align_seqs(a: TokenList, b: TokenList, fill:Token='') -> Tuple[TokenList, TokenList]:
    out_a, out_b = [], []
    seqmatcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        delta = (a1 - a0) - (b1 - b0)
        out_a += a[a0:a1] + [fill] * max(-delta, 0)
        out_b += b[b0:b1] + [fill] * max(delta, 0)
    assert len(out_a) == len(out_b)
    return out_a, out_b

def html_diffs(a, b):
    a = html.escape(a)
    b = html.escape(b)

    out_a, out_b = [], []
    for sent_a, sent_b in zip(*align_seqs(sentencize(a), sentencize(b))):
        mark_a, mark_b = markup_diff(tokenize(sent_a), tokenize(sent_b))
        out_a.append(untokenize(mark_a))
        out_b.append(untokenize(mark_b))

    return (out_a, out_b)

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
model = None
model_lock = Lock()

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count})

# https://towardsdatascience.com/creating-restful-apis-using-flask-and-python-655bad51b24
# https://stackoverflow.com/questions/20001229/how-to-get-posted-json-in-flask
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

def summarize_text(text):
  summary = None
  with model_lock:
      summary = model.predict(text)
  return summary

def addStrikethrough(old, new):
  # Split on non-word
  a = re.split(r'(\W+)', old)
  b = re.split(r'(\W+)', new)
  i = 0
  j = 0
  open_del = False
  original_with_strikethrough = ""
  while i < len(a):
    a_word = a[i].lower()
    b_word = b[j].lower() if j < len(b) else ""
    while j < len(b) and not b[j].isalnum():
      j += 1
      if j == len(b):
          b_word = ""
      else:
          b_word = b[j].lower()
    # Skip if not alnum
    if not a_word.isalnum():
      original_with_strikethrough += a[i]
    elif (a_word == b_word):
      if (j < len(b)):
        j += 1
        if j == len(b):
          b_word = ""
      # Close previous strikethrough
      if open_del:
        original_with_strikethrough += "</del>"
        open_del = False
      original_with_strikethrough += a[i]
    elif not open_del:
      # Open new strikethrough
      open_del = True
      original_with_strikethrough += '<del style="color: red;">'
      original_with_strikethrough += a[i]
    else:
      original_with_strikethrough += a[i]
    i += 1
  return original_with_strikethrough

@app.route('/summarize', methods=['POST'])
def summarize():
    if request.json:
        content = request.json["text"]
        summary = summarize_text(content)
        html_content = addStrikethrough(content, summary)
        # html_content, html_summary = html_diffs(content, summary)
        socketio.emit('entry', {'text': html_content, 'summary': summary})
        return Response('{"result": "'+summary+'"}', status=200, mimetype='application/json')
    return Response('{"error": "Not a valid JSON request"}', status=400, mimetype='application/json')


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1

    content = message['data']
    summary = summarize_text(content)
    html_content = addStrikethrough(content, summary)
    # html_content, html_summary = html_diffs(content, summary)
    socketio.emit('entry', {'text': html_content, 'summary': summary})
    # emit('my_response', {'data': summary, 'count': session['receive_count']})


@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])


@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         to=message['room'])


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    # Download model weights into persistent volume
    CACHE_PREFIX = "/app/cache"
    model_filename = "model.cpkt"
    if not exists(f"{CACHE_PREFIX}/{model_filename}"):
        print("Downloading model weights... (gdown logger doesn't work well with Docker, so you may not see the progress bar)")
        url = "https://drive.google.com/uc?id=1VNoFhqfwlvgwKuJwjlHnlGcGg38cGM--"
        output = f"{CACHE_PREFIX}/{model_filename}"
        gdown.download(url, output, quiet=False)
    else:
        print("Using cached model")
    # Startup model consumer & prepare shutdown hook
    # https://www.pythonfixing.com/2021/11/fixed-asyncioqueue-as-producer-consumer.html
    print("Loading model...")
    model = ExtractiveSummarizer.load_from_checkpoint(f"{CACHE_PREFIX}/{model_filename}")
    print("Starting app at http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
