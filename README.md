# Browser-Extractive-Summarization
Select text on page using a chrome extension, then perform extractive summarization on it.

- This is experimental but it works. Currently using [HHousen's work for the summarization model](https://github.com/HHousen/TransformerSum/), but hadn't found the time to pick up [git subtrees](https://blog.developer.atlassian.com/the-power-of-git-subtree/) so I dumped it in the repo
- Using docker, run a flask server. This flask server will host a website that will display any summarizations, and it will also host the summarization model (extractive). Currently, this docker container is expected to be run locally (although there is no such requirements).
- Install the chrome extension using developer's mode. 
- Start the flask server using docker and open the webpage.
- Select text and choose the option to summarize it (shortcut is ctrl+period).
- The open webpage will show the summarized text as it communicates with the flask server using websockets.
- There is no underlying database, so refreshing / closing the webpage will erase results.

# Resources
1. [Flask + REST + websocket template](https://github.com/miguelgrinberg/Flask-SocketIO/tree/main/example)
2. [Summarization model](https://github.com/maszhongming/MatchSum)
3. [Asyncio example](https://gist.github.com/showa-yojyo/4ed200d4c41f496a45a7af2612912df3), but flask+socketio doesn't work with asyncio

# Other references
- https://github.com/huggingface/transformers/issues/1678
- https://skeptric.com/python-diffs/ (only useful for extractive summarization)
- https://betterprogramming.pub/background-processing-with-rabbitmq-python-and-flask-5ca62acf409c (Too much overhead when everything is supposed to be running on the same PC)

# Issues
- https://github.com/HHousen/TransformerSum/issues/15